from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time


class FolderWatcher(FileSystemEventHandler):

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_created(self, event):

        if event.is_directory:
            return

        self.callback(event.src_path)


def watch(folder, callback):

    observer = Observer()

    observer.schedule(
        FolderWatcher(callback),
        folder,
        recursive=True
    )

    observer.start()

    print(f"Watching: {folder}")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        observer.stop()

    observer.join()