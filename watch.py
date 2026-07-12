import os

from src.watchers.folder_watcher import watch

from src.core.processor import Pipeline

pipeline = Pipeline(
    config_path="config/config.yaml"
)


def process_file(path):

    ext = os.path.splitext(path)[1].lower()

    print(f"Detected : {path}")

    if ext == ".pgn":

        print("Processing PGN")

        class FileInfo:
            def __init__(self, path):
                self.name = os.path.basename(path)
                self.suffix = ".pgn"

        pipeline.process_pgn(
            FileInfo(path)
        )

    elif ext in [".pdf", ".jpg", ".jpeg", ".png"]:

        print("Processing Brochure")

        # We'll call brochure processor here
        # in the next stage.

    else:

        print("Unsupported File")


watch(
    "inputs/pending",
    process_file
)
