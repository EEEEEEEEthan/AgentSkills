"""Showreel build helper: narration.json -> timeline.json -> audio/master.wav.

Run from the repository root with `python3 <WORK_DIR>/build.py <timeline|audio|all>`
(Windows: `py -3`). Frame budgets come from the measured narration WAV lengths, so the
pictures always fit the voice instead of the other way round. Everything lands under the
gitignored <WORK_DIR>.
"""

import json
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FPS = 30
SAMPLE_RATE = 44100
NARRATION_DIR = ROOT / "audio" / "narration"
BGM_PATH = ROOT / "audio" / "bgm" / "bgm.wav"
VOICE_GAIN = 1.0
BGM_UNDER_VOICE_GAIN = 0.10
BGM_ALONE_GAIN = 0.22
FADE_OUT_SECONDS = 2.0
PEAK_DBFS = -1.0


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def narration_seconds(shot_id: str) -> float:
    path = NARRATION_DIR / f"{shot_id}.wav"
    if not path.exists():
        raise SystemExit(f"缺少旁白 WAV：{path}（先跑 make_narration.ps1）")
    with wave.open(str(path)) as handle:
        return handle.getnframes() / float(handle.getframerate())


def shot_seconds(shot: dict) -> float:
    if shot.get("narration"):
        return narration_seconds(str(shot["id"])) + float(shot.get("gap", 0.0))
    return float(shot.get("seconds", 0.0))


def build_timeline() -> dict:
    config = load_json(ROOT / "narration.json")
    cursor = 0
    chapters = []
    for chapter in config["chapters"]:
        shots = []
        for shot in chapter["shots"]:
            frames = max(1, int(round(shot_seconds(shot) * FPS)))
            shots.append(
                {
                    "id": shot["id"],
                    "caption": shot.get("caption", ""),
                    "start_frame": cursor,
                    "frames": frames,
                }
            )
            cursor += frames
        chapters.append(
            {
                "id": chapter["id"],
                "title": chapter["title"],
                "issues": chapter.get("issues", []),
                "start_frame": shots[0]["start_frame"],
                "frames": cursor - shots[0]["start_frame"],
                "shots": shots,
            }
        )
    timeline = {"fps": FPS, "total_frames": cursor, "chapters": chapters}
    (ROOT / "timeline.json").write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    total_seconds = cursor / FPS
    print(f"TIMELINE total_frames={cursor} seconds={total_seconds:.1f}")
    for chapter in chapters:
        print(f"  {chapter['id']:<16} {chapter['frames'] / FPS:6.1f}s start={chapter['start_frame']}")
    if not 110.0 <= total_seconds <= 140.0:
        print(f"WARNING 总时长 {total_seconds:.1f}s 不在 110–140 秒之间")
    return timeline


def read_wav_mono(path: Path) -> tuple[list[float], int]:
    with wave.open(str(path)) as handle:
        channels = handle.getnchannels()
        width = handle.getsampwidth()
        rate = handle.getframerate()
        frames = handle.readframes(handle.getnframes())
    if width != 2:
        raise SystemExit(f"只支持 16 bit PCM：{path}")
    samples = [value / 32768.0 for value in _unpack_int16(frames)]
    if channels > 1:
        samples = [sum(samples[i : i + channels]) / channels for i in range(0, len(samples), channels)]
    return samples, rate


def _unpack_int16(raw: bytes) -> list[int]:
    import array

    values = array.array("h")
    values.frombytes(raw)
    if sys.byteorder == "big":
        values.byteswap()
    return values.tolist()


def resample(samples: list[float], source_rate: int, target_rate: int) -> list[float]:
    if source_rate == target_rate:
        return samples
    import numpy

    source = numpy.asarray(samples, dtype=numpy.float32)
    target_count = max(1, int(round(len(source) * target_rate / float(source_rate))))
    positions = numpy.linspace(0.0, len(source) - 1.0, target_count, dtype=numpy.float32)
    return numpy.interp(positions, numpy.arange(len(source), dtype=numpy.float32), source).tolist()


def build_audio() -> None:
    import numpy

    timeline = load_json(ROOT / "timeline.json")
    total_samples = int(round(timeline["total_frames"] / FPS * SAMPLE_RATE))
    master = numpy.zeros(total_samples, dtype=numpy.float32)
    voice_mask = numpy.zeros(total_samples, dtype=bool)
    for chapter in timeline["chapters"]:
        for shot in chapter["shots"]:
            config_shot = _shot_config(timeline, chapter, shot["id"])
            if not config_shot.get("narration"):
                continue
            samples, rate = read_wav_mono(NARRATION_DIR / f"{shot['id']}.wav")
            samples = resample(samples, rate, SAMPLE_RATE)
            offset = int(round(shot["start_frame"] / FPS * SAMPLE_RATE))
            end = min(total_samples, offset + len(samples))
            master[offset:end] += numpy.asarray(samples[: end - offset], dtype=numpy.float32) * VOICE_GAIN
            voice_mask[offset:end] = True
    if not BGM_PATH.exists():
        raise SystemExit(f"缺少 BGM：{BGM_PATH}（把项目的 BGM 解成 16bit PCM WAV 放这里）")
    background, background_rate = read_wav_mono(BGM_PATH)
    background = numpy.asarray(resample(background, background_rate, SAMPLE_RATE), dtype=numpy.float32)
    if background.size == 0:
        raise SystemExit("BGM 解出来是空的")
    repeats = int(numpy.ceil(total_samples / float(background.size)))
    background = numpy.tile(background, repeats)[:total_samples].copy()
    gain = numpy.where(voice_mask, BGM_UNDER_VOICE_GAIN, BGM_ALONE_GAIN).astype(numpy.float32)
    fade_samples = int(FADE_OUT_SECONDS * SAMPLE_RATE)
    if fade_samples < total_samples:
        gain[-fade_samples:] *= numpy.linspace(1.0, 0.0, fade_samples, dtype=numpy.float32)
    master += background * gain
    peak = float(numpy.max(numpy.abs(master))) if master.size else 0.0
    if peak <= 0.0:
        raise SystemExit("混音结果是静音")
    master *= (10.0 ** (PEAK_DBFS / 20.0)) / peak
    pcm = numpy.clip(master * 32767.0, -32768.0, 32767.0).astype("<i2")
    out_path = ROOT / "audio" / "master.wav"
    with wave.open(str(out_path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(pcm.tobytes())
    voiced_seconds = float(voice_mask.sum()) / SAMPLE_RATE
    print(
        f"AUDIO {out_path} samples={total_samples} peak_dbfs={PEAK_DBFS} voice={voiced_seconds:.1f}s"
    )


def _shot_config(timeline: dict, chapter: dict, shot_id: str) -> dict:
    config = load_json(ROOT / "narration.json")
    for config_chapter in config["chapters"]:
        if config_chapter["id"] != chapter["id"]:
            continue
        for shot in config_chapter["shots"]:
            if shot["id"] == shot_id:
                return shot
    raise SystemExit(f"narration.json 里找不到 {chapter['id']}/{shot_id}")


def main(argv: list[str]) -> int:
    action = argv[1] if len(argv) > 1 else "all"
    if action in ("timeline", "all"):
        build_timeline()
    if action in ("audio", "all"):
        build_audio()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
