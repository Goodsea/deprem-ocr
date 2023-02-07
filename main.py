import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import requests
from io import BytesIO

import utility
from detector import *
from recognizer import *

# Global Detector and Recognizer
args = utility.parse_args()
text_recognizer = TextRecognizer(args)
text_detector = TextDetector(args)


def apply_ocr(img):
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
    img_list.reverse()

    rec_res, _ = text_recognizer(img_list)

    # Postprocess
    total_text = ""
    table = dict()
    for i in range(len(rec_res)):
        table[i] = {
            "text": rec_res[i][0],
        }
        total_text += rec_res[i][0] + " "

    total_text = total_text.strip()
    return total_text


def main():
    image_url = "https://i.ibb.co/kQvHGjj/aewrg.png"
    response = requests.get(image_url)
    img = np.array(Image.open(BytesIO(response.content)).convert("RGB"))
    ocr_text = apply_ocr(img)
    print("Output:", ocr_text)


if __name__ == "__main__":
    main()
