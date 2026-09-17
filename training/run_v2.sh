#!/bin/bash
# run_v2.sh - the whole v2 chain on Donut's CPU, resumable (each stage skips if its output exists).
# Host side: nohup /w/run_v2.sh > /w/v2.log 2>&1 &
set -u
W=/w
D="docker run --rm -v $W:/w wakeword-train"
say() { echo "$(date '+%F %T') $*"; }
stage() { # name donefile command...
  local name="$1" done="$2"; shift 2
  if [ -e "$done" ]; then say "$name: done already ($done)"; return 0; fi
  say "$name: start"; "$@"; local rc=$?; say "$name: exit $rc"; [ $rc -eq 0 ] || exit $rc
}
stage gen2      "$W/samples/adversarial_flat2"          $D bash /w/gen2.sh
stage features2 "$W/features/adversarial2/testing"      $D python /w/build_features2.py
stage config2   "$W/training_parameters_v2.yaml"        $D python /w/make_config2.py
stage train2    "$W/trained/hey_donut_v2/tflite_stream_state_internal_quant/stream_state_internal_quant.tflite" $D bash /w/train2.sh
stage eval2     "$W/eval_v2.txt" bash -c "$D python /w/eval_v2.py | tee $W/eval_v2.txt"
# package: model + manifest with the first zero-false-accept cutoff from the training log
python3 - <<'PY'
import re, json, shutil, glob
W = "/w"
log = open(f"{W}/v2.log", errors="replace").read()
rows = re.findall(r"Cutoff ([0-9.]+): frr=([0-9.]+); faph=([0-9.]+)", log)
zero = [float(c) for c, frr, fa in rows if float(fa) == 0.0]
cutoff = round(min(zero), 2) if zero else 0.8
src = glob.glob(f"{W}/trained/hey_donut_v2/tflite_stream_state_internal_quant/*.tflite")[0]
shutil.copy(src, f"{W}/out/hey_donut_v2.tflite")
m = json.load(open(f"{W}/out/hey_donut.json"))
m["model"] = "hey_donut_v2.tflite"; m["micro"]["probability_cutoff"] = cutoff
json.dump(m, open(f"{W}/out/hey_donut_v2.json", "w"), indent=2)
table = "\n".join(f"cutoff {c}: missed {100*float(frr):.1f}%, false/h {fa}" for c, frr, fa in rows)
open(f"{W}/v2_summary.txt", "w").write(f"hey_donut_v2 packaged, cutoff {cutoff}\n{table}\n\n" + open(f"{W}/eval_v2.txt").read())
print(open(f"{W}/v2_summary.txt").read())
PY
# tell the owner (a Telegram message through Home Assistant)
TOK=${HA_TOKEN:?set HA_TOKEN to a Home Assistant long-lived token}
MSG=$(python3 -c "import json,sys; print(json.dumps({'message': 'Wake word v2 finished training.\n\n' + open('/w/v2_summary.txt').read()[:3500], 'target': 8242922389, 'parse_mode': 'plain_text'}))")
curl -s -o /dev/null -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" -d "$MSG" http://127.0.0.1:8123/api/services/telegram_bot/send_message
say "ALL-DONE"
