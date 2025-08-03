import os

def generate_tree(startpath, output_file, max_level=5):
    with open(output_file, 'w', encoding='utf-8') as f:
        for root, dirs, files in os.walk(startpath):
            level = root.replace(startpath, '').count(os.sep)
            if level >= max_level:
                continue
            indent = '│   ' * level + '├── '
            f.write(f"{indent}{os.path.basename(root)}/\n")
            subindent = '│   ' * (level + 1)
            for file in files:
                f.write(f"{subindent}{file}\n")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(current_dir, 'folder_structure.txt')
    generate_tree(current_dir, output_file)
    print(f"✅ Folder structure saved to {output_file}")
