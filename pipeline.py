"""
pipeline.py

Full pipeline for a single audio file.
Accepts optional language override.

Usage:
  python pipeline.py data/audio/call_008.ogg
  python pipeline.py data/audio/call_008.ogg hi

From frontend:
  from pipeline import run_pipeline
  run_pipeline(audio_path, language="hi")
"""

import sys
import json
from pathlib import Path
import os

from dotenv import load_dotenv
from openai import OpenAI
from deepgram import DeepgramClient

from backend.utils.extract_metadata import extract_metadata, save_metadata
from backend.transcript.parser import extract_conversation
from backend.utils.file_utils import save_text, load_text
from backend.llm.prompt import SYSTEM_PROMPT

load_dotenv()

deepgram_client = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))

llm_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

RAW_DIR   = Path("data/raw_transcripts")
META_DIR  = Path("data/metadata")
TRANS_DIR = Path("data/transcripts")
EVAL_DIR  = Path("data/evaluations")

for d in [RAW_DIR, META_DIR, TRANS_DIR, EVAL_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Language map
LANGUAGE_MAP = {
    "Auto":     None,       # detect_language=True
    "English":  "en",
    "Hindi":    "hi",
    "Hinglish": "hi",       # Deepgram uses hi model for Hinglish
}


def run_pipeline(audio_path: Path, language: str = "Auto", status_callback=None) -> dict:
    """
    Full pipeline for one audio file.

    Args:
        audio_path: Path to .ogg/.mp3/.wav file
        language:   "Auto" | "English" | "Hindi" | "Hinglish"
        status_callback: optional function(str) for progress updates

    Returns:
        evaluation dict
    """
    audio_path = Path(audio_path)
    call_id    = audio_path.stem

    def log(msg):
        print(msg)
        if status_callback:
            status_callback(msg)

    log(f"\n{'='*50}\n Pipeline: {call_id}\n{'='*50}")

    # ── Step 1: Transcribe ────────────────────────────────────────────────────
    log("🎙️ Transcribing audio...")

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    lang_code = LANGUAGE_MAP.get(language)

    if lang_code:
        # User specified language
        response = deepgram_client.listen.v1.media.transcribe_file(
            request=audio_data,
            model="nova-3",
            language=lang_code,
            smart_format=True,
            diarize_model="latest",
        )
    else:
        # Auto-detect
        response = deepgram_client.listen.v1.media.transcribe_file(
            request=audio_data,
            model="nova-3",
            detect_language=True,
            smart_format=True,
            diarize_model="latest",
        )

    raw_path = RAW_DIR / f"{call_id}_raw.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(response.model_dump_json(indent=4))
    log("  ✅ Transcription done")

    # ── Step 2: Extract metadata ──────────────────────────────────────────────
    log("🔍 Identifying speakers...")

    metadata  = extract_metadata(raw_path, llm_client)
    meta_path = META_DIR / f"{call_id}_meta.json"
    save_metadata(meta_path, metadata)

    advisor_speaker = metadata["advisor_speaker"]
    advisor_name    = metadata["advisor_name"]
    customer_name   = metadata["customer_name"]

    log(f"  Advisor  → {advisor_name} (Speaker {advisor_speaker})")
    log(f"  Customer → {customer_name}")

    # ── Step 3: Build clean transcript ───────────────────────────────────────
    log("📝 Building transcript...")

    conversation = extract_conversation(raw_path)
    output = []

    for start, end, speaker_num, text in conversation:
        label = (
            f"Advisor ({advisor_name})"
            if speaker_num == advisor_speaker
            else f"Customer ({customer_name})"
        )
        output.extend([f"[{start} - {end}]", f"{label}:", text, ""])

    trans_path = TRANS_DIR / f"{call_id}.txt"
    save_text(trans_path, "\n".join(output))
    log("  ✅ Transcript saved")

    # ── Step 4: Evaluate ──────────────────────────────────────────────────────
    log("🤖 Evaluating with GPT...")

    transcript = load_text(trans_path)

    eval_response = llm_client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": transcript},
        ],
    )

    evaluation = json.loads(eval_response.choices[0].message.content)

    eval_path = EVAL_DIR / f"{call_id}.json"
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=4, ensure_ascii=False)

    log(f"  ✅ Score: {evaluation.get('overall_score', '?')}/10")

    return evaluation


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py data/audio/call_008.ogg [language]")
        print("Language options: Auto (default), English, Hindi, Hinglish")
        sys.exit(1)

    audio   = Path(sys.argv[1])
    lang    = sys.argv[2] if len(sys.argv) > 2 else "Auto"

    if not audio.exists():
        print(f"File not found: {audio}")
        sys.exit(1)

    run_pipeline(audio, language=lang)