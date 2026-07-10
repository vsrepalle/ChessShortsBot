        # Dynamic video generation from the actual brochure image
        import subprocess
        from pathlib import Path

        video_output = "output/videos/brochure_short.mp4"
        Path("output/videos").mkdir(parents=True, exist_ok=True)

        tournament = info.get("tournament_name", "Chess Tournament Alert")

        cmd = f"""ffmpeg -loop 1 -i "{brochure_path}" `
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,drawtext=text='{tournament}':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=300" `
  -c:v libx264 -t 8 -pix_fmt yuv420p "{video_output}" -y"""

        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ Video generated with brochure: {video_output}")

        return {{
            "video": video_output,
            "thumbnail": None,
            "metadata": {{"Title": tournament}}
        }}
