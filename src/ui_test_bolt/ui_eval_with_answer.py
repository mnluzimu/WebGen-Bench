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


ui_prompt_template = """

Task: {task}

Expected Result: {expected_result}

Instructions:
- Attempt the task as a user would, using the UI elements available.
- Make multiple attempts if needed to try and achieve the expected result.
- Observe whether the expected result is fully, partially, or not at all achieved.
- IMPORTANT: You can at most interact with the website 15 times. If the limit is reached, directly output your answer.

At the end of your testing, answer only with one of the following:
- YES: if the expected result was fully achieved.
- NO: if the expected result could not be achieved at all.
- PARTIAL: if only some aspects of the expected result were achieved.

"""



def create_tasks_test(test_file, ports, tasks_file):
    datas = load_jsonl(test_file)
    tasks = []
    for idx, data in tqdm(enumerate(datas)):
        app = f"{idx + 1:06d}"
        if app not in ports.keys():
            continue
        for ui_idx, ui_instruct in enumerate(data["ui_instruct"]):
            instruction = ui_prompt_template.format(task=ui_instruct["task"], expected_result=ui_instruct["expected_result"])
            tasks.append({
                "web_name": data["id"],
                "id": f"{app}_{ui_idx}",
                "ques": instruction,
                "web": f"http://localhost:{ports[app]}/",
                "expected_result": ui_instruct["expected_result"],
                "task": ui_instruct["task"]
            })
    save_jsonl(tasks, tasks_file)


def run_webvoyager(input_dir):
    input_dir = Path(input_dir)                  # Path object for convenience

    cmd = [
        sys.executable,              # equivalent to "python"
        "-u", "webvoyager\\run.py",   # keep Windows backslash
        "--test_file", str(input_dir / "tasks_test_with_answer.jsonl"),
        "--api_key", "sk-mah6FUel7jrB3lNj8c3cnqUGeKy1ovL5DAD1GFge92C7Fe864c8646B1B9DaB6C20a10A896",
        "--api_model", "/mnt/cache/sharemath/models/Qwen/Qwen2.5-VL-32B-Instruct",
        "--headless",
        "--max_iter", "15",
        "--max_attached_imgs", "3",
        "--temperature", "1",
        "--fix_box_color",
        "--seed", "42",
        "--output_dir", str(input_dir / "results"),
        "--download_dir", str(input_dir / "downloads"),
        # "--num_workers", "8"
    ]

    # run the command, raise if it fails
    subprocess.run(cmd, check=True)


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--in_dir", type=str)
    args = parser.parse_args()
    in_dir = args.in_dir
    test_file = "data/test.jsonl"
    zip_files = [os.path.join(in_dir, file) for file in os.listdir(in_dir) if file.endswith(".zip") and not file.startswith("error")]
    
    output_root = os.path.join(in_dir, "extracted")
    if not os.path.exists(output_root):
        os.makedirs(output_root)

    tasks_file = os.path.join(output_root, "tasks_test_with_answer.jsonl")
    log_file = os.path.join(output_root, "log.jsonl")
    log_datas = []
    if os.path.isfile(log_file):
        log_datas = load_jsonl(log_file)
        
    zip_files = zip_files[len(log_datas):]

    unzip_files(zip_files, output_root)

    subprocess.run("pm2 delete all", shell=True)

    batch_size = 5
    for i in tqdm(range(0, len(zip_files), batch_size)):
        batch_zip_files = zip_files[i:i + batch_size]
        commands = get_shell_start(batch_zip_files, output_root)
        ports = start_services(output_root, commands)
        print(ports)

        create_tasks_test(test_file, ports, tasks_file)
        run_webvoyager(output_root)
        
        subprocess.run("pm2 delete all", shell=True)
        
        curr_log_datas = [{"app_path": app_path} for app_path in batch_zip_files]
        save_jsonl(curr_log_datas, log_file, mode="a")


if __name__ == "__main__":
    main()