import subprocess
import os
import uuid

CONFIDENCE_THRESHOLD = -0.5

# Lazy-loaded to avoid ~1.7GB RAM + DLL loading at server startup
_cheap_model = None
_accurate_model = None


def _get_cheap_model():
    global _cheap_model
    if _cheap_model is None:
        from faster_whisper import WhisperModel
        _cheap_model = WhisperModel("distil-small.en", device="cpu", compute_type="int8")
    return _cheap_model


def _get_accurate_model():
    global _accurate_model
    if _accurate_model is None:
        from faster_whisper import WhisperModel
        _accurate_model = WhisperModel("medium.en", device="cpu", compute_type="int8")
    return _accurate_model


def _transcribe(model, audio_path):
    segments, _ = model.transcribe(audio_path, beam_size=5)
    return [
        {
            "start": s.start,
            "end": s.end,
            "text": s.text,
            "conf": s.avg_logprob
        }
        for s in segments
    ]


def _extract(audio_path, start, end, out):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", audio_path,
        "-ss", str(start),
        "-to", str(end),
        "-ar", "16000",
        out
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def hybrid_transcribe(audio_path):
    base = _transcribe(_get_cheap_model(), audio_path)
    final_text = ""

    for i, seg in enumerate(base):
        if seg["conf"] < CONFIDENCE_THRESHOLD:
            tmp = f"tmp_{uuid.uuid4().hex}_{i}.wav"
            _extract(audio_path, seg["start"], seg["end"], tmp)

            try:
                better = _transcribe(_get_accurate_model(), tmp)
                if better:
                    final_text += " " + better[0]["text"]
                else:
                    final_text += " " + seg["text"]
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
        else:
            final_text += " " + seg["text"]

    return final_text.strip()
