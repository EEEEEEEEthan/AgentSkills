"""生成一段 60 秒的搞笑纪录片配乐：八音盒式的拨弦 + 雪橇铃铛 + 低音拨奏。

用法（仓库根目录）：`py -3 .export/short/make_bgm.py`
输出 `.export/short/audio/bgm/bgm.wav`（44.1kHz 单声道 16bit）。
"""

import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
OUT_PATH = ROOT / "audio" / "bgm" / "bgm.wav"
SAMPLE_RATE = 44100
BPM = 108.0
SECONDS = 66.0
BEAT = 60.0 / BPM

# Am — Am — F — F — C — C — G — G 的循环，每小节两拍一个和弦
CHORDS = [
    (57, [69, 72, 76]),  # Am
    (57, [69, 72, 76]),
    (53, [65, 69, 72]),  # F
    (53, [65, 69, 72]),
    (48, [64, 67, 72]),  # C
    (48, [64, 67, 72]),
    (55, [67, 71, 74]),  # G
    (55, [67, 71, 74]),
]
MELODY = [76, 72, 69, 0, 76, 79, 76, 72, 74, 71, 67, 0, 72, 76, 79, 76]


def midi_hz(note: int) -> float:
    return 440.0 * 2.0 ** ((note - 69) / 12.0)


def beep(freq: float, seconds: float, decay: float, harmonics: list[tuple[float, float]]) -> np.ndarray:
    count = int(seconds * SAMPLE_RATE)
    times = np.arange(count) / SAMPLE_RATE
    envelope = np.exp(-times / decay)
    attack = np.minimum(1.0, times / 0.006)
    wave_sum = np.zeros(count)
    for multiple, level in harmonics:
        wave_sum += level * np.sin(2.0 * np.pi * freq * multiple * times)
    return wave_sum * envelope * attack


def pluck(freq: float, seconds: float = 0.42) -> np.ndarray:
    return beep(freq, seconds, 0.085, [(1.0, 1.0), (2.0, 0.35), (3.0, 0.18), (4.0, 0.08)])


def bass(freq: float, seconds: float = 0.5) -> np.ndarray:
    return beep(freq, seconds, 0.16, [(0.5, 0.5), (1.0, 1.0), (2.0, 0.2)])


def bell(seconds: float = 0.09) -> np.ndarray:
    count = int(seconds * SAMPLE_RATE)
    times = np.arange(count) / SAMPLE_RATE
    noise = np.random.default_rng(7).normal(0.0, 1.0, count)
    ring = np.sin(2.0 * np.pi * 3200.0 * times) * 0.6 + noise * 0.4
    return ring * np.exp(-times / 0.02)


def add_track(track: np.ndarray, sound: np.ndarray, at_seconds: float, gain: float) -> None:
    start = int(at_seconds * SAMPLE_RATE)
    end = min(track.size, start + sound.size)
    if start >= track.size:
        return
    track[start:end] += sound[: end - start] * gain


def main() -> int:
    total = int(SECONDS * SAMPLE_RATE)
    track = np.zeros(total)
    bar = BEAT * 4.0
    index = 0
    time = 0.0
    while time < SECONDS:
        root, chord = CHORDS[index % len(CHORDS)]
        # 低音：每拍一下
        for beat in range(4):
            add_track(track, bass(midi_hz(root - 12)), time + beat * BEAT, 0.42)
        # 拨弦：八分音符的分解和弦，强弱交替
        pattern = [0, 1, 2, 1, 0, 2, 1, 2]
        for step, tone in enumerate(pattern):
            note = chord[tone] + (12 if step % 4 == 2 else 0)
            add_track(track, pluck(midi_hz(note)), time + step * BEAT * 0.5, 0.30)
        # 旋律：每两小节出现一次，留白让旁白说话
        if index % 4 in (1, 3):
            for step, note in enumerate(MELODY):
                if note:
                    add_track(
                        track, pluck(midi_hz(note), 0.34) * 1.0,
                        time + step * BEAT * 0.25, 0.20,
                    )
        # 雪橇铃：十六分音符的轻响
        for step in range(16):
            gain = 0.055 if step % 4 == 0 else 0.028
            add_track(track, bell(), time + step * BEAT * 0.25, gain)
        time += bar
        index += 1
    peak = float(np.max(np.abs(track)))
    track = track / peak * 0.85
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT_PATH), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes((track * 32767.0).astype("<i2").tobytes())
    print(f"BGM {OUT_PATH} {SECONDS:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
