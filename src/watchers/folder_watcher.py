"""
Folder Watcher Module - Monitors folders for new files
"""

import time
import logging
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FolderWatcherHandler(FileSystemEventHandler):
    """Handler for folder watcher events"""

    def __init__(self, callback):
        self.callback = callback
        self.processed_files = set()

    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Wait until the file exists and its size stops changing
        last_size = -1

        for _ in range(60):
            if path.exists():
                try:
                    size = path.stat().st_size

                    if size > 0 and size == last_size:
                        break

                    last_size = size

                except Exception:
                    pass

            time.sleep(1)

        if str(path) in self.processed_files:
            return

        self.processed_files.add(str(path))

        print(f"📁 File created: {path}")
        self.callback(str(path))

    def on_modified(self, event):
        """
        Ignore modify events.

        Windows generates many modify events while a file is still being copied.
        Processing only the create event avoids duplicate uploads.
        """
        return


class FolderWatcher:
    """Watches a folder for new files"""

    def __init__(self, watch_path, callback, recursive=True):
        """
        Initialize the folder watcher

        Args:
            watch_path: Path to watch
            callback: Function called when a new file is ready
            recursive: Watch subfolders
        """

        self.watch_path = Path(watch_path)
        self.callback = callback
        self.recursive = recursive

        self.handler = FolderWatcherHandler(callback)
        self.observer = None

        self.watch_path.mkdir(parents=True, exist_ok=True)

        logging.info(f"FolderWatcher initialized for: {self.watch_path}")
        print(f"👀 Watching: {self.watch_path} (recursive={self.recursive})")

    def start(self):
        """Start watching"""

        if self.observer is not None:
            return

        self.observer = Observer()

        self.observer.schedule(
            self.handler,
            str(self.watch_path),
            recursive=self.recursive
        )

        self.observer.start()

        logging.info(f"Started watching: {self.watch_path}")
        print(f"✅ Watcher started: {self.watch_path}")

    def stop(self):
        """Stop watching"""

        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

            logging.info(f"Stopped watching: {self.watch_path}")
            print("🛑 Watcher stopped")

    def is_running(self):
        """Returns True if watcher is active"""

        return (
            self.observer is not None
            and self.observer.is_alive()
        )