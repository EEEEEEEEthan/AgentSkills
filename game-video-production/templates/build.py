"""narration.json -> timeline.json -> audio/master.wav。

用法（仓库根目录）：`py -3 .export/<slug>/build.py [timeline|audio|all]`

镜头长度 = 实测配音时长 + 句尾留白。声音是唯一的时钟：
不拉伸音频，时间不够就改分镜或台词。
"""

import json
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
FPS = 30
SAMPLE_RATE = 44100
NARRATION_DIR = ROOT / "audio" / "narration"
BGM_PATH = ROOT / "audio" / "bgm" / "bgm.wav"
VOICE_LEAD = 0.15          # 每句配音在镜头开始后多久进入
EXTRA_GAP = 0.45           # 对白之间的安全留白（叠加在 shot.gap 上）
MAX_SHOT_GAP = 0.25        # narration.json 里单条 gap 的上限，防止行间拖沓
BGM_UNDER_VOICE_GAIN = 0.12
BGM_ALONE_GAIN = 0.26
FADE_OUT_SECONDS = 2.0
PEAK_DBFS = -1.0


def load_config() -> dict:
    return json.loads((ROOT / "narration.json").read_text(encoding="utf-8"))


def wav_seconds(path: Path) -> float:
    with wave.open(str(path)) as handle:
        return handle.getnframes() / float(handle.getframerate())


def shot_seconds(shot: dict) -> float:
    if shot.get("narration"):
        path = NARRATION_DIR / f"{shot['id']}.wav"
        if not path.exists():
            raise SystemExit(f"缺少配音 WAV：{path}（先跑 make_narration.py）")
        gap = min(float(shot.get("gap", 0.0)), MAX_SHOT_GAP)
        return wav_seconds(path) + gap + EXTRA_GAP
    return float(shot.get("seconds", 2.0)) + EXTRA_GAP


def display_tag(shot: dict) -> str:
    """把「人名 · 头衔」统一成「头衔 · 人名」；旁白给固定标识。"""
    if shot.get("who") == "narrator":
        return "旁白"
    tag = (shot.get("tag") or "").strip()
    if " · " in tag:
        name, title = tag.split(" · ", 1)
        return f"{title} · {name}"
    return tag


def build_timeline() -> dict:
    config = load_config()
    cursor = 0
    shots = []
    for index, shot in enumerate(config["shots"], start=1):
        frames = max(1, int(round(shot_seconds(shot) * FPS)))
        shots.append(
            {
                "id": shot["id"],
                "caption": (shot.get("narration") or shot.get("caption") or ""),
                "tag": display_tag(shot),
                "who": shot.get("who", ""),
                "index": index,
                "start": cursor,
                "frames": frames,
            }
        )
        cursor += frames
    timeline = {"fps": FPS, "total_frames": cursor, "total_shots": len(shots), "shots": shots}
    (ROOT / "timeline.json").write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"TIMELINE total_frames={cursor} seconds={cursor / FPS:.1f}")
    for shot in shots:
        print(f"  {shot['id']:<12} {shot['frames'] / FPS:6.2f}s  start={shot['start']:6d}")
    return timeline


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path)) as handle:
        channels = handle.getnchannels()
        width = handle.getsampwidth()
        rate = handle.getframerate()
        raw = handle.readframes(handle.getnframes())
    if width != 2:
        raise SystemExit(f"只支持 16 bit PCM：{path}")
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)
    if rate != SAMPLE_RATE:
        count = max(1, int(round(samples.size * SAMPLE_RATE / float(rate))))
        samples = np.interp(
            np.linspace(0.0, samples.size - 1.0, count), np.arange(samples.size), samples
        ).astype(np.float32)
    return samples


def build_audio(timeline: dict) -> None:
    total = int(round(timeline["total_frames"] / FPS * SAMPLE_RATE))
    master = np.zeros(total, dtype=np.float32)
    voice_mask = np.zeros(total, dtype=bool)
    config = {shot["id"]: shot for shot in load_config()["shots"]}
    for shot in timeline["shots"]:
        if not (config[shot["id"]].get("narration") or "").strip():
            continue
        samples = read_wav(NARRATION_DIR / f"{shot['id']}.wav")
        start = int(round((shot["start"] / FPS + VOICE_LEAD) * SAMPLE_RATE))
        end = min(total, start + samples.size)
        master[start:end] += samples[: end - start]
        voice_mask[start:end] = True
    background = read_wav(BGM_PATH)
    if background.size == 0:
        raise SystemExit("BGM 是空的")
    repeats = int(np.ceil(total / background.size))
    background = np.tile(background, repeats)[:total].copy()
    gain = np.where(voice_mask, BGM_UNDER_VOICE_GAIN, BGM_ALONE_GAIN).astype(np.float32)
    fade = int(FADE_OUT_SECONDS * SAMPLE_RATE)
    if fade < total:
        gain[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)
    master += background * gain
    peak = float(np.max(np.abs(master)))
    master *= (10.0 ** (PEAK_DBFS / 20.0)) / peak
    out_path = ROOT / "audio" / "master.wav"
    with wave.open(str(out_path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(np.clip(master * 32767.0, -32768, 32767).astype("<i2").tobytes())
    print(f"AUDIO {out_path} samples={total} voice={voice_mask.sum() / SAMPLE_RATE:.1f}s")


def main(argv: list[str]) -> int:
    action = argv[1] if len(argv) > 1 else "all"
    timeline = build_timeline()
    if action in ("audio", "all"):
        build_audio(timeline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
