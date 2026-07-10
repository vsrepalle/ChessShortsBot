import os
import json
import random
import logging
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeUploader:

    def __init__(self):

        self.logger = logging.getLogger(__name__)

        self.upload_config = self.load_json(
            "config/youtube_upload.json"
        )

        self.title_templates = self.load_json(
            "config/youtube_titles.json"
        )

        self.description_templates = self.load_json(
            "config/youtube_descriptions.json"
        )

        self.hashtag_templates = self.load_json(
            "config/youtube_hashtags.json"
        )

        self.youtube = self.authenticate()

    # ----------------------------------------------------------
    # JSON Loader
    # ----------------------------------------------------------

    def load_json(self, filename):

        path = Path(filename)

        if not path.exists():
            raise FileNotFoundError(filename)

        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)

    # ----------------------------------------------------------
    # OAuth Authentication
    # ----------------------------------------------------------

    def authenticate(self):

        token_file = self.upload_config["tokenFile"]
        client_secret = self.upload_config["clientSecretFile"]

        creds = None

        if os.path.exists(token_file):

            creds = Credentials.from_authorized_user_file(
                token_file,
                SCOPES
            )

        if creds and creds.expired and creds.refresh_token:

            self.logger.info("Refreshing OAuth Token...")

            creds.refresh(Request())

        elif not creds:

            self.logger.info("Opening browser for OAuth Login...")

            flow = InstalledAppFlow.from_client_secrets_file(
                client_secret,
                SCOPES
            )

            creds = flow.run_local_server(port=0)

            with open(token_file, "w") as token:

                token.write(creds.to_json())

        youtube = build(
            "youtube",
            "v3",
            credentials=creds
        )

        self.logger.info("YouTube Authentication Successful")

        return youtube

    # ----------------------------------------------------------
    # Random Template Helper
    # ----------------------------------------------------------

    def random_template(self, items):

        if not items:
            return ""

        return random.choice(items)

    # ----------------------------------------------------------
    # Placeholder Replacement
    # ----------------------------------------------------------

    def replace_variables(self, text, metadata):

        if text is None:
            return ""

        for key, value in metadata.items():

            placeholder = "{" + key + "}"

            text = text.replace(
                placeholder,
                str(value)
            )

        return text

    # ----------------------------------------------------------
    # Opening Specific Hashtags
    # ----------------------------------------------------------

    def get_opening_tags(self, opening_name):

        opening_tags = self.hashtag_templates.get(
            "openings",
            {}
        )

        return opening_tags.get(
            opening_name,
            []
        )

    # ----------------------------------------------------------
    # Safe Dictionary Reader
    # ----------------------------------------------------------

    def get_value(self, data, key, default=""):

        if key not in data:
            return default

        if data[key] is None:
            return default

        return data[key]

    # ----------------------------------------------------------
    # Logging Helper
    # ----------------------------------------------------------

    def log_metadata(self, metadata):

        self.logger.info("--------------------------------------")

        for k, v in metadata.items():

            self.logger.info(f"{k} : {v}")

        self.logger.info("--------------------------------------")
            # ----------------------------------------------------------
    # Detect Content Type
    # ----------------------------------------------------------

    def detect_content_type(self, metadata):

        if self.get_value(metadata, "Tournament"):
            return "brochure"

        if self.get_value(metadata, "White"):
            return "pgn"

        return "advertisement"

    # ----------------------------------------------------------
    # Generate Title
    # ----------------------------------------------------------

    def generate_title(self, metadata):

        content_type = self.detect_content_type(metadata)

        if content_type == "pgn":

            section = "general"

            opening = self.get_value(metadata, "Opening")

            if opening:
                section = "opening"

            templates = self.title_templates["pgn"][section]

        elif content_type == "brochure":

            templates = self.title_templates["brochure"]["tournament"]

        else:

            templates = self.title_templates["advertisement"]

        title = self.random_template(templates)

        return self.replace_variables(title, metadata)

    # ----------------------------------------------------------
    # Generate Description
    # ----------------------------------------------------------

    def generate_description(self, metadata):

        content_type = self.detect_content_type(metadata)

        if content_type == "pgn":

            templates = self.description_templates["pgn"]["templates"]

        else:

            templates = self.description_templates["brochure"]["templates"]

        description = self.random_template(templates)

        description = self.replace_variables(
            description,
            metadata
        )

        footer = "\n".join(
            self.description_templates["footer"]
        )

        description += "\n\n"

        description += footer

        return description

    # ----------------------------------------------------------
    # Generate Hashtags
    # ----------------------------------------------------------

    def generate_hashtags(self, metadata):

        hashtags = []

        hashtags.extend(
            self.hashtag_templates["general"]
        )

        hashtags.extend(
            self.hashtag_templates["shorts"]
        )

        content_type = self.detect_content_type(metadata)

        if content_type == "pgn":

            hashtags.extend(
                self.hashtag_templates["training"]
            )

            opening = self.get_value(
                metadata,
                "Opening"
            )

            hashtags.extend(
                self.get_opening_tags(opening)
            )

        elif content_type == "brochure":

            hashtags.extend(
                self.hashtag_templates["brochure"]
            )

        else:

            hashtags.extend(
                self.hashtag_templates["advertisement"]
            )

        hashtags = list(dict.fromkeys(hashtags))

        limit = self.hashtag_templates["limits"][
            "maximum_hashtags"
        ]

        hashtags = hashtags[:limit]

        return hashtags

    # ----------------------------------------------------------
    # Build Upload Metadata
    # ----------------------------------------------------------

    def build_metadata(self, metadata):

        title = self.generate_title(metadata)

        description = self.generate_description(metadata)

        hashtags = self.generate_hashtags(metadata)

        description += "\n\n"

        description += " ".join(
            "#" + tag.replace(" ", "")
            for tag in hashtags
        )

        upload_metadata = {

            "title": title,

            "description": description,

            "tags": hashtags,

            "categoryId":
                self.upload_config["categoryId"],

            "privacyStatus":
                self.upload_config["privacyStatus"]

        }

        self.log_metadata(upload_metadata)

        return upload_metadata

    # ----------------------------------------------------------
    # Save Metadata JSON
    # ----------------------------------------------------------

    def save_metadata(self, metadata, video_file):

        metadata_folder = Path(
            self.upload_config["metadataFolder"]
        )

        metadata_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        outfile = metadata_folder / (
            Path(video_file).stem + ".json"
        )

        with open(
            outfile,
            "w",
            encoding="utf-8"
        ) as fp:

            json.dump(
                metadata,
                fp,
                indent=4,
                ensure_ascii=False
            )

        self.logger.info(
            f"Metadata saved : {outfile}"
        )

        return outfile

    # ----------------------------------------------------------
    # Prepare Metadata
    # ----------------------------------------------------------

    def prepare_upload(self, metadata, video_file):

        upload_metadata = self.build_metadata(
            metadata
        )

        self.save_metadata(
            upload_metadata,
            video_file
        )

        return upload_metadata
            # ----------------------------------------------------------
    # Upload Thumbnail
    # ----------------------------------------------------------

    def upload_thumbnail(self, video_id, thumbnail_path):

        if not thumbnail_path:
            return

        if not os.path.exists(thumbnail_path):
            self.logger.warning(
                f"Thumbnail not found : {thumbnail_path}"
            )
            return

        try:

            self.youtube.thumbnails().set(

                videoId=video_id,

                media_body=thumbnail_path

            ).execute()

            self.logger.info(
                "Thumbnail uploaded successfully."
            )

        except Exception as ex:

            self.logger.exception(ex)

    # ----------------------------------------------------------
    # Upload Video
    # ----------------------------------------------------------

    def upload_video(
            self,
            video_file,
            metadata,
            thumbnail=None
    ):

        from googleapiclient.http import MediaFileUpload

        body = {

            "snippet": {

                "title":
                    metadata["title"],

                "description":
                    metadata["description"],

                "tags":
                    metadata["tags"],

                "categoryId":
                    metadata["categoryId"]

            },

            "status": {

                "privacyStatus":
                    metadata["privacyStatus"],

                "selfDeclaredMadeForKids":
                    self.upload_config[
                        "selfDeclaredMadeForKids"
                    ],

                "madeForKids":
                    self.upload_config[
                        "madeForKids"
                    ]

            }

        }

        media = MediaFileUpload(

            video_file,

            chunksize=-1,

            resumable=True

        )

        request = self.youtube.videos().insert(

            part="snippet,status",

            body=body,

            media_body=media

        )

        response = None

        while response is None:

            status, response = request.next_chunk()

            if status:

                percent = int(status.progress() * 100)

                print(f"Uploading : {percent}%")

        video_id = response["id"]

        self.logger.info(

            f"Video Uploaded : {video_id}"

        )

        if thumbnail:

            self.upload_thumbnail(

                video_id,

                thumbnail

            )

        return video_id

    # ----------------------------------------------------------
    # Retry Upload
    # ----------------------------------------------------------

    def retry_upload(

            self,

            video_file,

            metadata,

            thumbnail=None

    ):

        retries = self.upload_config[
            "uploadRetries"
        ]

        delay = self.upload_config[
            "retryDelaySeconds"
        ]

        import time

        last_exception = None

        for attempt in range(1, retries + 1):

            try:

                self.logger.info(

                    f"Upload Attempt {attempt}"

                )

                return self.upload_video(

                    video_file,

                    metadata,

                    thumbnail

                )

            except Exception as ex:

                last_exception = ex

                self.logger.exception(ex)

                time.sleep(delay)

        raise last_exception

    # ----------------------------------------------------------
    # Archive Uploaded Video
    # ----------------------------------------------------------

    def archive_video(self, video_file):

        if not self.upload_config[
            "archiveVideo"
        ]:

            return

        archive = Path("output/archive")

        archive.mkdir(

            parents=True,

            exist_ok=True

        )

        destination = archive / Path(video_file).name

        import shutil

        shutil.copy2(

            video_file,

            destination

        )

        self.logger.info(

            f"Archived : {destination}"

        )

    # ----------------------------------------------------------
    # Public Upload API
    # ----------------------------------------------------------

    def upload(

            self,

            video_file,

            metadata,

            thumbnail=None

    ):

        upload_metadata = self.prepare_upload(

            metadata,

            video_file

        )

        video_id = self.retry_upload(

            video_file,

            upload_metadata,

            thumbnail

        )

        self.archive_video(

            video_file

        )

        self.logger.info(

            "Upload Completed Successfully"

        )

        return video_id