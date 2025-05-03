from prompt_select_template_system import starterTemplateSelectionPrompt
from prompt_generate_artifect import systemPrompt
import requests
import time
import os
from tqdm import tqdm
import json
from argparse import ArgumentParser
import re


def load_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding="utf-8") as f:
        for line in tqdm(f):
            data.append(json.loads(line))
    return data


def save_jsonl(data, out_file, mode="w"):
    with open(out_file, mode, encoding="utf-8") as f:
        for d in data:
            f.write(json.dumps(d, ensure_ascii=False) + '\n')


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


template_names = {
    "astro": 'bolt-astro-basic',
    "nextjs": 'bolt-nextjs-shadcn',
    "my-qwik-basic-starter": 'bolt-qwik-ts',
    "slidev": 'bolt-slidev',
    "vite-starter": 'vanilla-vite',
    "vite-react-typescript-starter": 'bolt-vite-react',
    "vite-vue-typescript-starter": 'bolt-vue',
    "angular-starter": 'bolt-angular'
}


def get_instruction_template_messages(data):
    messages = []
    for e in data["messages"]:
        content = e["content"]
        if isinstance(content, str):
            if content.startswith("[Model: "):
                content = "\n\n".join(content.split("\n\n")[2:])
            messages.append({"role": e["role"], "content": content})
        else:
            if content[0]["text"].startswith("[Model: "):
                content[0]["text"] = "\n\n".join(content[0]["text"].split("\n\n")[2:])
            messages.append({"role": e["role"], "content": content[0]["text"]})
    if len(messages) < 2:
        return None, None, None, None
    instruction = messages[0]["content"]
    import_files = messages[1]["content"]
    template = "blank"
    for key in template_names.keys():
        if key in import_files:
            template = template_names[key]
    
    match = re.search(r'<boltArtifact[^>]*title="([^"]+)"', import_files)
    title = match.group(1) if match else None
    return messages, instruction, template, title
    

def main():
    in_dirs = [
        "data/train_data/deepseek-chat-v3-0324_free_train_filtered",
    ]
    out_file_select = "data/train_data/messages_select.jsonl"
    out_file_generate = "data/train_data/messages_generate.jsonl"

    select_datas = []
    generate_datas = []
    for in_dir, ref_file in zip(in_dirs, ref_files):
        ref_datas = load_jsonl(ref_file)
        for idx, ref_data in tqdm(enumerate(ref_datas)):
            in_file = os.path.join(in_dir, f"{idx + 1:06d}.json")
            if not os.path.isfile(in_file):
                continue

            data = load_json(in_file)

            messages, instruction, template, title = get_instruction_template_messages(data)
            select_datas.append({"messages": [
                {"role": "system", "content": starterTemplateSelectionPrompt},
                {"role": "user", "content": instruction},
                {"role": "assistant", "content": f"""<selection>
    <templateName>{template}</templateName>
    <title>{title}</title>
    </selection>"""}
            ],
            "instruction": instruction,
            })
            generate_datas.append({"messages": [{"role": "system", "content": systemPrompt}] + messages, "instruction": instruction})
            

    save_jsonl(select_datas, out_file_select)
    save_jsonl(generate_datas, out_file_generate)


if __name__ == "__main__":
    main()

