"""
Backend za Piškot Klasifikator.

Servira:
  GET  /              -> index.html (frontend)
  GET  /stream.mjpg   -> MJPEG live stream iz depthai kamere
  GET  /latest        -> JSON z zadnjo klasifikacijo ({label, confidence, ts})
  POST /push          -> sprejme payload iz gumba in logira / posreduje naprej

Zagon:
  pip install flask flask-cors opencv-python depthai numpy pillow tensorflow
  python app.py
"""

import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import time
import json
import threading
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

import depthai as dai
from tensorflow.lite.python.interpreter import Interpreter

from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS


# -------------------------
# KONFIG
# -------------------------
CLASS_NAMES        = ["kvadrat", "lunica", "oval", "srce", "trikotnik", "prazno"]
MODEL_PATH         = "model_unquant.tflite"
CLASSIFY_INTERVAL  = 1.0       
JPEG_QUALITY       = 80
HOST               = "0.0.0.0"
PORT               = 8000



class SharedState:
    def __init__(self):
        self.lock         = threading.Lock()
        self.latest_jpeg  = None          # bytes
        self.latest_label = None          # str
        self.latest_conf  = 0.0
        self.latest_raw   = None          # list[float]
        self.latest_ts    = None          # iso string
        self.running      = True

    def update_frame(self, jpeg_bytes):
        with self.lock:
            self.latest_jpeg = jpeg_bytes

    def update_classification(self, label, conf, raw):
        with self.lock:
            self.latest_label = label
            self.latest_conf  = float(conf)
            self.latest_raw   = [float(x) for x in raw]
            self.latest_ts    = time.strftime("%Y-%m-%dT%H:%M:%S")

    def snapshot(self):
        with self.lock:
            return {
                "label":      self.latest_label,
                "confidence": self.latest_conf,
                "raw":        self.latest_raw,
                "timestamp":  self.latest_ts,
            }

    def get_jpeg(self):
        with self.lock:
            return self.latest_jpeg


STATE = SharedState()


# -------------------------
# TFLITE (tvoja originalna logika)
# -------------------------
def preprocess(frame_bgr, input_shape):
    _, h, w, _ = input_shape
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb).resize((w, h), Image.Resampling.BILINEAR)
    x = np.asarray(img, dtype=np.float32) / 255.0
    return np.expand_dims(x, axis=0)


def classify(interpreter, inp, out, frame_bgr):
    x = preprocess(frame_bgr, inp[0]["shape"])
    interpreter.set_tensor(inp[0]["index"], x)
    interpreter.invoke()
    y = interpreter.get_tensor(out[0]["index"])[0]
    idx = int(np.argmax(y))
    return CLASS_NAMES[idx], float(y[idx]), y


# -------------------------
# CAMERA THREAD
# (gre skozi enak depthai pipeline kot tvoja originalna skripta,
#  samo da namesto cv2.imshow pushamo v shared state)
# -------------------------
def camera_worker():
    print("[cam] loading tflite...")
    interpreter = Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    inp = interpreter.get_input_details()
    out = interpreter.get_output_details()
    print("[cam] input:", inp[0]["shape"], "output:", out[0]["shape"])

    print("[cam] starting depthai pipeline...")
    pipeline = dai.Pipeline()
    cam = pipeline.create(dai.node.Camera).build()
    preview = cam.requestOutput((640, 640), type=dai.ImgFrame.Type.BGR888i)
    q_preview = preview.createOutputQueue(maxSize=4, blocking=False)

    last_classify = 0.0

    with pipeline:
        pipeline.start()
        print("[cam] ready")

        while pipeline.isRunning() and STATE.running:
            if not q_preview.has():
                time.sleep(0.005)
                continue

            pkt = q_preview.get()
            frame = pkt.getCvFrame()

            # klasifikacija vsako sekundo
            now = time.time()
            if now - last_classify >= CLASSIFY_INTERVAL:
                last_classify = now
                try:
                    label, conf, raw = classify(interpreter, inp, out, frame)
                    STATE.update_classification(label, conf, raw)
                    print(f"[cls] {label:10s}  conf={conf:.3f}")
                except Exception as e:
                    print("[cls] error:", e)

            # jpeg za MJPEG stream
            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            if ok:
                STATE.update_frame(buf.tobytes())


# -------------------------
# FLASK APP
# -------------------------
app = Flask(__name__, static_folder=None)
CORS(app)   # da lahko frontend tudi iz file:// ali drugega porta dostopa

FRONTEND_DIR = Path(__file__).parent


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/latest")
def latest():
    return jsonify(STATE.snapshot())


@app.route("/stream.mjpg")
def stream():
    def gen():
        boundary = b"--frame"
        while True:
            jpeg = STATE.get_jpeg()
            if jpeg is None:
                time.sleep(0.05)
                continue
            yield (
                boundary + b"\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n"
                + jpeg + b"\r\n"
            )
            # ~25 fps cap
            time.sleep(0.04)

    return Response(
        gen(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.route("/push", methods=["POST"])
def push():
    """
    Sprejme payload iz gumba "pošlji" v frontendu.
    Trenutno ga samo zalogira + shrani v push_log.jsonl.
    Kasneje tu dodaš POST na svoj pravi endpoint (npr. requests.post(...)).
    """
    payload = request.get_json(silent=True) or {}
    payload["received_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    print("[push]", json.dumps(payload, ensure_ascii=False))

    try:
        with open("push_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception as e:
        print("[push] log error:", e)

    # TODO: tu posreduj naprej na pravi endpoint, npr:
    # import requests
    # requests.post("https://tvoj-endpoint/api/piskoti", json=payload, timeout=5)

    return jsonify({"ok": True, "received_at": payload["received_at"]})


# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    t = threading.Thread(target=camera_worker, daemon=True)
    t.start()

    try:
        print(f"[web] http://{HOST}:{PORT}")
        app.run(host=HOST, port=PORT, threaded=True, debug=False)
    finally:
        STATE.running = False
        t.join(timeout=2.0)
