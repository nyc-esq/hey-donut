#!/bin/bash
cd /w/negatives
echo "### microWakeWord precomputed negative features"
for f in dinner_party.zip no_speech.zip speech.zip dinner_party_eval.zip; do
  echo "--- $f"
  wget -q --show-progress --timeout=60 --tries=3 \
    "https://huggingface.co/datasets/kahrendt/microwakeword/resolve/main/$f" -O "$f" 2>&1 | tail -1
  [ -s "$f" ] || { echo "   (not found, skipping)"; rm -f "$f"; }
done
echo "### done"; ls -la /w/negatives/
du -sh /w/negatives
