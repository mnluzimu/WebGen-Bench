import glob
import os
import shutil

def remove_node_modules():
    base_patterns = [
      r"D:\research\bolt\APP-Bench\data\oh_deepseek-v3\workspaces\workspace_*\start-wrapper.cjs",
    ]
    
    # Use glob to find all matching node_modules directories (recursive search).
    directories = []
    for base_pattern in base_patterns:
      directories.extend(glob.glob(base_pattern, recursive=True))
    
    print(directories)
    for dir_path in directories:
        if os.path.isfile(dir_path):
            print(f"Removing: {dir_path}")
            shutil.os.remove(dir_path)
        elif os.path.isdir(dir_path):
            print(f"Removing directory: {dir_path}")
            shutil.rmtree(dir_path)


if __name__ == "__main__":
    remove_node_modules()
