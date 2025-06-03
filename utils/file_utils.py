import os
import shutil


def delete_if_exists(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def copy_folder(src, dest):
    shutil.copytree(src, dest)


def ensure_folder(path):
    os.makedirs(path, exist_ok=True)
