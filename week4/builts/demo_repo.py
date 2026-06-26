import ast
import os

def map_single_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    outline = []

    # Look only at the main trunk of the tree
    for node in tree.body:
        
        # If it's a function...
        if isinstance(node, ast.FunctionDef):
            outline.append(f"  def {node.name}()  [Line {node.lineno}]")
            
        # If it's a class...
        elif isinstance(node, ast.ClassDef):
            outline.append(f"  class {node.name}:  [Line {node.lineno}]")
            
            # Look inside the class for its methods
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    outline.append(f"    def {child.name}()")
                    
    return outline
def generate_repo_map(directory):
    print(f"--- REPO MAP FOR: {directory} ---")
    
    # Walk through all folders and files

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                
                # Try to map the file
                try:
                    file_outline = map_single_file(filepath)
                    
                    # If we found classes/functions, print them out!
                    if file_outline:
                        print(f"\n{file}:")
                        for line in file_outline:
                            print(line)
                except SyntaxError:
                    print(f"\n{file}: [Contains Syntax Errors]")

if __name__=="__main__":
    generate_repo_map(r"C:\Users\aarti\ClankerBot\week3")