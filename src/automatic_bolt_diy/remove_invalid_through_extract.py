import os
import json
import sys
import shutil
from tqdm import tqdm
import zipfile

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
            

def process_directory(directory):
    extracted_directory = os.path.join(directory, "extracted")
    zip_file_paths = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.zip') and f.startswith("0")]
    unzip_files(zip_file_paths, extracted_directory)
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        # Skip directories and non-JSON files
        if not os.path.isfile(filepath) or not filename.endswith('.json') or filename.startswith('error-'):
            continue
        
        try:
            with open(filepath, 'r', encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"Skipping invalid JSON file: {filename}")
            continue
        
        messages = data.get('messages', [])
        if not isinstance(messages, list):
            print(f"Skipping {filename}: 'messages' is not a list")
            continue
        
        if not messages:
            continue  # No messages to check
        
        last_message = messages[-1]
        content = last_message.get('content')

        curr_extracted_dir = os.path.join(extracted_directory, filename.replace(".json", ""))
        # print(curr_extracted_dir)
        if os.path.exists(curr_extracted_dir):
            not_json_files = [f for f in os.listdir(curr_extracted_dir) if not f.startswith('package') and not f == "node_modules" and not f == "start-wrapper.cjs"]
            if len(not_json_files) == 0:
                print(f"Removing empty extracted directory: {curr_extracted_dir}")
                shutil.rmtree(curr_extracted_dir)
                should_remove = True
            else:
                should_remove = False
        
        # Check if content exists and is an empty string
        if isinstance(content, str) and content == '' or should_remove:
            new_filename = f"error-{filename}"
            new_filepath = os.path.join(directory, new_filename)
            
            if os.path.exists(new_filepath):
                os.remove(new_filepath)  # Remove existing file with the same name
            if os.path.exists(new_filepath.replace(".json", ".zip")):
                os.remove(new_filepath.replace(".json", ".zip"))
            os.rename(filepath, new_filepath)
            os.rename(filepath.replace(".json", ".zip"), new_filepath.replace(".json", ".zip"))
            print(f"Renamed: {filename} -> {new_filename}")

if __name__ == '__main__':
    target_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    process_directory(target_dir)