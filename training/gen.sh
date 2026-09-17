#!/bin/bash
set -e
pip install --quiet --no-cache-dir piper-tts 2>&1 | tail -1
cd /opt/piper-sample-generator
cp /w/work/en_US-libritts_r-medium.pt models/ 2>/dev/null || true
M=models/en_US-libritts_r-medium.pt

echo "### POSITIVES: 'hey donut' x 12000, varied speed"
python3 -m piper_sample_generator 'hey donut.' --model $M \
  --max-samples 12000 --batch-size 100 --max-speakers 500 \
  --length-scales 0.75 0.85 1.0 1.15 1.3 \
  --output-dir /w/samples/positive/ 2>&1 | grep -viE "FutureWarning|warnings.warn|DEBUG:" | tail -4

echo "### ADVERSARIAL: near-misses that must NOT trigger"
i=0
for phrase in "donut." "donuts." "do not." "hey dolly." "hey donna." "hey do not do that." "the donut shop." "hey there." "a donut please." "doughnut."; do
  i=$((i+1))
  python3 -m piper_sample_generator "$phrase" --model $M \
    --max-samples 400 --batch-size 100 --max-speakers 500 \
    --length-scales 0.85 1.0 1.15 \
    --output-dir "/w/samples/adversarial/p$i/" 2>&1 | grep -c "Done" >/dev/null
  echo "   done: $phrase"
done

echo "### COUNTS"
echo "  positives:   $(ls /w/samples/positive/ 2>/dev/null | wc -l)"
echo "  adversarial: $(find /w/samples/adversarial -name '*.wav' 2>/dev/null | wc -l)"
