import numpy as np
import paddle


def load_vqa_bio_label_maps(label_map_path):
    with open(label_map_path, "r", encoding="utf-8") as fin:
        lines = fin.readlines()
    lines = [line.strip() for line in lines]
    if "O" not in lines:
        lines.insert(0, "O")
    labels = []
    for line in lines:
        if line == "O":
            labels.append("O")
        else:
            labels.append("B-" + line)
            labels.append("I-" + line)
    label2id_map = {label: idx for idx, label in enumerate(labels)}
    id2label_map = {idx: label for idx, label in enumerate(labels)}
    return label2id_map, id2label_map


class VQASerTokenLayoutLMPostProcess(object):
    """Convert between text-label and text-index"""

    def __init__(self, class_path, **kwargs):
        super(VQASerTokenLayoutLMPostProcess, self).__init__()
        label2id_map, self.id2label_map = load_vqa_bio_label_maps(class_path)

        self.label2id_map_for_draw = dict()
        for key in label2id_map:
            if key.startswith("I-"):
                self.label2id_map_for_draw[key] = label2id_map["B" + key[1:]]
            else:
                self.label2id_map_for_draw[key] = label2id_map[key]

        self.id2label_map_for_show = dict()
        for key in self.label2id_map_for_draw:
            val = self.label2id_map_for_draw[key]
            if key == "O":
                self.id2label_map_for_show[val] = key
            if key.startswith("B-") or key.startswith("I-"):
                self.id2label_map_for_show[val] = key[2:]
            else:
                self.id2label_map_for_show[val] = key

    def __call__(self, preds, batch=None, *args, **kwargs):
        if isinstance(preds, paddle.Tensor):
            preds = preds.numpy()

        if batch is not None:
            return self._metric(preds, batch[1])
        else:
            return self._infer(preds, **kwargs)

    def _metric(self, preds, label):
        pred_idxs = preds.argmax(axis=2)
        decode_out_list = [[] for _ in range(pred_idxs.shape[0])]
        label_decode_out_list = [[] for _ in range(pred_idxs.shape[0])]

        for i in range(pred_idxs.shape[0]):
            for j in range(pred_idxs.shape[1]):
                if label[i, j] != -100:
                    label_decode_out_list[i].append(self.id2label_map[label[i, j]])
                    decode_out_list[i].append(self.id2label_map[pred_idxs[i, j]])
        return decode_out_list, label_decode_out_list

    def _infer(self, preds, attention_masks, segment_offset_ids, ocr_infos):
        results = []

        for pred, attention_mask, segment_offset_id, ocr_info in zip(
            preds, attention_masks, segment_offset_ids, ocr_infos
        ):
            pred = np.argmax(pred, axis=1)
            pred = [self.id2label_map[idx] for idx in pred]

            for idx in range(len(segment_offset_id)):
                if idx == 0:
                    start_id = 0
                else:
                    start_id = segment_offset_id[idx - 1]

                end_id = segment_offset_id[idx]

                curr_pred = pred[start_id:end_id]
                curr_pred = [self.label2id_map_for_draw[p] for p in curr_pred]

                if len(curr_pred) <= 0:
                    pred_id = 0
                else:
                    counts = np.bincount(curr_pred)
                    pred_id = np.argmax(counts)
                ocr_info[idx]["pred_id"] = int(pred_id)
                ocr_info[idx]["pred"] = self.id2label_map_for_show[int(pred_id)]
            results.append(ocr_info)
        return results
