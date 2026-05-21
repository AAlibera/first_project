import os
import uuid
from pathlib import Path

def ensure_directories():
    directories = [
        "static/uploads",
        "static/results",
        "models"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

async def save_upload_file(upload_file, destination_dir):
    filename = f"{uuid.uuid4().hex}_{upload_file.filename}"
    file_path = os.path.join(destination_dir, filename)
    
    os.makedirs(destination_dir, exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await upload_file.read())
    
    return filename

def get_file_url(filename, directory):
    return f"/{directory}/{filename}"

def generate_unique_filename(original_filename):
    ext = os.path.splitext(original_filename)[1]
    return f"{uuid.uuid4().hex}{ext}"