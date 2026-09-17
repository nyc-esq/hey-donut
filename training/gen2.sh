#!/bin/bash
# gen2.sh - v2 positives, near-misses and held-out clips for "hey donut" (2026-09-16).
# Why v2: said aloud the T in "Donut" is usually a glottal stop ("hey donuh"), and the v1 model only
# ever heard Piper's crisp "hey donut.". Worse, "hey donna." was a v1 near-miss, and Whisper hears
# Piper's T-less renderings as "Hey Donna" - v1 was trained to REJECT the way the phrase is said.
# Spellings below were checked by transcribing Piper's output: "doe nuh" / "dohnuh" keep the long O.
set -e
pip install --quiet --no-cache-dir piper-tts 2>&1 | tail -1
cd /opt/piper-sample-generator
cp /w/work/en_US-libritts_r-medium.pt models/ 2>/dev/null || true
M=models/en_US-libritts_r-medium.pt
gen() { # phrase count outdir length-scales...
  local phrase="$1" n="$2" out="$3"; shift 3
  if [ -d "$out" ] && [ "$(ls "$out" | wc -l)" -ge "$n" ]; then echo "   $phrase -> present"; return; fi
  rm -rf "$out"
  python3 -m piper_sample_generator "$phrase" --model $M --max-samples "$n" --batch-size 100 --max-speakers 500 \
    --length-scales "$@" --output-dir "$out/" 2>&1 | grep -iE "^error|Traceback" || true
  echo "   $phrase -> $(ls "$out" | wc -l) files"
}
echo "### T-LESS POSITIVES"
gen "hey doe nuh."   3000 /w/samples/positive_tless/p1 0.75 0.85 1.0 1.15 1.3
gen "hey dohnuh."    3000 /w/samples/positive_tless/p2 0.75 0.85 1.0 1.15 1.3
gen "hey doughnuh."  2000 /w/samples/positive_tless/p3 0.75 0.85 1.0 1.15 1.3
echo "### FAST DELIVERIES (a wake word is said quickly)"
gen "hey donut."     2000 /w/samples/positive_tless/p4 0.6 0.7
gen "hey doe nuh."   1000 /w/samples/positive_tless/p5 0.6 0.7
echo "### NEW NEAR-MISSES (bare T-less forms keep 'hey' required; the rest are common phrases)"
i=10
for phrase in "donuh." "doe nuh." "dohnuh." "hey don't." "hey dunno." "hey no." "hey, don't do that."; do
  i=$((i+1)); gen "$phrase" 400 /w/samples/adversarial2/p$i 0.85 1.0 1.15
done
echo "### HELD-OUT EVAL CLIPS (never trained on)"
gen "hey donut."     200 /w/samples/eval/hey_donut_T   0.85 1.0 1.15
gen "hey doe nuh."   200 /w/samples/eval/hey_doenuh    0.85 1.0 1.15
gen "hey dohnuh."    200 /w/samples/eval/hey_dohnuh    0.85 1.0 1.15
gen "hey donna."     200 /w/samples/eval/hey_donna     0.85 1.0 1.15
gen "hey don't."     200 /w/samples/eval/hey_dont      0.85 1.0 1.15
gen "donuh."         200 /w/samples/eval/bare_donuh    0.85 1.0 1.15
gen "donut."         200 /w/samples/eval/bare_donut    0.85 1.0 1.15
gen "do not."        200 /w/samples/eval/do_not        0.85 1.0 1.15
gen "hey there."     200 /w/samples/eval/hey_there     0.85 1.0 1.15
echo "### FLATTEN (Clips() reads one directory)"
rm -rf /w/samples/positive_tless_flat /w/samples/adversarial_flat2
mkdir -p /w/samples/positive_tless_flat /w/samples/adversarial_flat2
for d in /w/samples/positive_tless/p*; do b=$(basename "$d"); for f in "$d"/*.wav; do ln "$f" "/w/samples/positive_tless_flat/${b}_$(basename "$f")"; done; done
# v1 near-misses (gen.sh order: p1 donut p2 donuts p3 do not p4 hey dolly p5 HEY DONNA p6 hey do not do that
# p7 the donut shop p8 hey there p9 a donut please p10 doughnut) minus p5, plus the new set
for d in /w/samples/adversarial/p1 /w/samples/adversarial/p2 /w/samples/adversarial/p3 /w/samples/adversarial/p4 \
         /w/samples/adversarial/p6 /w/samples/adversarial/p7 /w/samples/adversarial/p8 /w/samples/adversarial/p9 \
         /w/samples/adversarial/p10 /w/samples/adversarial2/p*; do
  b=$(basename "$d"); for f in "$d"/*.wav; do ln "$f" "/w/samples/adversarial_flat2/${b}_$(basename "$f")"; done
done
echo "  positive (v1, kept):  $(ls /w/samples/positive | wc -l)"
echo "  positive_tless_flat:  $(ls /w/samples/positive_tless_flat | wc -l)"
echo "  adversarial_flat2:    $(ls /w/samples/adversarial_flat2 | wc -l)"
echo "GEN2-DONE"
