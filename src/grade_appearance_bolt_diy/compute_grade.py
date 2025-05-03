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

import re

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


def first_grade_int(text: str) -> int:
    """
    Return the first integer that appears *anywhere after* the substring
    'Grade' (case–insensitive).  
    If no such integer exists, return 0.

    Parameters
    ----------
    text : str
        The input string to scan.

    Returns
    -------
    int
        The first integer following the word 'Grade', or 0 if none found.
    """
    #  ▸ 'Grade'  (any capitalization)
    #  ▸ .*?       any characters (non‑greedy) including newlines
    #  ▸ (-?\d+)   capture an optional sign and at least one digit
    match = re.search(r'Grade.*?(\d)', text, flags=re.IGNORECASE | re.DOTALL)
    return int(match.group(1)) if match else 0
    
            
def get_grade(in_dir, prefix):
    app_paths = [get_app_path(in_dir, app) for app in os.listdir(in_dir) if app.startswith(prefix)]
    
    total_grade = 0
    for app_path in tqdm(app_paths):
        result_path = os.path.join(app_path, "shots", "result.json")
        if not os.path.isfile(result_path):
            continue
        result = load_json(result_path)
        grade = first_grade_int(result["model_output"])
        total_grade += grade
        
    grade = round(total_grade / 101, 2)
    save_json({"grade": grade}, os.path.join(in_dir, "grade.json"))
    
    return grade
        
        
if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Compute the grade based on model output.")
    parser.add_argument("--in_dir", default="downloads/OpenAILike/Qwen2.5-Coder-32B-Instruct", help="Path to the input directory")
    parser.add_argument("--prefix", default="00", help="Prefix for the app directories")
    args = parser.parse_args()
    in_dir = os.path.join(args.in_dir, "extracted")
    prefix = args.prefix
    print(get_grade(in_dir, prefix))
    