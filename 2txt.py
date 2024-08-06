import os

def write_files_to_txt(root_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for subdir, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.py'):  # Можно добавить другие расширения при необходимости
                    file_path = os.path.join(subdir, file)
                    outfile.write(f"\n\n--- {file_path} ---\n\n")
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())

# Использование
write_files_to_txt('app', 'TGBbot.txt')