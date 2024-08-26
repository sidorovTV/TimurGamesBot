import os

def write_files_to_txt(root_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for subdir, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(subdir, file)
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read().strip()
                        if content:
                            outfile.write(f"\n--- {file_path} ---\n{content}\n")

# Использование
write_files_to_txt('app', 'TGBbot.txt')