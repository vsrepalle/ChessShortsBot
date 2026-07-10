import os

from PIL import Image

from moviepy.editor import (
    ImageClip,
    CompositeVideoClip,
    TextClip,
    AudioFileClip
)


WIDTH = 1080
HEIGHT = 1920


class BrochureRenderer:

    def __init__(self):

        self.footer = "Online Chess Classes | WhatsApp : 9390626564"

    ############################################################

    def render(
        self,
        brochure_image,
        info,
        output_video
    ):

        duration = 20

        background = ImageClip(
            brochure_image
        )

        background = background.resize(
            width=WIDTH
        )

        background = background.set_duration(
            duration
        )

        # Slow Zoom

        background = background.resize(
            lambda t: 1 + (0.15 * t / duration)
        )

        ########################################################

        title = TextClip(

            info["tournament_name"],

            fontsize=70,

            color="white",

            font="Arial-Bold",

            method="caption",

            size=(1000, None)

        )

        title = title.set_duration(duration)

        title = title.set_position(
            ("center", 40)
        )

        ########################################################

        details = f"""

Venue
{info["venue"]}

Dates
{' , '.join(info["dates"])}

Entry Fee
{info["entry_fee"]}

Prize
{info["prize_fund"]}

Contact

{' '.join(info["contact"])}

"""

        detail_clip = TextClip(

            details,

            fontsize=48,

            color="yellow",

            bg_color="black",

            method="caption",

            size=(950, None)

        )

        detail_clip = detail_clip.set_duration(
            duration
        )

        detail_clip = detail_clip.set_position(
            ("center", 1200)
        )

        ########################################################

        footer = TextClip(

            self.footer,

            fontsize=40,

            color="white",

            bg_color="red",

            method="caption",

            size=(1080,60)

        )

        footer = footer.set_duration(duration)

        footer = footer.set_position(
            ("center",1850)
        )

        ########################################################

        clips = [

            background,

            title,

            detail_clip,

            footer

        ]

        video = CompositeVideoClip(

            clips,

            size=(WIDTH,HEIGHT)

        )

        ########################################################

        if os.path.exists(
            "assets/background_music.mp3"
        ):

            audio = AudioFileClip(

                "assets/background_music.mp3"

            ).set_duration(duration)

            video = video.set_audio(audio)

        ########################################################

        video.write_videofile(

            output_video,

            fps=30,

            codec="libx264",

            audio_codec="aac"

        )

        return output_video
