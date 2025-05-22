import os

# ���������
directory = "/home/makar/Programming/serverTxt"
exclude_folders = {"node_modules", "__pycache__", "pycache"}
exclude_files = {"desktop.ini", ".DS_Store"}

def print_directory_tree(startpath, indent=""):
    try:
        for item in sorted(os.listdir(startpath)):
            # ������� ������� ������/�����
            if item.startswith("."):
                continue
            
            path = os.path.join(startpath, item)

            if os.path.isdir(path):
                # ������� ����������� ����������
                if item in exclude_folders:
                    continue
                print(f"{indent}├── {item}")
                print_directory_tree(path, indent + "│     ")
            else:
                # ������� ����������� ������
                if item in exclude_files:
                    continue
                print(f"{indent}├──  {item}")
    except PermissionError:
        print(f"{indent} [Permission Denied] {startpath}")

# ������
if __name__ == "__main__":
    print_directory_tree(directory)