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


def _do_request(data: dict, files: dict | None, output_path: str | None) -> None:
    headers = {"X-API-Key": API_KEY}
    out = sys.stdout.buffer if output_path is None else None

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


def stream_tts(text: str, output_path: str | None, voice_arg: str | None) -> None:
    print(f"Generating: {text!r}", file=sys.stderr)

    # Check if it's a stored server-side voice name
    if voice_arg is not None and not Path(voice_arg).exists():
        # Not a local file — check if it's stored on the server
        r = requests.get(f"{BASE_URL}/voices", headers={"X-API-Key": API_KEY}, timeout=10)
        if r.ok and voice_arg in r.json().get("voices", []):
            print(f"Voice: {voice_arg} (server-stored)", file=sys.stderr)
            _do_request({"text": text, "voice_url": voice_arg}, None, output_path)
            return

    # Resolve to a local file and upload it
    voice_path = _resolve_local_voice(voice_arg)
    print(f"Voice: {voice_path.name}", file=sys.stderr)
    with voice_path.open("rb") as voice_file:
        _do_request(
            {"text": text},
            {"voice_wav": (voice_path.name, voice_file, "audio/mpeg")},
            output_path,
        )


def _resolve_local_voice(voice_arg: str | None) -> Path:
    if voice_arg is None:
        return DEFAULT_VOICE

    p = Path(voice_arg)
    if p.exists():
        return p

    for candidate in VOICES_DIR.iterdir():
        if candidate.stem.lower() == voice_arg.lower():
            return candidate

    print(f"Voice not found: {voice_arg!r}", file=sys.stderr)
    print(f"Local files: {', '.join(p.name for p in sorted(VOICES_DIR.iterdir()))}", file=sys.stderr)
    print(f"Use 'python3 upload_voice.py --list' to see server-stored voices.", file=sys.stderr)
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
            "Voice to use: a server-stored name (upload_voice.py), "
            f"a local file, or a name from {VOICES_DIR}. "
            f"Default: {DEFAULT_VOICE.name}."
        ),
    )
    args = parser.parse_args()

    stream_tts(args.text, args.output, args.voice)


if __name__ == "__main__":
    main()
