import os
from tqdm import tqdm
import json

def count_tokens(in_dir):
    in_files = [os.path.join(in_dir, f, "agent.log") for f in os.listdir(in_dir) if os.path.isdir(os.path.join(in_dir, f))]
    # Prompt Tokens: 7492; Completion Tokens: 69
    prompt_tokens = 0
    completion_tokens = 0
    for in_file in tqdm(in_files):
        print(f"Processing {in_file}...")
        if not os.path.exists(in_file):
            print(f"{in_file} not found, skipping...")
            continue
        with open(in_file, "r", encoding="utf-8", errors='replace') as f:
            for line in f:
                if "Prompt Tokens:" in line:
                    prompt_tokens += int(line.split("Prompt Tokens: ")[1].split(";")[0].strip())
                    completion_tokens += int(line.split("Completion Tokens: ")[1].strip())
    
    total_price = prompt_tokens * 2.5 / 1000000 + completion_tokens * 15 / 1000000

    output_file = os.path.join(in_dir, "tokens.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_price": total_price}, f, indent=4)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("in_dir", type=str)
    args = parser.parse_args()
    
    count_tokens(args.in_dir)