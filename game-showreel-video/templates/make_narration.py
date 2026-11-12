"""Showreel narration with a neural voice instead of the robotic SAPI one.

Reads narration.json and speaks every shot's line with edge-tts (Microsoft neural voices,
zh-CN-XiaoxiaoNeural by default), writes `<WORK_DIR>/audio/narration/<shot id>.wav`
(22.05 kHz mono 16 bit, what build.py measures and mixes). Needs the network: edge-tts
streams from the Azure speech endpoint, so a blocked network fails loudly here.

Run: `python3 <WORK_DIR>/make_narration.py [--voice zh-CN-YunxiNeural] [--rate +6%]`
(Windows: `py -3`).
"""

import argparse
import asyncio
import json
import subprocess
import sys
import wave
from pathlib import Path

import edge_tts
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent
NARRATION_DIR = ROOT / "audio" / "narration"
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
DEFAULT_RATE = "+6%"


def shots_with_narration() -> list[dict]:
    config = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))
    shots = []
    for chapter in config["chapters"]:
        for shot in chapter["shots"]:
            if (shot.get("narration") or "").strip():
                shots.append(shot)
    return shots


async def speak(text: str, voice: str, rate: str, mp3_path: Path) -> None:
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(str(mp3_path))


def to_wav(mp3_path: Path, wav_path: Path) -> float:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run(
        [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(mp3_path),
         "-ar", "22050", "-ac", "1", "-c:a", "pcm_s16le", str(wav_path)],
        check=True,
    )
    with wave.open(str(wav_path)) as handle:
        return handle.getnframes() / float(handle.getframerate())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--rate", default=DEFAULT_RATE)
    arguments = parser.parse_args()
    NARRATION_DIR.mkdir(parents=True, exist_ok=True)
    shots = shots_with_narration()
    total_seconds = 0.0
    for shot in shots:
        mp3_path = NARRATION_DIR / f"{shot['id']}.mp3"
        wav_path = NARRATION_DIR / f"{shot['id']}.wav"
        asyncio.run(speak(str(shot["narration"]), arguments.voice, arguments.rate, mp3_path))
        seconds = to_wav(mp3_path, wav_path)
        total_seconds += seconds
        print(f"NARRATION {shot['id']:<16} {seconds:5.2f}s  {shot['narration']}")
    print(f"NARRATION_DONE {len(shots)} lines {total_seconds:.1f}s voice={arguments.voice}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
