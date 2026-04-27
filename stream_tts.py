"""Stream TTS audio from pocket-tts.caronboulme.fr.

Usage:
  python3 stream_tts.py "Bonjour." -o out.wav   # save to file
  python3 stream_tts.py "Bonjour." | ffplay -    # pipe to player
"""

import argparse
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

BASE_URL = "https://pocket-tts.caronboulme.fr"
API_KEY = os.environ["POCKET_TTS_API_KEY"]
VOICES_DIR = Path("/home/francois/workspace/Voix")
DEFAULT_VOICE = VOICES_DIR / "FIP3.mp3"


def stream_tts(text: str, output_path: str | None, voice_path: Path) -> None:
    headers = {"X-API-Key": API_KEY}
    data = {"text": text}

    print(f"Voice: {voice_path.name}", file=sys.stderr)
    print(f"Generating: {text!r}", file=sys.stderr)

    out = sys.stdout.buffer if output_path is None else None

    with voice_path.open("rb") as voice_file:
        files = {"voice_wav": (voice_path.name, voice_file, "audio/mpeg")}
        with requests.post(
            f"{BASE_URL}/tts",
            data=data,
            files=files,
            headers=headers,
            stream=True,
            timeout=120,
        ) as response:
            if not response.ok:
                print(f"Error {response.status_code}: {response.text[:500]}", file=sys.stderr)
                sys.exit(1)

            total = 0
            with (open(output_path, "wb") if out is None else out) as f:
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
                        if out is None:
                            print(f"\r  {total / 1024:.1f} KB received", end="", file=sys.stderr)

    if out is None:
        print(f"\nSaved to {output_path} ({total / 1024:.1f} KB)", file=sys.stderr)


def resolve_voice(voice_arg: str | None) -> Path:
    if voice_arg is None:
        return DEFAULT_VOICE

    p = Path(voice_arg)
    if p.exists():
        return p

    # Try as a name in VOICES_DIR
    for candidate in VOICES_DIR.iterdir():
        if candidate.stem.lower() == voice_arg.lower():
            return candidate

    print(f"Voice not found: {voice_arg!r}", file=sys.stderr)
    print(f"Available: {', '.join(p.name for p in sorted(VOICES_DIR.iterdir()))}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stream TTS audio from pocket-tts server")
    parser.add_argument("text", help="Text to synthesize")
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output WAV file. If omitted, writes to stdout for piping (e.g. | ffplay -).",
    )
    parser.add_argument(
        "--voice",
        help=(
            f"Voice file path or name from {VOICES_DIR}. "
            f"Available: {', '.join(p.name for p in sorted(VOICES_DIR.iterdir()))}. "
            f"Default: {DEFAULT_VOICE.name}"
        ),
    )
    args = parser.parse_args()

    voice_path = resolve_voice(args.voice)
    stream_tts(args.text, args.output, voice_path)


if __name__ == "__main__":
    main()
