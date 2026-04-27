"""Convert a voice audio file and upload it to the pocket-tts server.

Usage:
  python3 upload_voice.py /home/francois/workspace/Voix/FIP3.mp3 --name fip3
  python3 upload_voice.py calme.wav --name calme
  python3 upload_voice.py --list
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


def list_voices() -> None:
    r = requests.get(f"{BASE_URL}/voices", headers={"X-API-Key": API_KEY}, timeout=10)
    r.raise_for_status()
    voices = r.json()["voices"]
    if voices:
        print("Stored voices:")
        for v in voices:
            print(f"  - {v}")
    else:
        print("No stored voices yet.")


def upload_voice(audio_path: Path, name: str) -> None:
    print(f"Uploading '{audio_path.name}' as voice '{name}'...", file=sys.stderr)
    print("(The server converts the audio to a voice embedding — this takes ~10–30s)", file=sys.stderr)

    with audio_path.open("rb") as f:
        r = requests.post(
            f"{BASE_URL}/voices",
            data={"name": name},
            files={"voice_wav": (audio_path.name, f, "audio/mpeg")},
            headers={"X-API-Key": API_KEY},
            timeout=120,
        )

    if not r.ok:
        print(f"Error {r.status_code}: {r.text[:500]}", file=sys.stderr)
        sys.exit(1)

    print(f"Voice '{name}' stored. Use it with:", file=sys.stderr)
    print(f"  python3 stream_tts.py \"Bonjour.\" --voice {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload a voice to the pocket-tts server")
    parser.add_argument("audio", nargs="?", help="Audio file to convert (WAV, MP3, FLAC…)")
    parser.add_argument("--name", help="Name to give the stored voice")
    parser.add_argument("--list", action="store_true", help="List stored voices on the server")
    args = parser.parse_args()

    if args.list:
        list_voices()
        return

    if not args.audio:
        parser.error("Provide an audio file or use --list")

    audio_path = Path(args.audio)
    if not audio_path.exists():
        # Try in VOICES_DIR
        candidate = VOICES_DIR / args.audio
        if candidate.exists():
            audio_path = candidate
        else:
            print(f"File not found: {args.audio}", file=sys.stderr)
            sys.exit(1)

    name = args.name or audio_path.stem.lower()
    upload_voice(audio_path, name)


if __name__ == "__main__":
    main()
