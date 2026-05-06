from google import genai
from google.genai import types
import os

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SUPPORTED_AUDIO_TYPES = {
    "audio/mpeg": "audio/mpeg",     # .mp3
    "audio/mp3": "audio/mpeg",
    "audio/wav": "audio/wav",       # .wav
    "audio/x-wav": "audio/wav",
    "audio/mp4": "audio/mp4",       # .m4a
    "audio/x-m4a": "audio/mp4",     # .m4a (Windows / Chrome)
}


def transcribe_audio(file_bytes: bytes, content_type: str) -> str:
    """
    Transcribe audio bytes using Gemini 2.5 flash lite model.
    """

    if content_type not in SUPPORTED_AUDIO_TYPES:
        raise ValueError(f"Unsupported audio type: {content_type}")

    audio_part = types.Part.from_bytes(
        data=file_bytes,
        mime_type=SUPPORTED_AUDIO_TYPES[content_type]
    )

    response = client.models.generate_content(
    model="models/gemini-2.5-flash-native-audio-latest",
    contents=[
        "Transcribe this classroom lecture audio clearly into text.",
        audio_part
    ]
)



    return response.text.strip()
