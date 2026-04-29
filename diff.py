import filecmp
import os

def print_diff(dir1, dir2):
    dcmp = filecmp.dircmp(dir1, dir2, ignore=['venv', '.git', 'votewise-v2', 'votewise-v3', '__pycache__', '.pytest_cache'])
    if dcmp.diff_files:
        print(f"[{dir1}] modified: {dcmp.diff_files}")
    if dcmp.right_only:
        print(f"[{dir1}] added (in v3): {dcmp.right_only}")
    if dcmp.left_only:
        print(f"[{dir1}] deleted (in v3): {dcmp.left_only}")
    
    for c in dcmp.common_dirs:
        print_diff(os.path.join(dir1, c), os.path.join(dir2, c))

print_diff(r"d:\hackathon\votewise", r"d:\hackathon\votewise\votewise-v3")
