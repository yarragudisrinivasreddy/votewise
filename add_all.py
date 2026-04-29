import os
import ast

def get_exports(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '__all__' in content:
        return None
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return None
        
    exports = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith('_'):
                exports.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith('_'):
                    # Some constants are meant to be exported
                    exports.append(target.id)
    return exports

def add_all_to_file(filepath, exports):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # Find the first line after imports or docstring
    insert_idx = 0
    in_docstring = False
    for i, line in enumerate(lines):
        if i == 0 and line.startswith('"""'):
            if line.strip() == '"""' or line.count('"""') == 2:
                insert_idx = i + 1
            else:
                in_docstring = True
            continue
        if in_docstring:
            if '"""' in line:
                in_docstring = False
                insert_idx = i + 1
            continue
            
        if line.startswith('from __future__ import'):
            insert_idx = i + 1
            continue
            
        if line.strip() == '' and i == insert_idx:
            insert_idx = i + 1
            continue
            
        if line.startswith('import ') or line.startswith('from '):
            continue
            
        if not line.startswith('import ') and not line.startswith('from ') and line.strip() != '':
            # found code! But we should insert __all__ before code, maybe after imports.
            pass
            
    # simpler approach: insert after imports
    # actually, standard is after from __future__ and imports. Let's just insert it before the first Class/Function/Assign that is exported
    
    # Let's find first line that defines an export
    first_def_idx = len(lines)
    for i, line in enumerate(lines):
        if line.startswith('def ') or line.startswith('class ') or (line.split('=')[0].strip() in exports and not line.startswith(' ')):
            first_def_idx = i
            break
            
    # Build __all__ string
    all_str = f'\n__all__ = [{", ".join(repr(e) for e in exports)}]\n\n'
    
    # If the file is __init__.py we can just put it at the end
    if filepath.endswith('__init__.py'):
        lines.append(all_str)
    else:
        # insert before first def
        lines.insert(first_def_idx, all_str)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def main():
    app_dir = os.path.join('d:\\hackathon\\votewise', 'app')
    for root, dirs, files in os.walk(app_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                exports = get_exports(filepath)
                if exports is not None: # Means it doesn't have __all__
                    if exports or file == '__init__.py': # if empty exports but it's init, we can add __all__ = []
                        add_all_to_file(filepath, exports)
                        print(f"Added __all__ to {filepath}")

if __name__ == '__main__':
    main()
