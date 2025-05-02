import os
from tqdm import tqdm
import json


PRIMARY_CATEGORIES = [
"Content Presentation",
"User Interaction",
"Data Management"
]

INST_PRIMARY_CATEGORIES = [
"Functional Testing",
"Data Display Testing",
"Design Validation Testing"
]

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

        
def main():
    categories = {}
    for cat in PRIMARY_CATEGORIES:
        categories[cat] = {
            "yes_num": 0,
            "partial_num": 0,
            "no_num": 0,
            "start_failed_num": 0,
            "score": 0,
            "total": 0,
            "accuracy": 0
        }
    for cat in INST_PRIMARY_CATEGORIES:
        categories[cat] = {
            "yes_num": 0,
            "partial_num": 0,
            "no_num": 0,
            "start_failed_num": 0,
            "score": 0,
            "total": 0,
            "accuracy": 0
        }
        
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("in_dir", type=str)
    args = parser.parse_args()
    args.in_dir = os.path.join(args.in_dir, "extracted")
    result_dir = os.path.join(args.in_dir, "results")
    
    test_file = "data/test.jsonl"
    test_datas = load_jsonl(test_file)
    total = 0
    for data in test_datas:
        total += len(data["ui_instruct"])
        cat = data["Category"]["primary_category"]
        categories[cat]["total"] += len(data["ui_instruct"])
        for task in data["ui_instruct"]:
            task_cat = task["task_category"]["primary_category"]
            categories[task_cat]["total"] += 1

    tasks = [f for f in os.listdir(result_dir) if os.path.isdir(os.path.join(result_dir, f))]
    score = 0
    yes_num = 0
    partial_num = 0
    no_num = 0
    
    for task in tqdm(tasks):
        if not os.path.exists(os.path.join(result_dir, task, "interact_messages.json")):
            print(f"interact_messages.json not found in {task}, skipping...")
            continue
        
        index = int(task.replace("task_", "").replace("task", "").split("_")[0]) - 1
        sub_index = int(task.replace("task_", "").replace("task", "").split("_")[1])
        cat = test_datas[index]["Category"]["primary_category"]
        task_cat = test_datas[index]["ui_instruct"][sub_index]["task_category"]["primary_category"]
        
        data = load_json(os.path.join(result_dir, task, "interact_messages.json"))
        text = ""
        for message in data[-1::-1]:
            if message["role"] == "assistant":
                text = message["content"]
                break
        if "YES" in text:
            score += 1
            yes_num += 1
            categories[cat]["yes_num"] += 1
            categories[cat]["score"] += 1
            categories[task_cat]["yes_num"] += 1
            categories[task_cat]["score"] += 1
        elif "PARTIAL" in text:
            score += 0.5
            partial_num += 1
            categories[cat]["partial_num"] += 1
            categories[cat]["score"] += 0.5
            categories[task_cat]["partial_num"] += 1
            categories[task_cat]["score"] += 0.5
        else:
            no_num += 1
            categories[cat]["no_num"] += 1
            categories[task_cat]["no_num"] += 1
            
    for cat in categories:
        categories[cat]["start_failed_num"] = categories[cat]["total"] - categories[cat]["yes_num"] - categories[cat]["partial_num"] - categories[cat]["no_num"]
        categories[cat]["accuracy"] = categories[cat]["score"] / categories[cat]["total"] * 100 if categories[cat]["total"] > 0 else 0

    start_failed_num = total - yes_num - partial_num - no_num
    print(f"start_failed: {start_failed_num}")
    test_name = os.path.basename(args.in_dir)
    yes_rate = yes_num / total * 100
    partial_rate = partial_num / total * 100
    no_rate = no_num / total * 100
    start_failed_rate = start_failed_num / total * 100
    accuracy = score / total * 100
    table = f"| test_name | yes_num | partial_num | no_num | start_failed_num | total | yes_rate | partial_rate | no_rate | start_failed_rate | accuracy |" + " | ".join(PRIMARY_CATEGORIES + INST_PRIMARY_CATEGORIES) + " |\n"
    table += "|------|------|------|------|------|------|------|------|------|------|------|" + "------|" * len(PRIMARY_CATEGORIES + INST_PRIMARY_CATEGORIES) + "\n"
    table += f"| {test_name} | {yes_num} | {partial_num} | {no_num}  | {start_failed_num} | {total} | {yes_rate:.1f} | {partial_rate:.1f} | {no_rate:.1f} | {start_failed_rate:.1f} | {accuracy:.1f} |" + " | ".join([f"{categories[cat]['accuracy']:.1f}" for cat in (PRIMARY_CATEGORIES + INST_PRIMARY_CATEGORIES)]) + " |\n"
    
    with open(os.path.join(args.in_dir, "table.md"), "w", encoding="utf-8") as f:
        f.write(table)
        
    print(table)


if __name__ == "__main__":
    main()