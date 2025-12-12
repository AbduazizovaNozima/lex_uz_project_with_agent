import os

path = "sandbox:/home/nozima/langchain_first_project/static/registration.png"
clean_path = path.replace("sandbox:", "")

print(f"Original path: {path}")
print(f"Exists? {os.path.exists(path)}")

print(f"Clean path: {clean_path}")
print(f"Exists? {os.path.exists(clean_path)}")
