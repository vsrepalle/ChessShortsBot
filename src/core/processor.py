import os
import shutil
import logging
import yaml
import time
import sys
from pathlib import Path

from src.core.youtube_uploader import YouTubeUploader
from src.processors.pgn_processor import PGNProcessor
from src.processors.brochure_processor import BrochureProcessor


class Pipeline:

    # ==========================================================
    # Constructor
    # ==========================================================

    def __init__(self, config_path):

        self.config_path = config_path

        self.config = self.load_config(config_path)

        self.logger = self.setup_logger()

        self.create_folders()

        self.youtube = YouTubeUploader()

        self.logger.info("=" * 60)
        self.logger.info("Chess Shorts Bot Initialized")
        self.logger.info("=" * 60)

    # ==========================================================
    # Load YAML Configuration
    # ==========================================================

    def load_config(self, filename):

        if not os.path.exists(filename):

            raise FileNotFoundError(filename)

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as fp:

            return yaml.safe_load(fp)

    # ==========================================================
    # Logger
    # ==========================================================

    def setup_logger(self):

        logger = logging.getLogger("ChessShortsBot")

        logger.setLevel(logging.INFO)

        if logger.handlers:
            return logger

        formatter = logging.Formatter(

            "%(asctime)s - %(levelname)s - %(message)s"

        )

        console = logging.StreamHandler()

        console.setFormatter(formatter)

        logger.addHandler(console)

        log_folder = Path("logs")

        log_folder.mkdir(

            parents=True,

            exist_ok=True

        )

        logfile = logging.FileHandler(

            log_folder / "pipeline.log",

            encoding="utf-8"

        )

        logfile.setFormatter(formatter)

        logger.addHandler(logfile)

        return logger

    # ==========================================================
    # Create Required Folders
    # ==========================================================

    def create_folders(self):

        folders = [

            "inputs/pending",

            "inputs/pending/pgn",

            "inputs/pending/brochures",

            "inputs/archive",

            "inputs/archive/pgn",

            "inputs/archive/brochures",

            "inputs/processed",

            "output",

            "output/videos",

            "output/thumbnails",

            "output/metadata",

            "temp",

            "temp/frames",

            "temp/audio",

            "logs"

        ]

        for folder in folders:

            Path(folder).mkdir(

                parents=True,

                exist_ok=True

            )

    # ==========================================================
    # Banner
    # ==========================================================

    def banner(self):

        self.logger.info("")

        self.logger.info("=" * 60)

        self.logger.info("Chess Shorts Bot")

        self.logger.info("Version : 1.0.0")

        self.logger.info("=" * 60)

        self.logger.info("")

    # ==========================================================
    # Count Pending Files
    # ==========================================================

    def pending_files(self):

        pending = []

        root = Path("inputs/pending")

        if not root.exists():

            return pending

        for ext in (

            "*.pgn",

            "*.pdf",

            "*.png",

            "*.jpg",

            "*.jpeg"

        ):

            pending.extend(

                root.rglob(ext)

            )

        return pending

    # ==========================================================
    # Print Summary
    # ==========================================================

    def summary(self):

        files = self.pending_files()

        self.logger.info("")

        self.logger.info("=" * 60)

        self.logger.info(

            f"Pending Files : {len(files)}"

        )

        self.logger.info("=" * 60)

        self.logger.info("")

    # ==========================================================
    # PGN Processing
    # ==========================================================

    def process_pgn(self, file_path):

        self.logger.info("----------------------------------------")
        self.logger.info("Processing PGN")
        self.logger.info(file_path)

        processor = PGNProcessor(self.config)

        print("STEP 3 - Calling processor.process()")
        result = processor.process(file_path)
        print("STEP 4 - processor.process() returned")

        if result is None:

            self.logger.error("PGN processing failed.")

            return

        video_file = result["video"]
        thumbnail = result.get("thumbnail")
        metadata = result["metadata"]

        self.logger.info("Uploading PGN Video...")

        video_id = self.youtube.upload(
            video_file=video_file,
            metadata=metadata,
            thumbnail=thumbnail
        )

        self.logger.info(f"Upload Successful : {video_id}")

        self.archive_file(file_path)

    # ==========================================================
    # Brochure Processing
    # ==========================================================

    def process_brochure(self, file_path):
        import time
        import os
        import sys
        from pathlib import Path
        
        self.logger.info("=" * 60)
        self.logger.info("Entered Pipeline.process_brochure()")
        self.logger.info(f"Input File : {file_path}")
        
        # Wait for file to be ready
        time.sleep(0.5)
        
        self.logger.info("-" * 40)
        self.logger.info("Processing Brochure")
        self.logger.info(file_path)
        
        # FORCE RELOAD - Remove from sys.modules
        if 'src.processors.brochure_processor' in sys.modules:
            del sys.modules['src.processors.brochure_processor']
            print("⚠️ Removed cached module")
        
        # Now import fresh
        import src.processors.brochure_processor
        from src.processors.brochure_processor import BrochureProcessor
        
        print("STEP 1 - About to create BrochureProcessor")
        print(f"📁 BrochureProcessor file: {src.processors.brochure_processor.__file__}")
        processor = BrochureProcessor(self.config)
        print("STEP 2 - BrochureProcessor created")
        
        print("STEP 3 - Calling processor.process()")
        result = processor.process(file_path)
        print("STEP 4 - processor.process() returned")
        
        print(f"📊 Result: {result}")
        print(f"📊 Result keys: {result.keys() if result else 'None'}")
        
        if result is None:
            self.logger.error("Brochure processing failed.")
            return
        
        # Check if user skipped
        if result.get('skipped', False):
            self.logger.info("User chose to skip upload")
            self.archive_file(file_path)
            return
        
        # Get video path
        video_file = result.get("video")
        if not video_file:
            self.logger.error("No video path returned")
            return
        
        # Verify video exists and has content
        if not os.path.exists(video_file):
            self.logger.error(f"Video file not found: {video_file}")
            return
        
        video_size = os.path.getsize(video_file)
        if video_size < 10000:  # Less than 10KB
            self.logger.error(f"Video file too small: {video_size} bytes")
            return
        
        self.logger.info(f"Video ready: {video_file} ({video_size:,} bytes)")
        
        # Get thumbnail and metadata
        thumbnail = result.get("thumbnail")
        metadata = result.get("metadata", {})
        
        self.logger.info("Uploading Brochure Video...")
        
        try:
            video_id = self.youtube.upload(
                video_file=video_file,
                metadata=metadata,
                thumbnail=thumbnail
            )
            
            self.logger.info(f"Upload Successful : {video_id}")
            
            # Only archive if upload was successful
            self.archive_file(file_path)
            
        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            # Don't archive if upload failed
            raise

    # Detect File Type
    # ==========================================================

    def get_file_type(self, file_path):

        extension = Path(file_path).suffix.lower()

        if extension == ".pgn":

            return "pgn"

        if extension in [

            ".pdf",

            ".png",

            ".jpg",

            ".jpeg"

        ]:

            return "brochure"

        return "unknown"

    # ==========================================================
    # Build Default Metadata
    # ==========================================================

    def build_default_metadata(self, file_path):

        return {

            "Title": Path(file_path).stem,

            "Tournament": "",

            "White": "",

            "Black": "",

            "Opening": "",

            "Venue": "",

            "Date": "",

            "Result": "",

            "Prize": "",

            "EntryFee": ""

        }

    # ==========================================================
    # Validate File
    # ==========================================================

    def validate_file(self, file_path):

        if not os.path.exists(file_path):

            self.logger.error(

                f"File does not exist : {file_path}"

            )

            return False

        if os.path.getsize(file_path) == 0:

            self.logger.error(

                "File is empty."

            )

            return False

        return True

    # ==========================================================
    # Archive Original File
    # ==========================================================

    def archive_file(self, file_path):

        archive_root = Path(

            self.config["folders"]["archive"]

        )

        archive_root.mkdir(

            parents=True,

            exist_ok=True

        )

        destination = archive_root / Path(file_path).name

        shutil.move(

            file_path,

            destination

        )

        self.logger.info(

            f"Archived : {destination}"

        )

    # ==========================================================
    # Process Single File
    # ==========================================================

    def process_file(self, file_path):

        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info(f"Processing : {file_path}")
        self.logger.info("=" * 70)

        if not self.validate_file(file_path):
            return

        file_type = self.get_file_type(file_path)

        try:

            if file_type == "pgn":

                self.process_pgn(file_path)

            elif file_type == "brochure":

                self.process_brochure(file_path)

            else:

                self.logger.warning(
                    f"Unsupported file type : {file_path}"
                )

        except Exception as ex:

            self.logger.exception(ex)

            self.move_to_failed(file_path)

    # ==========================================================
    # Move Failed Files
    # ==========================================================

    def move_to_failed(self, file_path):

        failed_folder = Path("inputs/failed")

        failed_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        destination = failed_folder / Path(file_path).name

        try:

            shutil.move(
                file_path,
                destination
            )

            self.logger.error(
                f"Moved to failed folder : {destination}"
            )

        except Exception as ex:

            self.logger.exception(ex)

    # ==========================================================
    # Scan Pending Folder
    # ==========================================================

    def scan_pending_folder(self):

        pending = []

        root = Path("inputs/pending")

        if not root.exists():

            return pending

        extensions = [

            "*.pgn",

            "*.pdf",

            "*.png",

            "*.jpg",

            "*.jpeg"

        ]

        for ext in extensions:

            pending.extend(

                root.rglob(ext)

            )

        pending.sort()

        return pending

    # ==========================================================
    # Batch Processing
    # ==========================================================

    def process_pending_files(self):

        files = self.scan_pending_folder()

        total = len(files)

        if total == 0:

            self.logger.info(
                "No pending files."
            )

            return

        self.logger.info(
            f"{total} pending file(s) found."
        )

        success = 0
        failed = 0

        for index, file in enumerate(files, start=1):

            self.logger.info("")
            self.logger.info(
                f"[{index}/{total}] {file.name}"
            )

            try:

                self.process_file(
                    str(file)
                )

                success += 1

            except Exception as ex:

                failed += 1

                self.logger.exception(ex)

        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("Batch Completed")
        self.logger.info("=" * 70)
        self.logger.info(f"Success : {success}")
        self.logger.info(f"Failed  : {failed}")
        self.logger.info("=" * 70)

    # ==========================================================
    # Clean Temporary Files
    # ==========================================================

    def cleanup(self):

        temp = Path("temp")

        if not temp.exists():

            return

        extensions = [

            "*.png",

            "*.jpg",

            "*.jpeg",

            "*.wav",

            "*.mp3",

            "*.svg"

        ]

        for ext in extensions:

            for file in temp.rglob(ext):

                try:

                    file.unlink()

                except:

                    pass

    # ==========================================================
    # Startup
    # ==========================================================

    def startup(self):

        self.banner()

        self.summary()

        self.cleanup()

        self.logger.info(
            "Startup Complete."
        )

    # ==========================================================
    # Watch Callback
    # ==========================================================

    def watch_callback(self, file_path):

        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("New File Detected")
        self.logger.info(file_path)
        self.logger.info("=" * 70)

        self.process_file(file_path)

    # ==========================================================
    # Continuous Watch Mode
    # ==========================================================

    def watch(self):

        from src.watchers.folder_watcher import watch

        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("Starting Folder Watcher")
        self.logger.info("=" * 70)

        watch(

            "inputs/pending",

            self.watch_callback

        )

    # ==========================================================
    # Process Existing Files
    # ==========================================================

    def process_existing(self):

        self.logger.info("")

        self.logger.info("Scanning Pending Folder...")

        self.process_pending_files()

    # ==========================================================
    # Main Runner
    # ==========================================================

    def run(self):

        self.startup()

        process_existing = True

        watch_mode = True

        try:

            if process_existing:

                self.process_existing()

            if watch_mode:

                self.watch()

        except KeyboardInterrupt:

            self.logger.info("Interrupted by user.")

        except Exception as ex:

            self.logger.exception(ex)

        finally:

            self.cleanup()

            self.logger.info("Pipeline stopped.")

    # ==========================================================
    # Display Configuration
    # ==========================================================

    def show_configuration(self):

        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("Current Configuration")
        self.logger.info("=" * 70)

        for section, values in self.config.items():

            self.logger.info(f"[{section}]")

            if isinstance(values, dict):

                for key, value in values.items():

                    self.logger.info(

                        f"  {key} : {value}"

                    )

            else:

                self.logger.info(values)

        self.logger.info("=" * 70)

    # ==========================================================
    # Health Check
    # ==========================================================

    def health_check(self):

        folders = [

            "inputs/pending",

            "inputs/archive",

            "output/videos",

            "output/thumbnails",

            "output/metadata",

            "logs"

        ]

        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("Health Check")
        self.logger.info("=" * 70)

        for folder in folders:

            exists = Path(folder).exists()

            status = "OK" if exists else "MISSING"

            self.logger.info(

                f"{folder:<35} {status}"

            )

        self.logger.info("=" * 70)