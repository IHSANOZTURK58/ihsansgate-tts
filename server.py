"""
İhsan's Gate — High Quality TTS Server (FastAPI + edge-tts)
Provides neural voices like Andrew and Ava in the cloud.
"""

import os
import edge_tts
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import requests
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env file
load_dotenv()

app = FastAPI()

# --- CONFIG ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables.")


# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VOICES = {
    "andrew": "en-US-AndrewNeural",
    "ava":    "en-US-AvaNeural",
    "brian":  "en-US-BrianNeural",
    "emma":   "en-US-EmmaNeural",
    "jenny":  "en-US-JennyNeural",
    "guy":    "en-US-GuyNeural",
}

DEFAULT_VOICE = "en-US-AndrewNeural"

@app.get("/api/tts")
async def tts_endpoint(
    text: str = Query(..., min_length=1),
    voice: str = Query("andrew")
):
    try:
        voice_id = VOICES.get(voice.lower(), DEFAULT_VOICE)
        communicate = edge_tts.Communicate(text, voice_id)
        
        async def audio_generator():
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
                    
        return StreamingResponse(audio_generator(), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health():
    return {"status": "ok", "engine": "edge-tts", "version": "2.0.0-FastAPI"}

@app.get("/")
async def root():
    return {"service": "IhsansGate TTS (Neural)", "version": "2.0.0"}

class AIRequest(BaseModel):
    prompt: str
    model: str = "gemini-1.5-flash"

@app.post("/api/ai/generate")
async def gemini_proxy(request: AIRequest):
    try:
        api_key = GEMINI_API_KEY
        if not api_key:
             raise HTTPException(status_code=500, detail="Server API Key is missing")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{request.model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": request.prompt}]
            }]
        }
        
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        
        if response.status_code != 200:
             raise HTTPException(status_code=response.status_code, detail=f"Gemini API Error: {response.text}")
            
        return response.json()

    except Exception as e:
        print(f"[AI Proxy Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
