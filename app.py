import os
import tempfile
import whisper
import streamlit as st
import google.generativeai as genai
from moviepy.editor import VideoFileClip
from dotenv import load_dotenv

# -------------------
# 🔐 Load Gemini API
# -------------------
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = genai.GenerativeModel("gemini-2.5-flash")

# Add ffmpeg to PATH for MoviePy
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"

# -------------------
# 📄 Page setup
# -------------------
st.set_page_config(page_title="🎙️ Assistly Chatbot", layout="wide")

# -------------------
# 💬 Chat bubble styling only
# -------------------
st.markdown("""
    <style>
    .chat-bubble-user {
        background-color: #1c1f26;
        color: white;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 5px;
        max-width: 70%;
        margin-left: auto;
    }
    .chat-bubble-assistant {
        background-color: #252a34;
        color: #f1f1f1;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 5px;
        max-width: 70%;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------
# 🧠 Title
# -------------------
st.markdown("<h1 style='text-align: center;'>🎤 Assistly - Audio/Video Q&A Chatbot</h1>", unsafe_allow_html=True)

# -------------------
# 💾 Initialize session
# -------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------
# 📁 Upload section
# -------------------
with st.sidebar:
    st.header("📁 Upload")
    uploaded = st.file_uploader("Upload audio/video", type=["mp3", "wav", "mp4", "mov", "mkv"])

    if uploaded:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded.name)[1])
        tmp.write(uploaded.getvalue())
        path = tmp.name

        if path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
            st.info("🎬 Extracting audio from video...")
            clip = VideoFileClip(path)
            audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            clip.audio.write_audiofile(audio_path)
        else:
            audio_path = path

        st.audio(audio_path)
        st.info("🔍 Transcribing with Whisper...")
        text = whisper.load_model("base").transcribe(audio_path)["text"]
        st.session_state.transcript = text
        st.success("✅ Transcription complete!")

# -------------------
# 💬 Chat display
# -------------------
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    bubble_class = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-assistant"
    st.markdown(f"<div class='{bubble_class}'>{msg['content']}</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# -------------------
# 💬 Chat input
# -------------------
if "transcript" in st.session_state:
    prompt = st.chat_input("Ask a question about the content:")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        full_prompt = f"""Please answer based on the transcript below:\n\nTranscript:\n\"\"\"\n{st.session_state.transcript}\n\"\"\"\n\nQuestion: {prompt}\nAnswer:"""
        response = MODEL.generate_content(full_prompt).text.strip()

        st.session_state.messages.append({"role": "assistant", "content": response})
