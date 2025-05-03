import json
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
import editdistance
import os

def load_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def save_jsonl(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def is_duplicate(args):
    item, unique_items, threshold = args
    for u_item in unique_items:
        if abs(len(item['instruction']) - len(u_item['instruction'])) > threshold:
            continue
        if item['instruction'] == u_item['instruction'] or editdistance.eval(item['instruction'], u_item['instruction']) <= threshold:
            return True
    return False

def deduplicate_instructions(input_paths, output_path, threshold=5):
    data = []
    for input_path in input_paths:
        data.extend(load_jsonl(input_path))
    unique_data = []

    with Pool(cpu_count()) as pool:
        for item in tqdm(data, desc='Deduplicating instructions'):
            if not unique_data:
                unique_data.append(item)
                continue

            args = [(item, unique_data, threshold)]
            result = pool.map(is_duplicate, args)[0]

            if not result:
                unique_data.append(item)

    save_jsonl(unique_data, output_path)


# Example usage
if __name__ == '__main__':
    in_dir = "data/train_raw"
    input_paths = [
        os.path.join(in_dir, f) for f in os.listdir(in_dir) if f.endswith(".jsonl")
    ]
    deduplicate_instructions(input_paths, 'data/train_processed/train_deduplicated.jsonl', threshold=50)
