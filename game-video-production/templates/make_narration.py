"""用豆包语音合成 2.0（双向流式 WebSocket）逐句生成配音。

用法（仓库根目录）：
    $env:DOUBAO_API_KEY = "..."
    py -3 .export/<slug>/make_narration.py [--force] [--only id1,id2]

- 每句先写 audio/tmp/<id>.mp3，再解码成 22.05 kHz 单声道 wav。
- 按台词文本哈希缓存：文本没变就跳过；只有改动过的句子会重新合成。
- 合成后不做任何变速/拉伸，镜头的时长由 build.py 按真实语音反推。
"""

import argparse
import asyncio
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
import wave
from pathlib import Path

import imageio_ffmpeg
import websockets

ROOT = Path(__file__).resolve().parent
AUDIO_DIR = ROOT / "audio" / "narration"
TMP_DIR = ROOT / "audio" / "tmp"
HASH_PATH = ROOT / "audio" / "narration.hash.json"
URL = "wss://openspeech.bytedance.com/api/v3/tts/bidirection"
RESOURCE = "seed-tts-2.0"
DEFAULT_SPEAKER = "zh_male_yunzhou_uranus_bigtts"

# protocols.py 从豆包官方 demo 复制到 .export/<slug>/tts/
sys.path.insert(0, str(Path(__file__).resolve().parent / "tts"))
from protocols import (  # noqa: E402
    EventType, MsgType, finish_connection, finish_session, receive_message,
    start_connection, start_session, task_request, wait_for_event,
)


async def synth_sentence(text: str, speaker: str, speech_rate: int) -> bytes:
    key = os.environ.get("DOUBAO_API_KEY")
    if not key:
        raise SystemExit("缺少环境变量 DOUBAO_API_KEY")
    headers = {
        "X-Api-Key": key,
        "X-Api-Resource-Id": RESOURCE,
        "X-Api-Connect-Id": str(uuid.uuid4()),
    }
    ws = await websockets.connect(URL, additional_headers=headers, max_size=20 * 1024 * 1024)
    try:
        await start_connection(ws)
        await wait_for_event(ws, MsgType.FullServerResponse, EventType.ConnectionStarted)
        base = {"req_params": {"speaker": speaker, "speech_rate": speech_rate,
                              "audio_params": {"format": "mp3", "sample_rate": 24000}}}
        request = copy.deepcopy(base)
        request["event"] = EventType.StartSession
        session_id = str(uuid.uuid4())
        await start_session(ws, json.dumps(request).encode(), session_id)
        await wait_for_event(ws, MsgType.FullServerResponse, EventType.SessionStarted)
        request = copy.deepcopy(base)
        request["event"] = EventType.TaskRequest
        request["req_params"]["text"] = text
        await task_request(ws, json.dumps(request).encode(), session_id)
        await finish_session(ws, session_id)
        audio = bytearray()
        while True:
            message = await receive_message(ws)
            if message.type == MsgType.FullServerResponse and message.event == EventType.SessionFinished:
                break
            if message.type == MsgType.AudioOnlyServer:
                audio.extend(message.payload)
        await finish_connection(ws)
        await wait_for_event(ws, MsgType.FullServerResponse, EventType.ConnectionFinished)
        return bytes(audio)
    finally:
        await ws.close()


def to_wav(mp3_path: Path, wav_path: Path) -> float:
    subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(mp3_path), "-ar", "22050", "-ac", "1", "-c:a", "pcm_s16le", str(wav_path)],
        check=True,
    )
    with wave.open(str(wav_path)) as handle:
        return handle.getnframes() / float(handle.getframerate())


def text_hash(text: str, speaker: str) -> str:
    return hashlib.sha256(f"{speaker}\n{text}".encode("utf-8")).hexdigest()


def main() -> int:
    config = json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--speaker", default=config.get("speaker", DEFAULT_SPEAKER))
    parser.add_argument("--speech-rate", type=int, default=int(config.get("speech_rate", 0)))
    parser.add_argument("--force", action="store_true", help="全部重新合成")
    parser.add_argument("--only", default="", help="只处理这些 id，逗号分隔")
    args = parser.parse_args()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    hashes = json.loads(HASH_PATH.read_text(encoding="utf-8")) if HASH_PATH.exists() else {}
    only = {item.strip() for item in args.only.split(",") if item.strip()}
    total = 0.0
    missing = []
    for shot in config["shots"]:
        text = (shot.get("narration") or "").strip()
        if not text:
            continue
        if only and shot["id"] not in only:
            continue
        speaker = shot.get("speaker") or args.speaker
        digest = text_hash(text, speaker)
        wav_path = AUDIO_DIR / f"{shot['id']}.wav"
        mp3_path = TMP_DIR / f"{shot['id']}.mp3"
        if not args.force and hashes.get(shot["id"]) == digest and wav_path.exists():
            with wave.open(str(wav_path)) as handle:
                seconds = handle.getnframes() / float(handle.getframerate())
            total += seconds
            print(f"SKIP  {shot['id']:<12} {seconds:5.2f}s  {text}")
            continue
        audio = None
        for attempt in range(3):
            try:
                async with asyncio.timeout(75):
                    audio = asyncio.run(synth_sentence(text, speaker, args.speech_rate))
                if audio:
                    break
            except Exception as error:  # noqa: BLE001
                print(f"RETRY {shot['id']} {attempt + 1}: {error}")
                time.sleep(1)
        if not audio:
            missing.append(shot["id"])
            print(f"FAIL  {shot['id']}  {text}")
            continue
        mp3_path.write_bytes(audio)
        seconds = to_wav(mp3_path, wav_path)
        hashes[shot["id"]] = digest
        total += seconds
        print(f"VOICE {shot['id']:<12} {seconds:5.2f}s  {text}")
    HASH_PATH.write_text(json.dumps(hashes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"NARRATION_DONE speech={total:.1f}s missing={missing}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
