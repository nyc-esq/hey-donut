import os, numpy as np, scipy.io.wavfile, datasets

def have(d, n=10):
    return os.path.isdir(d) and len(os.listdir(d)) >= n

# --- MIT room impulse responses (small, high value: room acoustics realism) ---
out = "/w/augment/mit_rirs"
os.makedirs(out, exist_ok=True)
if not have(out):
    ds = datasets.load_dataset("davidscripka/MIT_environmental_impulse_responses",
                               split="train", streaming=True)
    n = 0
    for row in ds:
        a = row["audio"]
        name = os.path.basename(a["path"])
        if not name.endswith(".wav"): name += ".wav"
        scipy.io.wavfile.write(os.path.join(out, name), 16000,
                               (np.asarray(a["array"]) * 32767).astype(np.int16))
        n += 1
    print(f"  MIT RIRs written: {n}")
else:
    print(f"  MIT RIRs present: {len(os.listdir(out))}")

# --- background clips: optional, best-effort across a couple of sources ---
out2 = "/w/augment/background"
os.makedirs(out2, exist_ok=True)
if not have(out2, 50):
    got = 0
    for name, split in (("agkphysics/AudioSet", "train"),):
        try:
            ds = datasets.load_dataset(name, split=split, streaming=True, trust_remote_code=True)
            for row in ds:
                a = row.get("audio")
                if not a: continue
                scipy.io.wavfile.write(os.path.join(out2, f"bg_{got}.wav"), 16000,
                                       (np.asarray(a["array"]) * 32767).astype(np.int16))
                got += 1
                if got >= 1500: break
            if got: break
        except Exception as e:
            print(f"  {name} unavailable: {str(e)[:120]}")
    print(f"  background clips: {got}")
else:
    print(f"  background present: {len(os.listdir(out2))}")
print("AUG-DONE")
