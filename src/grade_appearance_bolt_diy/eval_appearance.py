import os
import zipfile
from tqdm import tqdm
import time

import re
from typing import List, Tuple
import json

import subprocess
from pathlib import Path
import sys

from start_service import start_services
from get_screenshots import capture_scroll_screenshots
from vlm_eval_qwenvl import get_score_result


def load_json(in_file):
    with open(in_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_json(data, out_file):
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_jsonl(in_file):
    datas = []
    with open(in_file, "r", encoding="utf-8") as f:
        for line in tqdm(f):
            datas.append(json.loads(line))
    return datas


def save_jsonl(datas, out_file, mode="w"):
    with open(out_file, mode, encoding="utf-8") as f:
        for data in tqdm(datas):
            f.write(json.dumps(data, ensure_ascii=False) + "\n")


def extract_bolt_actions(text: str) -> Tuple[List[str], str]:
    # Extract all shell actions
    shell_actions = re.findall(r'<boltAction type="shell">(.*?)</boltAction>', text, re.DOTALL)

    # Extract all start actions
    start_actions = re.findall(r'<boltAction type="start">(.*?)</boltAction>', text, re.DOTALL)

    # Get the last start action, if any
    last_start_action = start_actions[-1] if start_actions else ""

    return shell_actions, last_start_action


def unzip_files(zip_file_paths, output_root):
    """
    Given a list of .zip files and a desired output root directory,
    unzip each file into a subdirectory named after the .zip file.
    
    :param zip_file_paths: List of paths to .zip files (e.g. ["path/to/file1.zip", "path/to/file2.zip"]).
    :param output_root: Output root directory where extracted folders will be created.
    """
    # Ensure the output_root exists
    if not os.path.exists(output_root):
        os.makedirs(output_root)
    
    for zip_path in tqdm(zip_file_paths):

        try:
            # Get the base name of the zip file (e.g. "my_archive" from "my_archive.zip")
            base_name = os.path.splitext(os.path.basename(zip_path))[0]
            
            # Construct the output folder path
            output_dir = os.path.join(output_root, base_name)
            
            # Create the output directory if it doesn't exist
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Extract all contents of the zip file into the output directory
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
        except:
            print(f"Error extracting {zip_path} to {output_dir}")


def get_shell_start(zip_file_paths, output_root):
    commands = {}
    for zip_file in tqdm(zip_file_paths):
        json_file = zip_file.replace(".zip", ".json")
        data = load_json(json_file)
        shell_actions, last_start_action = extract_bolt_actions(data["messages"][-1]["content"])
        commands[os.path.basename(zip_file).replace(".zip", "")] = {"shell_actions": shell_actions, "last_start_action": last_start_action}

    save_json(commands, os.path.join(output_root, "commands.json"))
    return commands


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("in_dir", type=str)
    parser.add_argument("-t", type=str, default="data/test.jsonl")
    args = parser.parse_args()
    in_dir = args.in_dir
    test_file = args.t
    test_datas = load_jsonl(test_file)
    zip_files = [os.path.join(in_dir, file) for file in os.listdir(in_dir) if file.endswith(".zip") and file.startswith("00")]
    
    output_root = os.path.join(in_dir, "extracted")
    if not os.path.exists(output_root):
        os.makedirs(output_root)

    filtered_zip_files = []
    for zip_file in zip_files:
        app_name = os.path.basename(zip_file).replace(".zip", "")
        shot_file = os.path.join(output_root, app_name, "shots", "shot_1.png")
        if not os.path.isfile(shot_file):
            filtered_zip_files.append(zip_file)
    zip_files = filtered_zip_files

    unzip_files(zip_files, output_root)

    subprocess.run("pm2 delete all", shell=True)

    batch_size = 1
    for i in tqdm(range(0, len(zip_files), batch_size)):
        batch_zip_files = zip_files[i:i + batch_size]
        commands = get_shell_start(batch_zip_files, output_root)
        ports = start_services(output_root, commands)
        print(ports)
        
        time.sleep(1)

        for app in ports.keys():
            port = ports[app]
            shot_path = os.path.join(output_root, app, "shots")
            capture_scroll_screenshots(
                url = f"http://localhost:{port}/",
                out_dir = shot_path,
                max_shots = 1,
                pause = 0.4,
                viewport_height = 768
            )
            
        subprocess.run("pm2 delete all", shell=True)
        
    for idx, data in tqdm(enumerate(test_datas)):
        instruction = data["instruction"]
        app = f"{idx + 1:06d}"
        shot_path = os.path.join(output_root, app, "shots")
        result_path = os.path.join(output_root, app, "shots", "result.json")
        if os.path.isfile(result_path):
            print(f"result.json already exists in {app}, skipping...")
            continue
        if not os.path.exists(shot_path):
            print(f"shots not found in {app}, skipping...")
            continue
        image_paths = [os.path.join(shot_path, f) for f in os.listdir(shot_path) if f.endswith(".png")]
        if len(image_paths) == 0:
            print(f"shots not found in {app}, skipping...")
            continue
        output = get_score_result(image_paths, instruction)
        save_json({"model_output": output}, result_path)
        print(f"Processed {app} with {len(image_paths)} images.")


if __name__ == "__main__":
    main()