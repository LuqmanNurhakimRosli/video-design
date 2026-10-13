"""Word-level transcript with faster-whisper (slower, better names).

usage: uv run --python 3.12 --with faster-whisper python pipeline/transcribe_fw.py <audio.wav> <out.json>
export audio to 16 kHz mono wav first (see make_video.py get_db).
"""
import json, sys
from faster_whisper import WhisperModel

import wave
import numpy as np

wav, out = sys.argv[1], sys.argv[2]
with wave.open(wav) as f:
    wav = np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768
m =WhisperModel("medium", device="cpu", compute_type="int8")
segs, info = m.transcribe(
    wav, language="en", word_timestamps=True, vad_filter=False,
    initial_prompt="SEDIC 2026 final at MITEC, Kuala Lumpur. Project MATA, Maritime AI Threat Awareness. Insyaallah. Assalamualaikum.",
)
words = []
for s in segs:
    for w in s.words:
        words.append({"text": w.word.strip(), "start": round(w.start, 2), "end": round(w.end, 2), "p": round(w.probability, 2)})
json.dump(words, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(words), "words")
