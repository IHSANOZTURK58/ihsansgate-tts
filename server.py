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

app = FastAPI()

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

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
