from utils.file_utils import delete_if_exists, copy_folder
import os
import time

def sync_output(config, retries=3, delay=0.5):
    src_path = config['build_output']
    for attempt in range(retries):
        if os.path.exists(src_path):
            break
        print(f"[WARN] Build output folder not found: {src_path}. Retrying ({attempt+1}/{retries})...")
        time.sleep(delay)
    else:
        print(f"[ERROR] Build output folder does not exist after retries: {src_path}")
        return
    for dest in config['destinations']:
        print(f"[SYNC] Syncing to {dest}")
        delete_if_exists(dest)
        copy_folder(src_path, dest)
        print("[SYNC] Done.")