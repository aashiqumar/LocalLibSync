import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from services.builder import build_library
from services.syncer import sync_output


class ChangeHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config

    def on_any_event(self, event):
        if event.is_directory:
            return
        print(f"[CHANGE] Detected change in {event.src_path}")
        build_library(self.config)
        sync_output(self.config)


def start_watcher(config):
    path = config['src']
    event_handler = ChangeHandler(config)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
