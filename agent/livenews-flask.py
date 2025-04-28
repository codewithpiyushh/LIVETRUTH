from flask import Flask, request, jsonify
import subprocess
import numpy as np
import yt_dlp
from faster_whisper import WhisperModel
import time
import os
import json
import google.generativeai as genai
from flask_cors import CORS
from meta_ai_api import MetaAI
import re
import google.generativeai as genai

ai = MetaAI()
# ========== Setup ==========
app = Flask(__name__)
os.makedirs("agent/summaries", exist_ok=True)
CORS(app)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Replace with your actual Gemini API key
# genai.configure(api_key=GEMINI_API_KEY)
# model = genai.GenerativeModel("gemini-2.0-flash")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

whisper_model = WhisperModel("base.en", device="cpu", compute_type="int8")



def clean_text(text):
    # Remove Unicode superscript digits (¹ = \u00b9, ² = \u00b2, ..., ⁹ = \u2079)
    text = re.sub(r'[\u00b9\u00b2\u00b3\u2070-\u2079]+', '', text)
    # Optionally normalize spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_audio_url(youtube_url):
    print("[INFO] Extracting audio stream URL from YouTube link...")
    ydl_opts = {
        'quiet': True,
        'format': 'bestaudio/best',
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        for f in info['formats']:
            if 'acodec' in f and f['acodec'] != 'none':
                print("[INFO] Audio stream URL obtained.")
                return f['url'], info.get('is_live', False)
    return None, False


def extract_summary(text):
    print("[INFO] Sending segment to Gemini for summarization...")
    if not text.strip():
        return "No meaningful speech detected."
    
    promptmeta = f"Summarize this transcript in 50 words:\n\n{text}\n\nSummary:"
    try:
        response = model.generate_content(promptmeta)
        # response = ai.prompt(message=promptmeta)
        print("[DEBUG] Summary raw response:", response)
        
        # Return only the 'message' part if it exists
        if isinstance(response, dict) and "message" in response:
            return clean_text(response["message"])
        
        # Fallbacks
        if isinstance(response, dict):
            return response.get("text") or response.get("output") or str(response)
        elif hasattr(response, "text"):
            return response.text.strip()
        
        return str(response).strip()
        
    except Exception as e:
        return f"[Summary Error] {str(e)}"



def fact_check_summary(summary):
    print("[INFO] Sending summary to Gemini for fact-checking...")
    promptmeta1 = (
        f"Given the following claim:\n\n'{summary}'\n\n"
        "Search the web and report whether the claim is true, false, or uncertain. "
        "Provide reasoning in 2 lines."
    )
    try:
        response = model.generate_content(promptmeta1)
        # response = ai.prompt(message=promptmeta1)
        print("[DEBUG] Fact-Check raw response:", response)  # NEW LINE
        print("[DEBUG] Type of response:", type(response))

        if isinstance(response, dict) and "message" in response:
            return clean_text(response["message"])

        if isinstance(response, dict):
            return response.get("text") or response.get("output") or str(response)
        elif hasattr(response, "text"):
            return response.text
        return str(response)
    except Exception as e:
        return f"[Fact-Check Error] {str(e)}"




def live_news_processor(audio_url):
    print("[INFO] Starting ffmpeg to stream audio...")
    FFMPEG_CMD = [
        "ffmpeg", "-re", "-i", audio_url, "-vn",
        "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-f", "wav", "pipe:1"
    ]
    process = subprocess.Popen(FFMPEG_CMD, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    segment_duration = 30  # seconds
    sample_rate = 16000
    buffer_size = sample_rate * segment_duration * 2
    result_json = []
    segment_count = 0
    max_segments = 10

    while True:
        audio_buffer = process.stdout.read(buffer_size)
        if not audio_buffer:
            print("[INFO] No more audio data to process.")
            break

        audio_np = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
        if len(audio_np) > 0:
            print(f"\n[INFO] Transcribing segment #{segment_count + 1}...")
            segments, _ = whisper_model.transcribe(audio_np)
            segment_text = " ".join([seg.text.strip() for seg in segments])

            if segment_text:
                print(f"[INFO] Text extracted: {segment_text[:100]}...")
                summary = extract_summary(segment_text)
                verification = fact_check_summary(summary)
                # timestamp = time.strftime("%H:%M:%S", time.gmtime(segment_count * segment_duration))

                result = {
                    # "timestamp": timestamp,
                    "summary": summary,
                    "fact_check": verification
                }

                # print(f"\n⏱  [{timestamp}]")
                print(f"📝 Summary: {summary}")
                print(f"🔍 Fact Check: {verification}")

                return result  # Return one result per POST
            else:
                segment_count += 1
                if segment_count >= max_segments:
                    break

    return {"error": "No meaningful segment found in stream."}


def process_first_non_empty_segment(audio_url):
    segment_duration = 30
    sample_rate = 16000
    buffer_size = sample_rate * segment_duration * 2

    FFMPEG_CMD = [
        "ffmpeg", "-re", "-i", audio_url, "-vn",
        "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", "-f", "wav", "pipe:1"
    ]
    process = subprocess.Popen(FFMPEG_CMD, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    max_tries = 10
    for i in range(max_tries):
        audio_buffer = process.stdout.read(buffer_size)
        if not audio_buffer:
            break

        audio_np = np.frombuffer(audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
        if len(audio_np) == 0:
            continue

        segments, _ = whisper_model.transcribe(audio_np)
        segment_text = " ".join([seg.text.strip() for seg in segments])
        if segment_text.strip():
            summary = extract_summary(segment_text)
            fact_check = fact_check_summary(summary)
            # timestamp = time.strftime("%H:%M:%S", time.gmtime(i * segment_duration))

            return {
                # "timestamp": timestamp,
                "summary": summary,
                "fact_check": fact_check
            }

    return {"error": "No speech detected in the first 5 minutes."}


@app.route("/liveanalysis", methods=["POST"])
def index():
    data = request.get_json()
    youtube_url = data.get("url")

    if not youtube_url:
        return jsonify({"error": "Missing 'url' in request body"}), 400
    try:
        audio_url, is_live = get_audio_url(youtube_url)

        if not audio_url:
            return jsonify({"error": "Failed to extract audio."}), 500
        if is_live:
            print("[INFO] Detected live stream. Processing live audio...")
            result = live_news_processor(audio_url)
        else:
            print("[INFO] Detected normal video. Processing...")
            result = process_first_non_empty_segment(audio_url)

        print("========== COMPLETED ==========")
        print(json.dumps(result, indent=4))
        return json.dumps(result, indent=4)

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True, port = 5100)