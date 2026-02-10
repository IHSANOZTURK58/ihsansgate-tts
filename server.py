"""
İhsan's Gate — TTS Server (gTTS Edition)
Cloud-ready, high-quality Google Text-to-Speech (Reliable & Robust).
"""

import io
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from gtts import gTTS

app = Flask(__name__)
CORS(app)

VOICES = {
    "andrew": "en",
    "ava":    "en",
    "brian":  "en",
    "emma":   "en",
    "jenny":  "en",
    "guy":    "en",
}

@app.route('/api/tts', methods=['GET', 'POST'])
def tts_endpoint():
    try:
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            text = data.get('text', '').strip()
            voice = data.get('voice', 'en').lower()
        else:
            text = request.args.get('text', '').strip()
            voice = request.args.get('voice', 'en').lower()

        if not text:
            return jsonify({"error": "Text is required."}), 400

        # Create gTTS object
        # Note: gTTS doesn't support specific neural voices by name like edge-tts,
        # so we use standard English 'en'. We can use 'tld' for different accents.
        tts = gTTS(text=text, lang='en', slow=False)
        
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=False
        )

    except Exception as e:
        print(f"[API Error] {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_endpoint():
    return jsonify({"status": "ok", "engine": "gTTS", "platform": "python-flask"})

@app.route('/')
def root():
    return jsonify({"service": "IhsansGate TTS (gTTS)", "status": "running"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=False)
