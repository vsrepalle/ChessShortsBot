import os
import shutil
import logging

from pathlib import Path

import chess
import chess.svg
import cairosvg

from PIL import Image

from moviepy.editor import (
    ImageSequenceClip,
    CompositeVideoClip,
    TextClip,
    AudioFileClip
)


class PGNRenderer:

    def __init__(self, config):

        self.config = config

        self.logger = logging.getLogger(
            "ChessShortsBot"
        )

        self.temp_folder = Path(
            "temp/frames"
        )

        self.output_folder = Path(
            "output/videos"
        )

        self.thumbnail_folder = Path(
            "output/thumbnails"
        )

        self.temp_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        self.output_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        self.thumbnail_folder.mkdir(
            parents=True,
            exist_ok=True
        )

    # ==================================================
    # Render
    # ==================================================

    def render(
            self,
            game,
            metadata
    ):

        self.clear_frames()

        board = game.board()

        frame_files = []

        frame_number = 0

        frame = self.create_board_frame(

            board,

            frame_number

        )

        frame_files.append(frame)

        for move in game.mainline_moves():

            board.push(move)

            frame_number += 1

            frame = self.create_board_frame(

                board,

                frame_number

            )

            frame_files.append(frame)

        video = self.create_video(

            frame_files,

            metadata

        )

        thumbnail = self.generate_thumbnail(

            frame_files,

            metadata

        )

        return {

            "video": video,

            "thumbnail": thumbnail

        }

    # ==================================================
    # SVG → PNG
    # ==================================================

    def create_board_frame(

            self,

            board,

            frame_number

    ):

        svg = chess.svg.board(

            board=board,

            size=900

        )

        png_file = self.temp_folder / (

            f"frame_{frame_number:04d}.png"

        )

        cairosvg.svg2png(

            bytestring=svg.encode(),

            write_to=str(png_file)

        )

        return str(png_file)

    # ==================================================
    # Cleanup
    # ==================================================

    def clear_frames(self):

        if self.temp_folder.exists():

            shutil.rmtree(

                self.temp_folder

            )

        self.temp_folder.mkdir(

            parents=True,

            exist_ok=True

        )
            # ==================================================
    # Create Video
    # ==================================================

    def create_video(
            self,
            frame_files,
            metadata
    ):

        self.logger.info(
            "Creating MP4..."
        )

        clip = ImageSequenceClip(
            frame_files,
            fps=1
        )

        duration = clip.duration

        overlays = []

        white = metadata.get(
            "White",
            "White"
        )

        black = metadata.get(
            "Black",
            "Black"
        )

        opening = metadata.get(
            "OpeningDisplay",
            ""
        )

        result = metadata.get(
            "Result",
            ""
        )

        white_clip = TextClip(
            txt=f"White : {white}",
            fontsize=40,
            color="white",
            method="caption",
            size=(900, None)
        ).set_duration(duration)

        white_clip = white_clip.set_position(
            ("center", 20)
        )

        overlays.append(
            white_clip
        )

        black_clip = TextClip(
            txt=f"Black : {black}",
            fontsize=40,
            color="white",
            method="caption",
            size=(900, None)
        ).set_duration(duration)

        black_clip = black_clip.set_position(
            ("center", 80)
        )

        overlays.append(
            black_clip
        )

        opening_clip = TextClip(
            txt=opening,
            fontsize=34,
            color="yellow",
            method="caption",
            size=(900, None)
        ).set_duration(duration)

        opening_clip = opening_clip.set_position(
            ("center", 140)
        )

        overlays.append(
            opening_clip
        )

        footer = TextClip(
            txt="Subscribe for Daily Chess Shorts",
            fontsize=36,
            color="white",
            method="caption",
            size=(900, None)
        ).set_duration(duration)

        footer = footer.set_position(
            ("center", 950)
        )

        overlays.append(
            footer
        )

        result_clip = TextClip(
            txt=f"Result : {result}",
            fontsize=34,
            color="cyan",
            method="caption",
            size=(900, None)
        ).set_duration(duration)

        result_clip = result_clip.set_position(
            ("center", 890)
        )

        overlays.append(
            result_clip
        )

        final_video = CompositeVideoClip(
            [clip] + overlays
        )

        music = self.add_background_music()

        if music is not None:

            final_video = final_video.set_audio(
                music
            )

        outfile = self.output_folder / (

            metadata["FileName"] + ".mp4"

        )

        final_video.write_videofile(

            str(outfile),

            fps=30,

            codec="libx264",

            audio_codec="aac"

        )

        final_video.close()

        clip.close()

        return str(outfile)

    # ==================================================
    # Background Music
    # ==================================================

    def add_background_music(self):

        music_file = Path(
            "assets/audio/background.mp3"
        )

        if not music_file.exists():

            self.logger.warning(
                "Background music not found."
            )

            return None

        try:

            return AudioFileClip(
                str(music_file)
            )

        except Exception as ex:

            self.logger.exception(ex)

            return None
            # ==================================================
    # Generate Thumbnail
    # ==================================================

    def generate_thumbnail(
            self,
            frame_files,
            metadata
    ):

        if not frame_files:

            return None

        thumbnail_path = self.thumbnail_folder / (
            metadata["FileName"] + ".jpg"
        )

        image = Image.open(frame_files[-1])

        image = image.resize(
            (1280, 720)
        )

        image.save(
            thumbnail_path,
            quality=95
        )

        self.logger.info(
            f"Thumbnail created : {thumbnail_path}"
        )

        return str(thumbnail_path)

    # ==================================================
    # Resize Frames for Shorts
    # ==================================================

    def resize_frame(
            self,
            frame_path
    ):

        image = Image.open(frame_path)

        image = image.resize(
            (
                1080,
                1080
            )
        )

        image.save(frame_path)

        return frame_path

    # ==================================================
    # Prepare Frames
    # ==================================================

    def prepare_frames(
            self,
            frame_files
    ):

        prepared = []

        for frame in frame_files:

            prepared.append(

                self.resize_frame(
                    frame
                )

            )

        return prepared

    # ==================================================
    # Add Intro Frame
    # ==================================================

    def create_intro_frame(
            self,
            metadata
    ):

        image = Image.new(
            "RGB",
            (
                1080,
                1080
            ),
            color=(30, 30, 30)
        )

        outfile = self.temp_folder / "intro.png"

        image.save(outfile)

        return str(outfile)

    # ==================================================
    # Add Outro Frame
    # ==================================================

    def create_outro_frame(
            self,
            metadata
    ):

        image = Image.new(
            "RGB",
            (
                1080,
                1080
            ),
            color=(15, 15, 15)
        )

        outfile = self.temp_folder / "outro.png"

        image.save(outfile)

        return str(outfile)

    # ==================================================
    # Build Final Frame List
    # ==================================================

    def build_frame_sequence(
            self,
            frame_files,
            metadata
    ):

        frames = []

        intro = self.create_intro_frame(
            metadata
        )

        frames.append(intro)

        frames.extend(

            self.prepare_frames(
                frame_files
            )

        )

        outro = self.create_outro_frame(
            metadata
        )

        frames.append(outro)

        return frames

    # ==================================================
    # Last Move Highlight
    # ==================================================

    def get_last_move(self, game):

        board = game.board()

        last_move = None

        for move in game.mainline_moves():

            board.push(move)

            last_move = move

        return last_move
        # ==================================================
    # Cleanup Resources
    # ==================================================

    def cleanup(self):

        try:

            if self.temp_folder.exists():

                shutil.rmtree(
                    self.temp_folder
                )

                self.logger.info(
                    "Temporary frames deleted."
                )

        except Exception as ex:

            self.logger.exception(ex)

    # ==================================================
    # Video Information
    # ==================================================

    def get_video_information(
            self,
            metadata,
            frame_count
    ):

        fps = 30

        duration = frame_count

        return {

            "width": 1080,

            "height": 1920,

            "fps": fps,

            "frames": frame_count,

            "duration": duration,

            "opening": metadata.get(
                "OpeningDisplay",
                ""
            ),

            "players":

                f'{metadata.get("White","")} vs '

                f'{metadata.get("Black","")}',

            "result": metadata.get(
                "Result",
                ""
            )

        }

    # ==================================================
    # Validate Frame List
    # ==================================================

    def validate_frames(
            self,
            frame_files
    ):

        valid = []

        for frame in frame_files:

            if os.path.exists(frame):

                valid.append(frame)

            else:

                self.logger.warning(

                    f"Missing frame : {frame}"

                )

        return valid

    # ==================================================
    # Export Statistics
    # ==================================================

    def export_statistics(
            self,
            metadata,
            frame_files
    ):

        info = self.get_video_information(

            metadata,

            len(frame_files)

        )

        self.logger.info("=" * 60)

        self.logger.info("Video Information")

        self.logger.info("=" * 60)

        for key, value in info.items():

            self.logger.info(

                f"{key:<15} : {value}"

            )

        self.logger.info("=" * 60)

    # ==================================================
    # Future Hooks
    # ==================================================

    def add_engine_bar(
            self,
            clip
    ):

        return clip

    def add_move_arrows(
            self,
            clip
    ):

        return clip

    def add_logo(
            self,
            clip
    ):

        return clip

    def add_watermark(
            self,
            clip
    ):

        return clip

    def add_subtitles(
            self,
            clip
    ):

        return clip

    # ==================================================
    # Final Render Wrapper
    # ==================================================

    def render(
            self,
            game,
            metadata
    ):

        self.clear_frames()

        board = game.board()

        frame_files = []

        frame_files.append(

            self.create_board_frame(

                board,

                0

            )

        )

        move_number = 1

        for move in game.mainline_moves():

            board.push(move)

            frame_files.append(

                self.create_board_frame(

                    board,

                    move_number

                )

            )

            move_number += 1

        frame_files = self.validate_frames(

            frame_files

        )

        frame_files = self.build_frame_sequence(

            frame_files,

            metadata

        )

        video = self.create_video(

            frame_files,

            metadata

        )

        thumbnail = self.generate_thumbnail(

            frame_files,

            metadata

        )

        self.export_statistics(

            metadata,

            frame_files

        )

        self.cleanup()

        return {

            "video": video,

            "thumbnail": thumbnail

        }