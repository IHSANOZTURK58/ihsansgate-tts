"""
İhsan's Gate — TTS Server (edge-tts + Flask)
Cloud-ready, free, high-quality American-accent Text-to-Speech.
"""

import asyncio
import os
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import edge_tts

app = Flask(__name__)
CORS(app)

VOICES = {
    "andrew": {"id": "en-US-AndrewNeural", "name": "Andrew", "gender": "Male"},
    "ava":    {"id": "en-US-AvaNeural",    "name": "Ava",    "gender": "Female"},
    "brian":  {"id": "en-US-BrianNeural",  "name": "Brian",  "gender": "Male"},
    "emma":   {"id": "en-US-EmmaNeural",   "name": "Emma",   "gender": "Female"},
    "jenny":  {"id": "en-US-JennyNeural",  "name": "Jenny",  "gender": "Female"},
    "guy":    {"id": "en-US-GuyNeural",    "name": "Guy",    "gender": "Male"},
}

DEFAULT_VOICE = "andrew"

async def generate_speech(text: str, voice_key: str = None):
    voice_info = VOICES.get(voice_key or DEFAULT_VOICE, VOICES[DEFAULT_VOICE])
    voice_id = voice_info["id"]
    communicate = edge_tts.Communicate(text, voice_id)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            yield chunk["data"]

@app.route('/api/tts', methods=['GET', 'POST'])
def tts_endpoint():
    try:
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            text = data.get('text', '').strip()
            voice = data.get('voice', DEFAULT_VOICE).lower()
        else:
            text = request.args.get('text', '').strip()
            voice = request.args.get('voice', DEFAULT_VOICE).lower()

        if not text:
            return jsonify({"error": "Text is required."}), 400

        if len(text) > 2000:
            return jsonify({"error": "Text too long (max 2000 chars)."}), 400

        def stream_audio():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            gen = generate_speech(text, voice)
            try:
                while True:
                    try:
                        chunk = loop.run_until_complete(gen.__anext__())
                        yield chunk
                    except StopAsyncIteration:
                        break
            finally:
                loop.close()

        return Response(stream_audio(), mimetype='audio/mpeg')

    except Exception as e:
        print(f"[API Error] {e}")
        return jsonify({"error": "Server error."}), 500

@app.route('/api/tts/voices', methods=['GET'])
def voices_endpoint():
    return jsonify({
        "default": DEFAULT_VOICE,
        "voices": [{"key": k, **v} for k, v in VOICES.items()]
    })

@app.route('/api/health', methods=['GET'])
def health_endpoint():
    return jsonify({"status": "ok", "engine": "edge-tts", "platform": "python-flask"})

@app.route('/')
def root():
    return jsonify({"service": "IhsansGate TTS", "status": "running"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)
