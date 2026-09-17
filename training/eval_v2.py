# eval_v2.py - v1 and v2 side by side on clean held-out clips the training never saw.
# Mimics the device: per-frame probabilities, a 5-frame sliding mean, detected if the mean ever
# clears the cutoff. Rows are phrase groups; the first three should be high, the rest near zero.
import glob, os, subprocess, sys, wave, numpy as np
subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--no-cache-dir", "librosa", "soundfile"], check=False)
import librosa
from microwakeword.inference import Model
CUTOFFS = [0.5, 0.6, 0.72, 0.8, 0.85, 0.9, 0.95]
MODELS = {"v1": "/w/out/hey_donut.tflite",
          "v2": "/w/trained/hey_donut_v2/tflite_stream_state_internal_quant/stream_state_internal_quant.tflite"}
GROUPS = ["hey_donut_T", "hey_doenuh", "hey_dohnuh", "hey_donna", "hey_dont", "bare_donuh", "bare_donut", "do_not", "hey_there"]
def load16k(path):
    """piper-sample-generator writes 22,050 Hz; the model (and the feature builder that trained
    it) want 16 kHz int16. Resample the way the training loader does."""
    w = wave.open(path, "rb"); sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16); w.close()
    if sr != 16000:
        a = (librosa.resample(a.astype(np.float32) / 32768.0, orig_sr=sr, target_sr=16000) * 32767).astype(np.int16)
    return a
def peak(model, path):
    p = np.asarray(model.predict_clip(load16k(path), step_ms=10), dtype=np.float32).ravel()
    if len(p) < 5: return float(p.max()) if len(p) else 0.0
    return float(np.convolve(p, np.ones(5) / 5, mode="valid").max())
for name, path in MODELS.items():
    if not os.path.exists(path): print(f"{name}: missing {path}"); continue
    m = Model(path)
    print(f"\n=== {name}  detection rate (%) per group at each cutoff")
    print(f"{'group':14}" + "".join(f"{c:>7}" for c in CUTOFFS) + "   n")
    for g in GROUPS:
        files = sorted(glob.glob(f"/w/samples/eval/{g}/*.wav"))
        if not files: continue
        peaks = np.array([peak(m, f) for f in files])
        print(f"{g:14}" + "".join(f"{100*np.mean(peaks > c):7.1f}" for c in CUTOFFS) + f"   {len(files)}")
print("\nEVAL-DONE", flush=True)
