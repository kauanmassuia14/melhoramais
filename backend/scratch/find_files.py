import os

start_dir = "/home/kauanmassuia/projeto-melhoramais"
print("Excel files in workspace:")
for root, dirs, files in os.walk(start_dir):
    # Skip virtual environments or node_modules or .git
    if any(p in root for p in [".git", "node_modules", "__pycache__", ".next", ".vercel"]):
        continue
    for file in files:
        if file.endswith((".xlsx", ".xls", ".csv")):
            path = os.path.join(root, file)
            size = os.path.getsize(path)
            print(f"  {path} ({size} bytes)")
