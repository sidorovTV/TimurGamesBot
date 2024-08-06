import os
import ast


def extract_functions(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read())

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            prefix = 'async ' if isinstance(node, ast.AsyncFunctionDef) else ''
            functions.append(f"{prefix}{node.name}")

    return functions


def process_directory(directory):
    results = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                functions = extract_functions(file_path)
                if functions:
                    results.append(f"File: {file_path}")
                    for func in functions:
                        results.append(f"  - {func}")
                    results.append("")  # Add an empty line for readability
    return results


def main():
    project_directory = input("Введите путь к директории вашего проекта: ")
    output_file = "functions_list.txt"

    results = process_directory(project_directory)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(results))

    print(f"Список функций сохранен в файл {output_file}")


if __name__ == "__main__":
    main()