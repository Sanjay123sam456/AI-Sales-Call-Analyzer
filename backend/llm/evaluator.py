from pathlib import Path
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from backend.utils.file_utils import load_text
from backend.llm.prompt import SYSTEM_PROMPT

# ==========================================
# Load Environment
# ==========================================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

# ==========================================
# Paths
# ==========================================

TRANSCRIPT_DIR = Path("data/transcripts")
OUTPUT_DIR = Path("data/evaluations")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

transcript_files = sorted(TRANSCRIPT_DIR.glob("*.txt"))

print(f"\nFound {len(transcript_files)} transcripts\n")

# ==========================================
# Evaluate
# ==========================================

for transcript_file in transcript_files:

    print(f"Evaluating {transcript_file.name}...")

    transcript = load_text(transcript_file)

    response = client.chat.completions.create(

        model="openai/gpt-4.1-mini",

        temperature=0.2,

        response_format={
            "type": "json_object"
        },

        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": transcript
            }
        ]
    )

    result = response.choices[0].message.content

    output_file = OUTPUT_DIR / f"{transcript_file.stem}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            json.loads(result),
            f,
            indent=4,
            ensure_ascii=False
        )

    print(f"✅ Saved {output_file.name}")

print("\n🎉 All evaluations completed!")