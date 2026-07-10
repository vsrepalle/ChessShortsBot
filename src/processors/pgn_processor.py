import os
import logging
from pathlib import Path

import chess.pgn

from src.renderers.pgn_renderer import PGNRenderer


class PGNProcessor:
    """
    Reads a PGN file, extracts metadata,
    renders a video, and prepares the
    information required for YouTube upload.
    """

    def __init__(self, config):

        self.config = config

        self.logger = logging.getLogger("ChessShortsBot")

        self.renderer = PGNRenderer(config)

    # ==========================================================
    # Main Entry Point
    # ==========================================================

    def process(self, file_path):

        self.logger.info("=" * 60)
        self.logger.info("PGN Processor Started")
        self.logger.info(file_path)
        self.logger.info("=" * 60)

        game = self.load_game(file_path)

        if game is None:

            return None

        metadata = self.extract_metadata(game)

        render_result = self.renderer.render(

            game,

            metadata

        )

        return {

            "video": render_result["video"],

            "thumbnail": render_result.get("thumbnail"),

            "metadata": metadata

        }

    # ==========================================================
    # Load PGN
    # ==========================================================

    def load_game(self, file_path):

        if not os.path.exists(file_path):

            self.logger.error(

                f"PGN not found : {file_path}"

            )

            return None

        try:

            with open(

                file_path,

                "r",

                encoding="utf-8",

                errors="ignore"

            ) as fp:

                game = chess.pgn.read_game(fp)

            if game is None:

                self.logger.error(

                    "Invalid PGN."

                )

                return None

            return game

        except Exception as ex:

            self.logger.exception(ex)

            return None

    # ==========================================================
    # Extract Metadata
    # ==========================================================

    def extract_metadata(self, game):

        headers = game.headers

        metadata = {

            "White": headers.get(

                "White",

                "Unknown"

            ),

            "Black": headers.get(

                "Black",

                "Unknown"

            ),

            "Tournament": headers.get(

                "Event",

                ""

            ),

            "Site": headers.get(

                "Site",

                ""

            ),

            "Date": headers.get(

                "Date",

                ""

            ),

            "Round": headers.get(

                "Round",

                ""

            ),

            "Result": headers.get(

                "Result",

                ""

            ),

            "WhiteElo": headers.get(

                "WhiteElo",

                ""

            ),

            "BlackElo": headers.get(

                "BlackElo",

                ""

            ),

            "ECO": headers.get(

                "ECO",

                ""

            ),

            "Opening": headers.get(

                "Opening",

                ""

            ),

            "Variation": headers.get(

                "Variation",

                ""

            )

        }

        metadata["Moves"] = self.count_moves(game)

        metadata["FileName"] = ""

        return metadata

    # ==========================================================
    # Count Moves
    # ==========================================================

    def count_moves(self, game):

        board = game.board()

        count = 0

        for move in game.mainline_moves():

            board.push(move)

            count += 1

        return count
        # ==========================================================
    # Build Metadata
    # ==========================================================

    def build_metadata(self, game, metadata):

        board = game.board()

        moves = []

        for move in game.mainline_moves():

            san = board.san(move)

            moves.append(san)

            board.push(move)

        metadata["MovesSAN"] = moves

        metadata["MoveCount"] = len(moves)

        metadata["Winner"] = self.get_winner(
            metadata["Result"]
        )

        metadata["OpeningDisplay"] = self.get_opening_name(
            metadata
        )

        metadata["Title"] = self.build_title(
            metadata
        )

        return metadata

    # ==========================================================
    # Render Video
    # ==========================================================

    def render_video(self, game, metadata):

        self.logger.info(
            "Rendering video..."
        )

        return self.renderer.render(
            game,
            metadata
        )

    # ==========================================================
    # Generate Thumbnail
    # ==========================================================

    def generate_thumbnail(
            self,
            game,
            metadata
    ):

        if hasattr(
            self.renderer,
            "generate_thumbnail"
        ):

            return self.renderer.generate_thumbnail(
                game,
                metadata
            )

        return None

    # ==========================================================
    # Process PGN
    # ==========================================================

    def process(self, file_path):

        game = self.load_game(file_path)

        if game is None:

            return None

        metadata = self.extract_metadata(game)

        metadata["FileName"] = Path(
            file_path
        ).stem

        metadata = self.build_metadata(
            game,
            metadata
        )

        render = self.render_video(
            game,
            metadata
        )

        thumbnail = self.generate_thumbnail(
            game,
            metadata
        )

        result = {

            "video": render["video"],

            "thumbnail": thumbnail,

            "metadata": metadata

        }

        self.logger.info(
            "PGN Processing Completed."
        )

        return result
        # ==========================================================
    # Determine Winner
    # ==========================================================

    def get_winner(self, result):

        result = result.strip()

        if result == "1-0":
            return "White"

        if result == "0-1":
            return "Black"

        if result == "1/2-1/2":
            return "Draw"

        return "Unknown"

    # ==========================================================
    # Opening Display
    # ==========================================================

    def get_opening_name(self, metadata):

        opening = metadata.get("Opening", "").strip()

        variation = metadata.get("Variation", "").strip()

        if opening and variation:

            return f"{opening} : {variation}"

        if opening:

            return opening

        eco = metadata.get("ECO", "").strip()

        if eco:

            return f"Opening ({eco})"

        return "Unknown Opening"

    # ==========================================================
    # Build Video Title
    # ==========================================================

    def build_title(self, metadata):

        white = self.format_player_name(
            metadata["White"]
        )

        black = self.format_player_name(
            metadata["Black"]
        )

        opening = metadata["OpeningDisplay"]

        result = metadata["Result"]

        if opening != "Unknown Opening":

            return (
                f"{white} vs {black} | "
                f"{opening} | {result}"
            )

        return (
            f"{white} vs {black} | {result}"
        )

    # ==========================================================
    # Format Player Name
    # ==========================================================

    def format_player_name(self, name):

        name = name.strip()

        if "," in name:

            parts = name.split(",")

            return f"{parts[1].strip()} {parts[0].strip()}"

        return name

    # ==========================================================
    # Checkmate Detection
    # ==========================================================

    def is_checkmate(self, game):

        board = game.board()

        for move in game.mainline_moves():

            board.push(move)

        return board.is_checkmate()

    # ==========================================================
    # Stalemate Detection
    # ==========================================================

    def is_stalemate(self, game):

        board = game.board()

        for move in game.mainline_moves():

            board.push(move)

        return board.is_stalemate()

    # ==========================================================
    # Draw Detection
    # ==========================================================

    def is_draw(self, game):

        board = game.board()

        for move in game.mainline_moves():

            board.push(move)

        return board.is_game_over() and board.result() == "1/2-1/2"

    # ==========================================================
    # Game Summary
    # ==========================================================

    def build_summary(self, game, metadata):

        summary = {

            "Winner": metadata["Winner"],

            "Moves": metadata["MoveCount"],

            "Opening": metadata["OpeningDisplay"],

            "Checkmate": self.is_checkmate(game),

            "Draw": self.is_draw(game),

            "Stalemate": self.is_stalemate(game)

        }

        return summary

    # ==========================================================
    # Log Metadata
    # ==========================================================

    def log_metadata(self, metadata):

        self.logger.info("=" * 60)

        self.logger.info("PGN Metadata")

        self.logger.info("=" * 60)

        for key, value in metadata.items():

            self.logger.info(
                f"{key:<20} : {value}"
            )

        self.logger.info("=" * 60)
            # ==========================================================
    # Save Metadata JSON
    # ==========================================================

    def save_metadata(self, metadata):

        metadata_folder = Path("output/metadata")

        metadata_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = (
            metadata.get("FileName", "game")
            + ".json"
        )

        outfile = metadata_folder / filename

        import json

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

    # ==========================================================
    # Validate Metadata
    # ==========================================================

    def validate_metadata(self, metadata):

        required = [

            "White",
            "Black",
            "Result"

        ]

        missing = []

        for field in required:

            if not metadata.get(field):

                missing.append(field)

        if missing:

            self.logger.warning(

                "Missing metadata : "

                + ", ".join(missing)

            )

        return len(missing) == 0

    # ==========================================================
    # Build Statistics
    # ==========================================================

    def build_statistics(self, metadata):

        statistics = {

            "Players":

                f'{metadata["White"]} vs {metadata["Black"]}',

            "Opening":

                metadata["OpeningDisplay"],

            "Winner":

                metadata["Winner"],

            "Moves":

                metadata["MoveCount"],

            "Result":

                metadata["Result"]

        }

        return statistics

    # ==========================================================
    # Log Statistics
    # ==========================================================

    def log_statistics(self, statistics):

        self.logger.info("=" * 60)

        self.logger.info("Game Statistics")

        self.logger.info("=" * 60)

        for key, value in statistics.items():

            self.logger.info(

                f"{key:<20} : {value}"

            )

        self.logger.info("=" * 60)

    # ==========================================================
    # Finalize Result
    # ==========================================================

    def finalize_result(

            self,

            result

    ):

        metadata = result["metadata"]

        self.validate_metadata(

            metadata

        )

        self.save_metadata(

            metadata

        )

        stats = self.build_statistics(

            metadata

        )

        self.log_statistics(

            stats

        )

        return result

    # ==========================================================
    # Process With Finalization
    # ==========================================================

    def process(self, file_path):

        game = self.load_game(file_path)

        if game is None:

            return None

        metadata = self.extract_metadata(game)

        metadata["FileName"] = Path(
            file_path
        ).stem

        metadata = self.build_metadata(
            game,
            metadata
        )

        render_result = self.render_video(
            game,
            metadata
        )

        thumbnail = self.generate_thumbnail(
            game,
            metadata
        )

        result = {

            "video": render_result["video"],

            "thumbnail": thumbnail,

            "metadata": metadata

        }

        self.logger.info(
            "PGN processing completed."
        )

        return self.finalize_result(
            result
        )