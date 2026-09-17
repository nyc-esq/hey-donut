# Hey Donut

A custom **"Hey Donut"** wake word for Home Assistant voice assistants. Runs entirely
on-device with [microWakeWord](https://github.com/kahrendt/microWakeWord) — no cloud, no
account, nothing leaves your house.

Two files, 62 KB. Drop them in and your assistant answers to Donut.

```
model/hey_donut.tflite    62 KB   int8 quantized streaming model
model/hey_donut.json      356 B   microWakeWord v2 manifest
```

The full training pipeline is in [`training/`](training/) if you'd rather teach it **your**
name instead.

---

## v2 (2026-09-16): trained on how the phrase is actually said

`model/hey_donut_v2.*` is the model to use. Said at speed, the T in "Donut" is a glottal stop
("hey donuh"), and v1 had only ever heard Piper's crisp "hey donut." - worse, Piper's T-less
renderings transcribe as "Hey Donna", which v1 was trained to *reject*. v2 adds 11,000 T-less and
fast-delivery positives and drops "hey donna" from the near-misses. On 1,800 held-out clean clips,
detection rate at a cutoff of 0.85:

| Phrase (200 clips each) | v1 | v2 |
|---|---|---|
| "hey donut", crisp T | 51.0% | **95.5%** |
| "hey doe nuh" | 60.0% | **96.5%** |
| "hey dohnuh" | 52.0% | **92.5%** |
| "hey donna" (near-miss) | 0.0% | 27.0% |
| "hey don't", bare "donut", "do not", "hey there" | 0% | 0-1% |

Framework table for v2 on its augmented test set: cutoff 0.95 = 9.0% missed / 0 false accepts per
hour; 0.77 = 4.9% / 0.19; 0.47 = 2.9% / 0.38. The manifest ships 0.95; 0.85 is a fair working point.
Full numbers in `training/eval_v2_results.txt`; how it was made in `training/README.md`.

## How well does v1 work?

Measured on the held-out test set at the shipped cutoff of `0.72`:

| Metric | Value |
|---|---|
| False rejection rate | **4.1%** (about 96 of 100 attempts wake it) |
| False accepts per hour | **0.000** |
| AUC | 0.032 |

Lower cutoffs trade accuracy for twitchiness, if you want them:

| Cutoff | Missed wakes | False accepts/hour |
|---|---|---|
| **0.72** (default) | 4.1% | 0.000 |
| 0.37 | 2.0% | 0.19 |
| 0.25 | 1.7% | 0.56 |
| 0.10 | 1.2% | 1.9 |

It was trained against deliberate near-misses so ordinary conversation doesn't set it off:
`donut`, `donuts`, `doughnut`, `do not`, `hey donna`, `hey dolly`, `the donut shop`,
`a donut please`, `hey there`.

---

## Install

### ESPHome voice satellites

Copy both files somewhere your ESPHome build can reach, and reference the manifest:

```yaml
micro_wake_word:
  models:
    - model: hey_donut.json
```

Requires ESPHome **2024.7.0** or newer (`tensor_arena_size` is 37000).

### ThirdReality / Buildroot-based speakers

These store wake words as ordinary files on a writable overlay — no firmware flash needed:

```bash
scp model/hey_donut.* root@<speaker-ip>:/usr/share/thirdreality/wakewords/microwakeword/
```

Restart the voice service, then pick **Hey Donut** in Home Assistant under the satellite's
wake word selector.

### Then tune it

Home Assistant exposes a sensitivity control per satellite:

```
number.<your_satellite>_wake_word_1_sensitivity
```

This **overrides** the manifest's `probability_cutoff` and it *is* the cutoff: **higher is
stricter**, lower wakes more easily. (Verified in the source of the Open Home Foundation's
`linux-voice-assistant`, which the ThirdReality speakers run: the number is stored as
`wake_word_1_threshold` and passed to microWakeWord as `probability_cutoff`.) Start at the
manifest's value and adjust only after reading the next section, which will save you an evening.

---

## Before you tune anything, move the microphone

The single biggest factor in whether a wake word works is **where the microphone physically
sits** — not the threshold, not the gain, not the noise suppression setting.

A satellite that missed roughly 70% of attempts was fixed completely by moving it out from
behind a monitor and away from a loudspeaker. Detection went to 10/10 at ten feet with no
configuration change at all. Six rounds of threshold tuning before that had produced
*incoherent* results — worse in both directions — which is itself the diagnostic:

> **If turning a dial up and turning it down both make things worse, the environment is
> moving, not the dial.** Stop tuning and look at the room.

Things that hurt: hard surfaces right behind the mic, a speaker cone anywhere near it,
being inside a shelf or cabinet, sitting behind a screen.

Also worth knowing: a satellite **cannot hear a wake word while it is already listening,
processing or responding** — roughly a nine-second window. Attempts inside that window
aren't detection failures. Count wake-ups from the satellite's own state history rather
than by feel, and try ten in a row so you get a rate instead of an impression.

---

## Train your own wake word

The pipeline in [`training/`](training/) is generic — change the phrase and run it. It
generates its own training audio, so **you never record yourself saying anything.**

Positives come from [piper-sample-generator](https://github.com/rhasspy/piper-sample-generator)
using a multi-speaker LibriTTS-R checkpoint: 12,000 samples across 500 speakers at five
speaking rates. Negatives are precomputed spectrogram features from the microWakeWord
dataset. Total training data is around 44 GB, almost all of it downloaded or generated —
which is why it isn't in this repo.

```bash
cd training
docker build -t wakeword-train .
docker run --rm -v /your/workspace:/w wakeword-train bash -c "
  /w/gen.sh &&          # synthesize positives + adversarial near-misses
  /w/getneg.sh &&       # fetch negative feature sets
  python /w/get_aug.py &&      # room impulse responses + background noise
  python /w/build_features.py && # spectrograms
  python /w/make_config.py &&
  /w/train.sh"
```

| File | Does |
|---|---|
| `gen.sh` | synthesizes positives and the adversarial near-miss set |
| `getneg.sh` | downloads precomputed negative features |
| `get_aug.py` | MIT room impulse responses + background clips for augmentation |
| `build_features.py` | turns audio into spectrograms with augmentation |
| `make_config.py` | writes `training_parameters.yaml` |
| `train.sh` | trains and exports the quantized streaming `.tflite` |

### Picking a phrase that actually works

**Three syllables with a hard stop consonant.** Bare "Donut" was tried and rejected on
acoustic grounds — two syllables with a soft onset, and it false-triggered on "do not" and
"donuts" constantly. Adding "Hey" gave it the length and the attack it needed.

Whatever you choose, generate an adversarial set of near-misses for it (see `gen.sh`) and
weight them heavily. That list is most of why this model doesn't wake up during dinner.

### It trains on CPU

This model was trained on spare CPU cores under `nice`, not a GPU — roughly 10,000 steps.
TensorFlow's Python version requirements are the reason the pipeline is containerized.

---

## Security note for anyone opening up a voice speaker

Several consumer voice satellites ship with **SSH, Telnet and ADB all reachable on the LAN
and a vendor-documented default root password.** ADB over TCP is the worst of the three: it
grants root with no authentication at all, so there is no password to get wrong. These are
devices with always-on microphones.

If you're going to put a custom wake word on one, change the default password and close the
services you aren't using while you're in there.

---

## Credits

- [microWakeWord](https://github.com/kahrendt/microWakeWord) by Kevin Ahrendt — the training
  framework and the negative datasets
- [piper-sample-generator](https://github.com/rhasspy/piper-sample-generator) by Rhasspy —
  synthetic positives
- [MIT environmental impulse responses](https://huggingface.co/datasets/davidscripka/MIT_environmental_impulse_responses)
  — room acoustics augmentation

## License

**[CC0 1.0 Universal](LICENSE)** — a public domain dedication. No rights reserved, no
attribution required. Use it, ship it, fork it, rename it, put it in a product. You do not
need to ask and you do not need to credit anyone.

The upstream tools keep their own licenses, which this dedication does not and cannot change:
[microWakeWord](https://github.com/kahrendt/microWakeWord) is Apache-2.0 and
[piper-sample-generator](https://github.com/rhasspy/piper-sample-generator) is MIT. If you
redistribute a model you trained with them, that is your model — but the tools are theirs.
