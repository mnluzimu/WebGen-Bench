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
from vlm_eval import get_score_result


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
            

def get_app_path(base_dir, app):
    app_path = os.path.join(base_dir, app)
    if len(os.listdir(app_path)) == 1 and os.path.isdir(os.path.join(app_path, os.listdir(app_path)[0])):
        app_path = os.path.join(app_path, os.listdir(app_path)[0])
    return app_path


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


def get_shell_start(app_path, output_root):
    commands = {}
    for app_path in tqdm(app_path):
        app_name = os.path.basename(app_path)
        commands[app_name] = {"shell_actions": [], "last_start_action": ""}

    save_json(commands, os.path.join(output_root, "commands.json"))
    return commands


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--in_dir", type=str)
    args = parser.parse_args()
    in_dir = args.in_dir
    test_file = "data\\app-bench.jsonl"
    test_datas = load_jsonl(test_file)
    app_paths = [os.path.join(in_dir, f"task_{i}") for i in range(101)]
    
    output_root = in_dir
    if not os.path.exists(output_root):
        os.makedirs(output_root)

    filtered_app_paths = []
    for app_path in app_paths:
        if len(os.listdir(app_path)) == 1:
            base_name = os.listdir(app_path)[0]
            shot_file = os.path.join(app_path, base_name, "shots", "shot_1.png")
        else:
            shot_file = os.path.join(app_path, "shots", "shot_1.png")
        if not os.path.isfile(shot_file):
            filtered_app_paths.append(app_path)
    app_paths = filtered_app_paths

    subprocess.run("pm2 delete all", shell=True)

    batch_size = 5
    for i in tqdm(range(0, len(app_paths), batch_size)):
        batch_app_paths = app_paths[i:i + batch_size]
        commands = get_shell_start(batch_app_paths, output_root)
        ports = start_services(output_root, commands)
        print(ports)
        
        time.sleep(1)

        for app in ports.keys():
            port = ports[app]
            app_path = os.path.join(output_root, app)
            if len(os.listdir(app_path)) == 1:
                base_name = os.listdir(app_path)[0]
                shot_path = os.path.join(output_root, app, base_name, "shots")
            else:
                shot_path = os.path.join(output_root, app, "shots")
            capture_scroll_screenshots(
                url = f"http://localhost:{port}/",
                out_dir = shot_path,
                max_shots = 3,
                pause = 0.4,
                viewport_height = 768
            )
            
        subprocess.run("pm2 delete all", shell=True)
        
    for idx, data in tqdm(enumerate(test_datas)):
        instruction = data["instruction"]
        app = f"task_{idx}"
        app_path = os.path.join(output_root, app)
        if len(os.listdir(app_path)) == 1:
            base_name = os.listdir(app_path)[0]
            shot_path = os.path.join(output_root, app, base_name, "shots")
        else:
            shot_path = os.path.join(output_root, app, "shots")
        result_path = os.path.join(shot_path, "result.json")
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