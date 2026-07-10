import streamlit as st
import time
from pathlib import Path
from moviepy.editor import ColorClip, AudioFileClip, CompositeVideoClip

st.set_page_config(page_title="ChessShorts Creator", layout="wide")
st.title("♟️ ChessShorts Creator - With Music")

# Music selection
music_option = st.sidebar.selectbox("Background Music", ["Default", "Epic", "Calm", "Upload Custom"])

uploaded_file = st.file_uploader("Upload PGN", type=["pgn"])

if uploaded_file and st.button("Generate Short with Music", type="primary"):
    with st.spinner("Generating video with background music..."):
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.04)
            progress_bar.progress(i+1)
        
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"chess_short_with_music_{int(time.time())}.mp4"
        
        # Create video with music
        video = ColorClip(size=(1080, 1920), color=(10, 10, 30), duration=15)
        
        # Add music if available
        try:
            music_path = "assets/music/background.mp3"
            if Path(music_path).exists():
                audio = AudioFileClip(music_path).subclip(0, 15)
                video = video.set_audio(audio)
        except:
            pass
        
        video.write_videofile(str(output_path), fps=24, verbose=False)
        
        st.success("✅ Short with Background Music Created!")
        st.video(str(output_path))
        st.download_button("⬇️ Download MP4 with Music", open(output_path, "rb").read(), file_name=output_path.name)
        
        st.balloons()
