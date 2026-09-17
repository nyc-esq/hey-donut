# Training pipeline

Everything here is generic. Change the phrase in `gen.sh` and you get your own wake word.

## Run order

| Step | Command | Produces |
|---|---|---|
| 1 | `./gen.sh` | positives + adversarial near-misses (`/w/samples/`) |
| 2 | `./getneg.sh` | precomputed negative features (`/w/negatives/`, ~30 GB) |
| 3 | `python get_aug.py` | impulse responses + background noise (`/w/augment/`) |
| 4 | `python build_features.py` | spectrograms (`/w/features/`, ~13 GB) |
| 5 | `python make_config.py` | `training_parameters.yaml` |
| 6 | `./train.sh` | quantized streaming `.tflite` |

All paths are `/w/...` inside the container. Mount your workspace there.

## Changing the phrase

In `gen.sh`, replace `'hey donut.'` with your phrase, then **rewrite the adversarial list**
underneath it. Those near-misses are most of what stops false triggers — they should be
things that sound like your phrase but aren't:

```bash
for phrase in "donut." "donuts." "do not." "hey dolly." "hey donna." "doughnut."; do
```

Say your phrase out loud and write down what it rhymes with, what it sounds like without
the first syllable, and the nearest common word. Those are your adversarials.

Also update `train_dir` in `make_config.py` and the output names in your manifest.

## Knobs worth knowing

| Setting | Where | Effect |
|---|---|---|
| `negative_class_weight: 20` | `make_config.py` | how hard false accepts are punished. High = conservative. |
| `sampling_weight` per feature set | `make_config.py` | adversarials sit at 4.0, general negatives at 10.0 |
| `training_steps: 10000` | `make_config.py` | more steps, longer train |
| `clip_duration_ms: 1500` | `make_config.py` | must comfortably fit your phrase |
| `AddBackgroundNoise: 0.75` | `build_features.py` | fraction of samples given background noise |
| `probability_cutoff` | the manifest | detection threshold; the training log prints the full curve |

Pick your cutoff from the table `train.sh` prints at the end, which lists false-rejection
rate against false-accepts-per-hour at every threshold. Choose the point where false
accepts per hour hits zero, then loosen it only if the thing genuinely misses you.

## Hardware

CPU is fine — this model was trained on spare cores under `nice`, no GPU. The container
exists because TensorFlow is particular about Python versions, not because of CUDA.

## v2: teach it how the phrase is actually said

Said at speed, the T in "Donut" is a glottal stop: *hey donuh*. Piper never says it that way,
and worse, Whisper transcribes Piper's T-less renderings as **"Hey Donna"** - which v1 had as
a near-miss. v1 was trained to reject the real pronunciation. The `*2.sh` / `*2.py` files are
the fix, and they reuse v1's positive features and the 30 GB of negatives untouched:

| File | Does |
|---|---|
| `gen2.sh` | T-less positives ("hey doe nuh." / "hey dohnuh." / "hey doughnuh." - spellings checked by transcribing them), fast deliveries at 0.6-0.7 length scale, new near-misses (bare "donuh." so *hey* stays required, "hey don't", "hey dunno", "hey no"), a held-out eval set, and the flattened dirs **without "hey donna"** |
| `build_features2.py` | spectrograms for the two new sets only |
| `make_config2.py` | v1's config plus the T-less positives, adversarials swapped for the v2 set, `train_dir` v2 |
| `train2.sh` | identical to `train.sh` on the v2 config |
| `eval_v2.py` | v1 and v2 side by side on the held-out clips: detection rate per phrase group at seven cutoffs, with the device's 5-frame sliding mean |
| `run_v2.sh` | the chain, resumable, packaged with the first zero-false-accept cutoff |

The lesson generalises: **transcribe your adversarials before you trust them.** If Whisper
hears one of them as your wake word, so will your model, and you have just taught it to
ignore the person who talks that way.
