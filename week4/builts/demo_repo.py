import ast
import os

def list_definitions(filepath):
    """
    Parses a Python file and returns a structured list of dictionaries 
    containing metadata about classes, functions, and methods.
    """
    definitions = []
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        
        # Parse the source code into an Abstract Syntax Tree
        tree = ast.parse(source)
    except (SyntaxError, FileNotFoundError) as e:
        # If the file doesn't exist or has invalid Python syntax, return empty
        
        return f"Error parsing {filepath}: {e}"

    # Look only at the main trunk of the tree
    for node in tree.body:
        
        # 1. If it's a standalone function...
        if isinstance(node, ast.FunctionDef):
            definitions.append({
                "kind": "function",
                "name": node.name,
                "line": node.lineno,
                # end_lineno is available in Python 3.8+
                "end_line": getattr(node, 'end_lineno', node.lineno) 
            })
            
        # 2. If it's a class...
        elif isinstance(node, ast.ClassDef):
            definitions.append({
                "kind": "class",
                "name": node.name,
                "line": node.lineno,
                "end_line": getattr(node, 'end_lineno', node.lineno)
            })
            
            # Look inside the class for its methods
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    definitions.append({
                        "kind": "method",
                        "name": child.name,
                        "line": child.lineno,
                        "end_line": getattr(child, 'end_lineno', child.lineno)
                    })
                    
    return definitions

def generate_repo_map(directory):
    """
    Walks a directory, maps all Python files using list_definitions, 
    and prints a readable outline of the repository.
    """
    print(f"--- REPO MAP FOR: {directory} ---")
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                
                # Fetch the structured definitions
                file_outline = list_definitions(filepath)
                
                # If we found classes/functions/methods, print them out
                if file_outline:
                    print(f"\n{file}:")
                    for item in file_outline:
                        if item["kind"] == "class":
                            print(f"  class {item['name']}:  [Lines {item['line']}-{item['end_line']}]")
                        elif item["kind"] == "method":
                            print(f"    def {item['name']}()  [Lines {item['line']}-{item['end_line']}]")
                        elif item["kind"] == "function":
                            print(f"  def {item['name']}()  [Lines {item['line']}-{item['end_line']}]")

if __name__ == "__main__":
    # Test the mapping logic on your local directory
    target_dir = r"C:\Users\aarti\ClankerBot\week3"
    
    if os.path.exists(target_dir):
        generate_repo_map(target_dir)
    else:
        print(f"Directory not found: {target_dir}")