# The recorder — collecting real voices

**Why this exists.** v1 and v2 of this wake word were trained on 12,000 samples from
`piper_sample_generator` and **not one recording of a human being** (see `../gen.sh`). Both score
92–96 % on their own held-out set and both make people shout and repeat themselves in a real room,
because the held-out clips came out of the same synthesiser. Swapping to a stock model trained on
real speech fixed it first try, on the same hardware, in the same second. The models were the fault.

So: real voices, real rooms, real distances.

## What it is

A phone page and a tiny stdlib-only server. The browser captures **16 kHz mono 16-bit** and builds
the WAV; the server validates and files it. No numpy, ffmpeg or sox needed on the host.

    server.py                   stdlib HTTP on 127.0.0.1:8444
    index.html                  the phone page
    wakeword-recorder.service   systemd unit

Samples land in `/data/wakeword/samples/real/<who>/<style>/<room>-NNNN.wav`.

## Install

    sudo mkdir -p /opt/wakeword-recorder
    sudo install -m 755 server.py /opt/wakeword-recorder/
    sudo install -m 644 index.html /opt/wakeword-recorder/
    sudo install -m 644 wakeword-recorder.service /etc/systemd/system/
    sudo systemctl enable --now wakeword-recorder
    sudo tailscale serve --bg --https=8444 http://127.0.0.1:8444

Then open `https://<host>.<tailnet>.ts.net:8444` on a phone **on the tailnet**. HTTPS matters: browsers
refuse microphone access to a page that is not a secure context, which also rules out emailing the
HTML as a file.

## The session

200 samples per person per room, six blocks, about 20 minutes:

| block | n | what it captures |
|---|---|---|
| normal | 60 | the everyday case |
| far | 40 | across the room, where detection actually fails |
| quiet | 30 | half voice |
| fast | 30 | "hey donuh" — the dropped T, how it is really said |
| calling | 20 | raised voice from the next room |
| noisy | 20 | TV or music behind it |

The page disables the browser's echo cancellation, noise suppression and auto gain, so the training
data is the microphone's own signal and the pipeline's augmentation (RIR + background) supplies the
rest.

## Rules that earned their place

- **Record more than one person.** The old model had no Jeanette in it at all.
- **Say it lazily.** Train on perfect enunciation and it only answers perfect enunciation.
- **Hold out REAL clips for evaluation.** The whole failure was an eval drawn from the training
  generator. A model is only as honest as the set you judge it on.

## Checking progress

    curl -s http://127.0.0.1:8444/counts
