import os
import zipfile

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_ZIP = os.path.join(PROJECT_DIR, "ForexMindAI_Cloud_Package.zip")

ignore_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', '.idea', '.vscode'}
ignore_exts = {'.pyc', '.pyo'}

print("Creating cloud deployment package...")

with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as ziph:
    for root, dirs, files in os.walk(PROJECT_DIR):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for file in files:
            if any(file.endswith(ext) for ext in ignore_exts):
                continue
            if file == "ForexMindAI_Cloud_Package.zip":
                continue
            
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, PROJECT_DIR)
            ziph.write(full_path, rel_path)

print(f"Package created successfully: {OUTPUT_ZIP} ({os.path.getsize(OUTPUT_ZIP)} bytes)")
