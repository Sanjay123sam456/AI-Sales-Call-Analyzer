from pathlib import Path

from backend.utils.file_utils import load_json


def format_time(seconds: float) -> str:
    """
    Convert seconds to MM:SS format.
    """

    minutes = int(seconds // 60)
    secs = int(seconds % 60)

    return f"{minutes:02}:{secs:02}"


def extract_conversation(json_path: Path):
    """
    Convert Deepgram word-level transcript
    into speaker-wise conversation with timestamps.
    """

    data = load_json(json_path)

    words = data["results"]["channels"][0]["alternatives"][0]["words"]

    conversation = []

    current_speaker = None
    current_sentence = []

    start_time = None
    end_time = None

    for word in words:

        speaker = word["speaker"]
        text = word["punctuated_word"]

        if current_speaker is None:
            current_speaker = speaker
            start_time = word["start"]

        if speaker != current_speaker:

            conversation.append(
                (
                    format_time(start_time),
                    format_time(end_time),
                    current_speaker,
                    " ".join(current_sentence),
                )
            )

            current_sentence = []
            current_speaker = speaker
            start_time = word["start"]

        current_sentence.append(text)
        end_time = word["end"]

    if current_sentence:

        conversation.append(
            (
                format_time(start_time),
                format_time(end_time),
                current_speaker,
                " ".join(current_sentence),
            )
        )

    return conversation