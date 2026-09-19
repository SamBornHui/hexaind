import hashlib
import io
import os
import shutil
from pathlib import Path
from decouple import config
from datetime import datetime, timezone
from zipfile import ZipFile, ZipInfo
# from app.env import *

def sha256_sum(file_path):

    # Compute SHA256 of the current file
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    file_hash = sha256_hash.hexdigest()

    return file_hash


def recursive_chown(path, owner, group):
    for dirpath, dirnames, filenames in os.walk(path):
        shutil.chown(dirpath, owner, group)
        for filename in filenames:
            shutil.chown(os.path.join(dirpath, filename), owner, group)



def save_to_share(save_path, f_dict, bool_delete_existing):

    # Try to create folder and all parents (in case they don't already exist)
    save_path.mkdir(parents=True, exist_ok=True)
    converted_paths=[]
    if bool_delete_existing:
        # Delete folder and all children
        shutil.rmtree(str(save_path))
        # Recreate folder
        save_path.mkdir(exist_ok=True)
    
    # Write files to directory
    for f_name, f_ascii in f_dict.items():
        f_path = Path(save_path, f_name)
        with open(f_path, 'wb') as f:
            f.write(f_ascii.encode('utf-8'))
        converted_paths.append(f_path)
    # Set the correct owner and group (so that the files are editable by users from share)
    uid = 1000  # samba
    gid = 100   # users
    # recursive_chown(IMPORT_PATH, uid, gid)
    return converted_paths


def compile_output_zip(f_dict):

    mem_f = io.BytesIO()

    f_date = tuple(datetime.now(timezone.utc).timetuple())

    with ZipFile(mem_f, mode='w') as zf:

        for f_name, f_ascii in f_dict.items():
            # Generate file metadata for zip
            zi = ZipInfo(f_name, f_date)
            # Write contents to zip archive as file
            with zf.open(zi, 'w') as f:
                f.write(f_ascii.encode("utf-8"))

    print("Compiled output zip")

    return mem_f
