import os
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.insert(0, os.path.abspath(os.path.join(__dir__, "../..")))

os.environ["FLAGS_allocator_strategy"] = "auto_growth"

import json
import sys
import time

import cv2
import numpy as np

import utility
from postprocess import build_post_process
from ppocr.data import create_operators, transform


class TextDetector(object):
    def __init__(self, args):
        self.args = args
        self.det_algorithm = args.det_algorithm
        self.use_onnx = args.use_onnx
        pre_process_list = [
            {
                "DetResizeForTest": {
                    "limit_side_len": args.det_limit_side_len,
                    "limit_type": args.det_limit_type,
                }
            },
            {
                "NormalizeImage": {
                    "std": [0.229, 0.224, 0.225],
                    "mean": [0.485, 0.456, 0.406],
                    "scale": "1./255.",
                    "order": "hwc",
                }
            },
            {"ToCHWImage": None},
            {"KeepKeys": {"keep_keys": ["image", "shape"]}},
        ]
        postprocess_params = {}
        if self.det_algorithm == "DB":
            postprocess_params["name"] = "DBPostProcess"
            postprocess_params["thresh"] = args.det_db_thresh
            postprocess_params["box_thresh"] = args.det_db_box_thresh
            postprocess_params["max_candidates"] = 1000
            postprocess_params["unclip_ratio"] = args.det_db_unclip_ratio
            postprocess_params["use_dilation"] = args.use_dilation
            postprocess_params["score_mode"] = args.det_db_score_mode
        elif self.det_algorithm == "EAST":
            postprocess_params["name"] = "EASTPostProcess"
            postprocess_params["score_thresh"] = args.det_east_score_thresh
            postprocess_params["cover_thresh"] = args.det_east_cover_thresh
            postprocess_params["nms_thresh"] = args.det_east_nms_thresh
        elif self.det_algorithm == "SAST":
            pre_process_list[0] = {
                "DetResizeForTest": {"resize_long": args.det_limit_side_len}
            }
            postprocess_params["name"] = "SASTPostProcess"
            postprocess_params["score_thresh"] = args.det_sast_score_thresh
            postprocess_params["nms_thresh"] = args.det_sast_nms_thresh
            self.det_sast_polygon = args.det_sast_polygon
            if self.det_sast_polygon:
                postprocess_params["sample_pts_num"] = 6
                postprocess_params["expand_scale"] = 1.2
                postprocess_params["shrink_ratio_of_width"] = 0.2
            else:
                postprocess_params["sample_pts_num"] = 2
                postprocess_params["expand_scale"] = 1.0
                postprocess_params["shrink_ratio_of_width"] = 0.3
        elif self.det_algorithm == "PSE":
            postprocess_params["name"] = "PSEPostProcess"
            postprocess_params["thresh"] = args.det_pse_thresh
            postprocess_params["box_thresh"] = args.det_pse_box_thresh
            postprocess_params["min_area"] = args.det_pse_min_area
            postprocess_params["box_type"] = args.det_pse_box_type
            postprocess_params["scale"] = args.det_pse_scale
            self.det_pse_box_type = args.det_pse_box_type
        elif self.det_algorithm == "FCE":
            pre_process_list[0] = {"DetResizeForTest": {"rescale_img": [1080, 736]}}
            postprocess_params["name"] = "FCEPostProcess"
            postprocess_params["scales"] = args.scales
            postprocess_params["alpha"] = args.alpha
            postprocess_params["beta"] = args.beta
            postprocess_params["fourier_degree"] = args.fourier_degree
            postprocess_params["box_type"] = args.det_fce_box_type

        self.preprocess_op = create_operators(pre_process_list)
        self.postprocess_op = build_post_process(postprocess_params)
        (
            self.predictor,
            self.input_tensor,
            self.output_tensors,
            self.config,
        ) = utility.create_predictor(args, "det")

        if self.use_onnx:
            img_h, img_w = self.input_tensor.shape[2:]
            if img_h is not None and img_w is not None and img_h > 0 and img_w > 0:
                pre_process_list[0] = {
                    "DetResizeForTest": {"image_shape": [img_h, img_w]}
                }
        self.preprocess_op = create_operators(pre_process_list)

    def order_points_clockwise(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def clip_det_res(self, points, img_height, img_width):
        for pno in range(points.shape[0]):
            points[pno, 0] = int(min(max(points[pno, 0], 0), img_width - 1))
            points[pno, 1] = int(min(max(points[pno, 1], 0), img_height - 1))
        return points

    def filter_tag_det_res(self, dt_boxes, image_shape):
        img_height, img_width = image_shape[0:2]
        dt_boxes_new = []
        for box in dt_boxes:
            box = self.order_points_clockwise(box)
            box = self.clip_det_res(box, img_height, img_width)
            rect_width = int(np.linalg.norm(box[0] - box[1]))
            rect_height = int(np.linalg.norm(box[0] - box[3]))
            if rect_width <= 3 or rect_height <= 3:
                continue
            dt_boxes_new.append(box)
        dt_boxes = np.array(dt_boxes_new)
        return dt_boxes

    def filter_tag_det_res_only_clip(self, dt_boxes, image_shape):
        img_height, img_width = image_shape[0:2]
        dt_boxes_new = []
        for box in dt_boxes:
            box = self.clip_det_res(box, img_height, img_width)
            dt_boxes_new.append(box)
        dt_boxes = np.array(dt_boxes_new)
        return dt_boxes

    def __call__(self, img):
        ori_im = img.copy()
        data = {"image": img}

        st = time.time()

        data = transform(data, self.preprocess_op)
        img, shape_list = data
        if img is None:
            return None, 0
        img = np.expand_dims(img, axis=0)
        shape_list = np.expand_dims(shape_list, axis=0)
        img = img.copy()

        if self.use_onnx:
            input_dict = {}
            input_dict[self.input_tensor.name] = img
            outputs = self.predictor.run(self.output_tensors, input_dict)
        else:
            self.input_tensor.copy_from_cpu(img)
            self.predictor.run()
            outputs = []
            for output_tensor in self.output_tensors:
                output = output_tensor.copy_to_cpu()
                outputs.append(output)

        preds = {}
        if self.det_algorithm == "EAST":
            preds["f_geo"] = outputs[0]
            preds["f_score"] = outputs[1]
        elif self.det_algorithm == "SAST":
            preds["f_border"] = outputs[0]
            preds["f_score"] = outputs[1]
            preds["f_tco"] = outputs[2]
            preds["f_tvo"] = outputs[3]
        elif self.det_algorithm in ["DB", "PSE"]:
            preds["maps"] = outputs[0]
        elif self.det_algorithm == "FCE":
            for i, output in enumerate(outputs):
                preds["level_{}".format(i)] = output
        else:
            raise NotImplementedError

        # self.predictor.try_shrink_memory()
        post_result = self.postprocess_op(preds, shape_list)
        dt_boxes = post_result[0]["points"]
        if (self.det_algorithm == "SAST" and self.det_sast_polygon) or (
            self.det_algorithm in ["PSE", "FCE"]
            and self.postprocess_op.box_type == "poly"
        ):
            dt_boxes = self.filter_tag_det_res_only_clip(dt_boxes, ori_im.shape)
        else:
            dt_boxes = self.filter_tag_det_res(dt_boxes, ori_im.shape)

        et = time.time()
        return dt_boxes, et - st


if __name__ == "__main__":
    args = utility.parse_args()
    image_file_list = ["images/y.png"]
    text_detector = TextDetector(args)
    count = 0
    total_time = 0
    draw_img_save = "./inference_results"

    if args.warmup:
        img = np.random.uniform(0, 255, [640, 640, 3]).astype(np.uint8)
        for i in range(2):
            res = text_detector(img)

    if not os.path.exists(draw_img_save):
        os.makedirs(draw_img_save)

    save_results = []
    for image_file in image_file_list:
        img = cv2.imread(image_file)

        for _ in range(10):
            st = time.time()
            dt_boxes, _ = text_detector(img)
            elapse = time.time() - st
            print(elapse * 1000)
        if count > 0:
            total_time += elapse
        count += 1
        save_pred = (
            os.path.basename(image_file)
            + "\t"
            + str(json.dumps([x.tolist() for x in dt_boxes]))
            + "\n"
        )
        save_results.append(save_pred)
        src_im = utility.draw_text_det_res(dt_boxes, image_file)
        img_name_pure = os.path.split(image_file)[-1]
        img_path = os.path.join(draw_img_save, "det_res_{}".format(img_name_pure))
        cv2.imwrite(img_path, src_im)

    with open(os.path.join(draw_img_save, "det_results.txt"), "w") as f:
        f.writelines(save_results)
        f.close()