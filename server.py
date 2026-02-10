"""
İhsan's Gate — TTS Server (edge-tts + Flask)
Cloud-ready, free, high-quality American-accent Text-to-Speech.
"""

import asyncio
import io
import os
import traceback
from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
import edge_tts

app = Flask(__name__)
CORS(app)

LAST_ERROR = None

VOICES = {
    "andrew": {"id": "en-US-AndrewNeural", "name": "Andrew", "gender": "Male"},
    "ava":    {"id": "en-US-AvaNeural",    "name": "Ava",    "gender": "Female"},
    "brian":  {"id": "en-US-BrianNeural",  "name": "Brian",  "gender": "Male"},
    "emma":   {"id": "en-US-EmmaNeural",   "name": "Emma",   "gender": "Female"},
    "jenny":  {"id": "en-US-JennyNeural",  "name": "Jenny",  "gender": "Female"},
    "guy":    {"id": "en-US-GuyNeural",    "name": "Guy",    "gender": "Male"},
}

DEFAULT_VOICE = "andrew"


async def _generate_audio(text: str, voice_key: str):
    """Generate audio and return as bytes buffer."""
    voice_info = VOICES.get(voice_key or DEFAULT_VOICE, VOICES[DEFAULT_VOICE])
    voice_id = voice_info["id"]
    
    buffer = io.BytesIO()
    communicate = edge_tts.Communicate(text, voice_id)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    
    if buffer.tell() == 0:
        raise Exception("Audio generation produced 0 bytes.")
        
    buffer.seek(0)
    return buffer


def generate_audio_sync(text: str, voice_key: str):
    """Synchronous wrapper for async audio generation (gunicorn compatible)."""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_generate_audio(text, voice_key))
    finally:
        loop.close()


@app.route('/api/tts', methods=['GET', 'POST'])
def tts_endpoint():
    global LAST_ERROR
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

        audio_buffer = generate_audio_sync(text, voice)
        
        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=False
        )

    except Exception as e:
        LAST_ERROR = {
            "msg": str(e),
            "trace": traceback.format_exc()
        }
        print(f"[API Error] {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/tts/voices', methods=['GET'])
def voices_endpoint():
    return jsonify({
        "default": DEFAULT_VOICE,
        "voices": [{"key": k, **v} for k, v in VOICES.items()]
    })


@app.route('/api/health', methods=['GET'])
def health_endpoint():
    return jsonify({
        "status": "ok", 
        "engine": "edge-tts", 
        "last_error": LAST_ERROR
    })


@app.route('/')
def root():
    return jsonify({"service": "IhsansGate TTS", "status": "running"})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)
