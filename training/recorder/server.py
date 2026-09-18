#!/usr/bin/env python3
"""Wake-word sample recorder. Serves a phone page and stores what it records.

2026-09-18, Chris: "build the recorder, both of us". The old "Hey Donut" models were trained on
12,000 Piper TTS samples and no human voice at all, which is why they needed shouting and the stock
Okay Nabu model worked first try. This collects the missing ingredient: real people, real rooms.

Stdlib only - Donut's host python has no aiohttp, numpy, ffmpeg or sox. The browser captures 16 kHz
mono and builds the WAV, so this just writes the bytes it is given.

Listens on 127.0.0.1:8444; Tailscale serves it to the tailnet over HTTPS.
Samples land in /data/wakeword/samples/real/<who>/<style>/<room>-<n>.wav
"""
import json, os, re, wave, io
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

ROOT = "/data/wakeword/samples/real"
PAGE = "/opt/wakeword-recorder/index.html"
SAFE = re.compile(r"[^a-z0-9_-]+")
MAX_BYTES = 2_000_000          # a 3 s 16 kHz mono clip is ~96 KB; this is a generous ceiling


def safe(s, default="x"):
    s = SAFE.sub("-", (s or "").strip().lower())
    return s.strip("-") or default


def counts():
    out = {}
    for who in sorted(os.listdir(ROOT)) if os.path.isdir(ROOT) else []:
        d = os.path.join(ROOT, who)
        if not os.path.isdir(d):
            continue
        per = {}
        for style in sorted(os.listdir(d)):
            sd = os.path.join(d, style)
            if os.path.isdir(sd):
                per[style] = len([f for f in os.listdir(sd) if f.endswith(".wav")])
        out[who] = per
    return out


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass                      # the journal does not need a line per sample

    def _send(self, code, body=b"", ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            try:
                body = open(PAGE, "rb").read()
            except OSError:
                return self._send(500, b"page missing", "text/plain")
            return self._send(200, body, "text/html; charset=utf-8")
        if path == "/counts":
            return self._send(200, json.dumps(counts()).encode())
        self._send(404, b"no", "text/plain")

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/upload":
            return self._send(404, b"no", "text/plain")
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._send(400, b'{"error":"bad length"}')
        if not 0 < n <= MAX_BYTES:
            return self._send(413, b'{"error":"too big or empty"}')
        raw = self.rfile.read(n)

        who = safe(self.headers.get("X-Who"), "unknown")
        style = safe(self.headers.get("X-Style"), "misc")
        room = safe(self.headers.get("X-Room"), "room")

        # Trust nothing: parse it as a WAV and check it is what the trainer needs.
        try:
            with wave.open(io.BytesIO(raw)) as w:
                ch, width, rate, frames = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        except Exception as e:
            return self._send(400, json.dumps({"error": f"not a wav: {e}"}).encode())
        if ch != 1 or width != 2:
            return self._send(400, json.dumps({"error": f"need mono 16-bit, got {ch}ch {width*8}bit"}).encode())
        secs = frames / float(rate or 1)
        if not 0.4 <= secs <= 6.0:
            return self._send(400, json.dumps({"error": f"length {secs:.2f}s out of range"}).encode())

        d = os.path.join(ROOT, who, style)
        os.makedirs(d, exist_ok=True)
        i = 1 + max([int(m.group(1)) for f in os.listdir(d)
                     for m in [re.search(r"-(\d+)\.wav$", f)] if m] or [0])
        name = f"{room}-{i:04d}.wav"
        tmp = os.path.join(d, "." + name)
        with open(tmp, "wb") as f:
            f.write(raw)
        os.replace(tmp, os.path.join(d, name))
        return self._send(200, json.dumps({"saved": name, "rate": rate, "seconds": round(secs, 2),
                                           "counts": counts().get(who, {})}).encode())


if __name__ == "__main__":
    os.makedirs(ROOT, exist_ok=True)
    ThreadingHTTPServer(("127.0.0.1", 8444), H).serve_forever()
