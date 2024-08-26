import os
import json
import base64

def list_files_and_contents(startpath):
    file_data = []
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        dir_entry = {
            "name": f"{indent}{os.path.basename(root)}/",
            "type": "directory",
            "contents": []
        }
        for f in files:
            file_path = os.path.join(root, f)
            try:
                with open(file_path, 'rb') as file:
                    content = base64.b64encode(file.read()).decode('utf-8')
                file_entry = {
                    "name": f"{' ' * 4 * (level + 1)}{f}",
                    "type": "file",
                    "content": content
                }
                dir_entry["contents"].append(file_entry)
            except Exception as e:
                print(f"Error reading file {file_path}: {str(e)}")
        file_data.append(dir_entry)
    return file_data

app_directory = 'app'
output_file = 'app_files_and_contents.json'

files_and_contents = list_files_and_contents(app_directory)

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(files_and_contents, f, ensure_ascii=False, indent=2)

print(f"File list and contents have been written to {output_file}")