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


def get_shell_start(app_paths, output_root):
    commands = {}
    for app_path in tqdm(app_paths):
        commands[os.path.basename(app_path)] = {"shell_actions": [], "last_start_action": ""}

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
        app = f"task_{idx}"
        if app not in ports.keys():
            continue
        for ui_idx, ui_instruct in enumerate(data["ui_instruct"]):
            instruction = ui_prompt_template.format(task=ui_instruct["task"], expected_result=ui_instruct["expected_result"])
            tasks.append({
                "web_name": data["url"],
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
        "--num_workers", "8"
    ]

    # run the command, raise if it fails
    subprocess.run(cmd, check=True)


def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--in_dir", type=str)
    args = parser.parse_args()
    in_dir = args.in_dir
    test_file = "data\\app-bench.jsonl"
    app_paths = [os.path.join(in_dir, f"task_{idx}") for idx in range(101)]
    output_root = in_dir
    tasks_file = os.path.join(output_root, "tasks_test_with_answer.jsonl")
    log_file = os.path.join(output_root, "log.jsonl")
    log_datas = []
    if os.path.isfile(log_file):
        log_datas = load_jsonl(log_file)
        
    app_paths = app_paths[len(log_datas):]

    batch_size = 5
    for i in range(0, len(app_paths), batch_size):

        batch_app_paths = app_paths[i:i + batch_size]
        commands = get_shell_start(batch_app_paths, output_root)
        print(commands)
        ports = start_services(output_root, commands)
        print(ports)

        create_tasks_test(test_file, ports, tasks_file)

        run_webvoyager(output_root)
        
        subprocess.run("pm2 delete all", shell=True)
        
        curr_log_datas = [{"app_path": app_path} for app_path in batch_app_paths]
        save_jsonl(curr_log_datas, log_file, mode="a")


if __name__ == "__main__":
    main()