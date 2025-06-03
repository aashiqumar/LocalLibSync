import json
import time
import os
import sys

def load_config(config_path='config/projects.json'):
    with open(config_path, 'r') as f:
        return json.load(f)

def run_watchers():
    from services.watcher import start_watcher
    config = load_config()
    for lib in config.get('libraries', []):
        build_output = lib.get('build_output')
        if not build_output or not os.path.exists(build_output):
            print(f"[WARN] Build output folder does not exist for {lib['name']}: {build_output}")
            print(f"[INFO] Waiting for build output to be created...")
        else:
            print(f"[INFO] Watching build output for {lib['name']}: {build_output}")
        start_watcher(lib)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Stopped watching.")

def run_gui():
    from ui.app_ui import launch_app
    launch_app()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'watch':
        run_watchers()
    else:
        run_gui()