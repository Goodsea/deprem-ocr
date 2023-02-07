import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import time
from aioflask import Flask, jsonify, request

import utility
from detector import *
from recognizer import *

app = Flask(__name__)

# Global Detector and Recognizer
args = utility.parse_args()
text_recognizer = TextRecognizer(args)
text_detector = TextDetector(args)


@app.route("/", methods=["GET"])
async def index():
    return jsonify(
        {
            "ServiceName": "OCR API",
            "version": "1.0.0",
            "Environment": "Development",
        }
    )


@app.route("/", methods=["POST"])
async def main():
    image_file = request.files["image_file"]
    img = np.array(Image.open(image_file).convert("RGB"))

    response = {
        "table": None,
        "message": "OK",
        "timestamp": int(time.time() * 1000),
    }

    # Detect text regions
    dt_boxes, _ = text_detector(img)

    boxes = []
    for box in dt_boxes:
        p1, p2, p3, p4 = box
        x1 = min(p1[0], p2[0], p3[0], p4[0])
        y1 = min(p1[1], p2[1], p3[1], p4[1])
        x2 = max(p1[0], p2[0], p3[0], p4[0])
        y2 = max(p1[1], p2[1], p3[1], p4[1])
        boxes.append([x1, y1, x2, y2])

    # Recognize text
    img_list = []
    for i in range(len(boxes)):
        x1, y1, x2, y2 = map(int, boxes[i])
        img_list.append(img.copy()[y1:y2, x1:x2])

    rec_res, _ = text_recognizer(img_list)

    # Postprocess
    table = dict()
    for i in range(len(rec_res)):
        table[i] = {
            "text": rec_res[i][0],
        }

    response["table"] = table

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8080)
