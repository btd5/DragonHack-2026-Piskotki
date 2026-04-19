import cv2
import depthai as dai
import numpy as np
import time
import os

CLASS_NAMES = [""]

SAVE_COUNT = 100
SAVE_FOLDER = "captured_shapes_zares"

def softmax(x):
    x = np.array(x, dtype=np.float32)
    e = np.exp(x - np.max(x))
    return e / e.sum()

pipeline = dai.Pipeline()

cam = pipeline.create(dai.node.Camera).build()

nn_frame = cam.requestOutput(
    (240, 240),
    type=dai.ImgFrame.Type.BGR888i
)

preview = cam.requestOutput(
    (640, 640),
    type=dai.ImgFrame.Type.BGR888i
)

nn = pipeline.create(dai.node.NeuralNetwork)
nn.setModelPath("ei-test2-transfer-learning-tensorflow-lite-float32-model.28.rvc4.tar.xz")
nn.setBackend("snpe")
nn.setBackendProperties({
    "runtime": "dsp",
    "performance_profile": "default"
})

nn_frame.link(nn.input)

q_nn = nn.out.createOutputQueue(maxSize=4, blocking=False)
q_preview = preview.createOutputQueue(maxSize=4, blocking=False)

os.makedirs(SAVE_FOLDER, exist_ok=True)

last_label = ""
last_img = None
saved_images = 0

with pipeline:
    pipeline.start()

    while pipeline.isRunning():
        if q_preview.has():
            pkt_preview = q_preview.get()
            img = pkt_preview.getCvFrame()
            last_img = img.copy()

            display_img = img.copy()

            if last_label != "":
                cv2.putText(
                    display_img,
                    f"Oblika: {last_label}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 0, 0),
                    2,
                    cv2.LINE_AA
                )

            cv2.putText(
                display_img,
                "SPACE = shrani, Q = izhod",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
                cv2.LINE_AA
            )

            cv2.imshow("Live preview", display_img)

        if q_nn.has():
            pkt = q_nn.get()
            scores = np.array(pkt.getFirstTensor()).squeeze()

            if scores.size != 3:
                continue

            probs = softmax(scores)
            class_id = 0
            last_label = CLASS_NAMES[class_id]

        key = cv2.waitKey(1) & 0xFF

        if key == ord(" "):  # SPACE
            if last_img is not None and last_label != "":
                saved_images += 1
                filename = f"{last_label}.{saved_images}.jpg"
                filepath = os.path.join(SAVE_FOLDER, filename)

                cv2.imwrite(filepath, last_img)
                print(f"Shranjeno: {filepath}")

                if saved_images >= SAVE_COUNT:
                    print("Doseženo maksimalno število slik.")
                    break
            else:
                print("Ni slike ali oznake za shranjevanje.")

        elif key == ord("q"):
            break

cv2.destroyAllWindows()