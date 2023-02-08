import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import time
import requests
from io import BytesIO

from deprem_ocr import utility
from deprem_ocr.detector import TextDetector
from deprem_ocr.recognizer import TextRecognizer

__all__ = ["DepremOCR"]


class DepremOCR:
    def __init__(self):
        args = utility.parse_args()
        self.text_recognizer = TextRecognizer(args)
        self.text_detector = TextDetector(args)

    def apply_ocr(self, img):
        # Detect text regions
        dt_boxes, _ = self.text_detector(img)

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

        rec_res, _ = self.text_recognizer(img_list)

        # Postprocess
        total_text = ""
        for i in range(len(rec_res)):
            total_text += rec_res[i][0] + " "

        total_text = total_text.strip()
        return total_text


def main():
    import numpy as np
    from PIL import Image

    image_url = "https://i.ibb.co/kQvHGjj/aewrg.png"
    response = requests.get(image_url)
    img = np.array(Image.open(BytesIO(response.content)).convert("RGB"))

    depremOCR = DepremOCR()

    t0 = time.time()
    epoch = 1
    for _ in range(epoch):
        ocr_text = depremOCR.apply_ocr(img)
    print("Elapsed time:", (time.time() - t0) * 1000 / epoch, "ms")

    print("Output:", ocr_text)


if __name__ == "__main__":
    main()
