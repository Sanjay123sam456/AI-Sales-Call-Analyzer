"""
transcribe.py

Sends audio files to Deepgram Nova-3.
- Auto-detects language (English, Hindi, Hinglish)
- Auto-detects speakers via diarization
- No hardcoded language or call_config dependency
"""

from pathlib import Path
import os

from dotenv import load_dotenv
from deepgram import DeepgramClient

load_dotenv()

client = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))

AUDIO_DIR = Path("data/audio")
RAW_DIR   = Path("data/raw_transcripts")

RAW_DIR.mkdir(parents=True, exist_ok=True)


def transcribe_audio(audio_path: Path) -> Path:
    """
    Transcribe a single audio file.
    Returns path to the saved raw JSON.
    """
    call_id = audio_path.stem

    print(f"Transcribing {audio_path.name}...")

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    response = client.listen.v1.media.transcribe_file(
        request=audio_data,
        model="nova-3",
        detect_language=True,   # auto-detects Hindi / English / Hinglish
        smart_format=True,
        diarize_model="latest",
    )

    output_path = RAW_DIR / f"{call_id}_raw.json"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response.model_dump_json(indent=4))

    print(f"Saved {output_path.name}")
    return output_path


if __name__ == "__main__":
    audio_files = sorted(AUDIO_DIR.glob("*.ogg"))
    print(f"\nFound {len(audio_files)} audio files\n")
    for audio_file in audio_files:
        transcribe_audio(audio_file)
    print("\nAll files transcribed!")