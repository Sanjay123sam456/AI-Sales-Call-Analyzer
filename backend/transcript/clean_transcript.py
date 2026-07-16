"""
clean_transcript.py

Converts raw Deepgram JSON into clean readable transcripts.
- Reads advisor/customer names from call_XXX_meta.json
- No dependency on call_config.py
"""

from pathlib import Path
import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from backend.transcript.parser import extract_conversation
from backend.utils.extract_metadata import extract_metadata, save_metadata, load_metadata
from backend.utils.file_utils import save_text

load_dotenv()

llm_client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

RAW_DIR    = Path("data/raw_transcripts")
OUTPUT_DIR = Path("data/transcripts")
META_DIR   = Path("data/metadata")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)


def clean_single(call_id: str) -> Path:
    """
    Process one call: extract metadata + build clean transcript.
    Returns path to saved transcript.
    """
    raw_path  = RAW_DIR  / f"{call_id}_raw.json"
    meta_path = META_DIR / f"{call_id}_meta.json"
    out_path  = OUTPUT_DIR / f"{call_id}.txt"

    # Extract or load metadata
    if not meta_path.exists():
        print(f"  Extracting metadata for {call_id}...")
        metadata = extract_metadata(raw_path, llm_client)
        save_metadata(meta_path, metadata)
    else:
        metadata = load_metadata(meta_path)

    advisor_speaker = metadata["advisor_speaker"]   # 0 or 1
    advisor_name    = metadata["advisor_name"]
    customer_name   = metadata["customer_name"]

    print(f"  Advisor = Speaker {advisor_speaker} ({advisor_name})")
    print(f"  Customer = Speaker {1 - advisor_speaker} ({customer_name})")

    # Parse conversation from raw JSON
    conversation = extract_conversation(raw_path)

    # Build clean transcript
    output = []
    for start, end, speaker_num, text in conversation:
        if speaker_num == advisor_speaker:
            label = f"Advisor ({advisor_name})"
        else:
            label = f"Customer ({customer_name})"

        output.append(f"[{start} - {end}]")
        output.append(f"{label}:")
        output.append(text)
        output.append("")

    save_text(out_path, "\n".join(output))
    print(f"  Saved {out_path.name}")
    return out_path


if __name__ == "__main__":
    json_files = sorted(RAW_DIR.glob("*_raw.json"))
    print(f"\nFound {len(json_files)} raw transcripts\n")

    for json_file in json_files:
        call_id = json_file.stem.replace("_raw", "")
        print(f"Processing {call_id}...")
        clean_single(call_id)

    print("\nAll transcripts cleaned!")