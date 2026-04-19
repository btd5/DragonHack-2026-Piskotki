import cv2
import depthai as dai
import numpy as np

CLASS_NAMES = ["kvadrat", "oval", "trikotnik"]

def softmax(x):
    x = np.array(x, dtype=np.float32)
    e = np.exp(x - np.max(x))
    return e / e.sum()

print("start")
pipeline = dai.Pipeline()

print("camera")
cam = pipeline.create(dai.node.Camera).build()

nn_frame = cam.requestOutput(
    (224, 224),
    type=dai.ImgFrame.Type.RGB888i   # RGB, ker model to pričakuje
)

preview = cam.requestOutput(
    (640, 480),
    type=dai.ImgFrame.Type.BGR888i
)

# Normalizacija: 0-255 → 0.0-1.0
manip = pipeline.create(dai.node.ImageManipV2)
manip.initialConfig.setFrameType(dai.ImgFrame.Type.RGBF16F16F16i)  # float16 RGB
manip.setMaxOutputFrameSize(224 * 224 * 3 * 2)

nn_frame.link(manip.inputImage)

print("nn")
nn = pipeline.create(dai.node.NeuralNetwork)
nn.setModelPath("ei-luxonis-transfer-learning-tensorflow-lite-float32-model.3.rvc4.tar.xz")
nn.setBackend("snpe")
nn.setBackendProperties({
    "runtime": "dsp",
    "performance_profile": "default"
})

print("link")
manip.out.link(nn.input)

q_nn = nn.out.createOutputQueue(maxSize=4, blocking=False)
q_preview = preview.createOutputQueue(maxSize=4, blocking=False)

print("starting pipeline")
pipeline.start()
print("pipeline started")

last_label = ""
last_conf = 0.0

with pipeline:
    while pipeline.isRunning():
        if q_preview.has():
            pkt_preview = q_preview.get()
            img = pkt_preview.getCvFrame()

            if last_label:
                text = f"{last_label}: {last_conf:.2%}"
                cv2.putText(img, text, (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow("Live preview", img)

        if q_nn.has():
            pkt = q_nn.get()

            scores = pkt.getFirstTensor()
            scores = np.array(scores).squeeze()

            print("raw output:", scores, "shape:", scores.shape)

            if scores.size != 3:
                print(f"POZOR: model ni vrnil 3 vrednosti, ampak {scores.size}")
                continue

            probs = softmax(scores)

            class_id = int(np.argmax(probs))
            conf = float(probs[class_id])
            label = CLASS_NAMES[class_id]

            last_label = label
            last_conf = conf

            print(f"Napoved: {label} ({conf:.2%})")

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

cv2.destroyAllWindows()