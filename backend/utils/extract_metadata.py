"""
extract_metadata.py

Automatically determines:
- Which Deepgram speaker number is the Advisor vs Customer
- Advisor name and Customer name (from conversation context)
- Detected language

Replaces the hardcoded call_config.py completely.
"""

import json
from pathlib import Path

from backend.utils.file_utils import load_json


def build_speaker_preview(words: list, max_turns: int = 10) -> str:
    """
    Convert first N speaker turns into readable text for GPT.
    """
    turns = []
    current_speaker = None
    current_words = []

    for word in words:
        speaker = word["speaker"]
        text = word["punctuated_word"]

        if current_speaker is None:
            current_speaker = speaker

        if speaker != current_speaker:
            turns.append(f"Speaker {current_speaker}: {' '.join(current_words)}")
            current_words = []
            current_speaker = speaker

            if len(turns) >= max_turns:
                break

        current_words.append(text)

    if current_words and len(turns) < max_turns:
        turns.append(f"Speaker {current_speaker}: {' '.join(current_words)}")

    return "\n".join(turns)


def extract_metadata(raw_json_path: Path, llm_client) -> dict:
    """
    Use GPT to extract call metadata from the raw Deepgram transcript.

    Returns:
    {
        "advisor_speaker": 0,
        "advisor_name": "Rahul",
        "customer_name": "Anita",
        "detected_language": "en"
    }
    """

    data = load_json(raw_json_path)

    # Extract words and detected language
    words = data["results"]["channels"][0]["alternatives"][0]["words"]

    # Deepgram returns detected language when detect_language=True
    detected_language = (
        data.get("results", {})
        .get("channels", [{}])[0]
        .get("detected_language", "en")
    )

    # Build a preview of first 10 speaker turns
    preview = build_speaker_preview(words, max_turns=10)

    prompt = f"""
You are analyzing the beginning of a sales call transcript.
Speaker numbers are assigned by a speech recognition system (0 or 1).

Here are the first few turns:

{preview}

Your job:
1. Identify which speaker number (0 or 1) is the ADVISOR (salesperson calling the customer).
   The advisor typically: introduces themselves, mentions a company, asks questions.
2. Extract the ADVISOR's first name if mentioned. If not found, use "Advisor".
3. Extract the CUSTOMER's first name if mentioned. If not found, use "Customer".

Return ONLY valid JSON, no markdown:
{{
    "advisor_speaker": 0,
    "advisor_name": "Rahul",
    "customer_name": "Anita"
}}
"""

    response = llm_client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )

    result = json.loads(response.choices[0].message.content)

    # Add detected language from Deepgram
    result["detected_language"] = detected_language

    return result


def save_metadata(meta_path: Path, metadata: dict) -> None:
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)
    print(f"✅ Metadata saved: {meta_path.name}")


def load_metadata(meta_path: Path) -> dict:
    """Load existing metadata or return safe defaults."""
    if meta_path.exists():
        return load_json(meta_path)
    return {
        "advisor_speaker": 0,
        "advisor_name": "Advisor",
        "customer_name": "Customer",
        "detected_language": "en",
    }