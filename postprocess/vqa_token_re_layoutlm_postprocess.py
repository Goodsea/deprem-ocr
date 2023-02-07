class VQAReTokenLayoutLMPostProcess(object):
    """Convert between text-label and text-index"""

    def __init__(self, **kwargs):
        super(VQAReTokenLayoutLMPostProcess, self).__init__()

    def __call__(self, preds, label=None, *args, **kwargs):
        if label is not None:
            return self._metric(preds, label)
        else:
            return self._infer(preds, *args, **kwargs)

    def _metric(self, preds, label):
        return preds["pred_relations"], label[6], label[5]

    def _infer(self, preds, *args, **kwargs):
        ser_results = kwargs["ser_results"]
        entity_idx_dict_batch = kwargs["entity_idx_dict_batch"]
        pred_relations = preds["pred_relations"]

        # merge relations and ocr info
        results = []
        for pred_relation, ser_result, entity_idx_dict in zip(
            pred_relations, ser_results, entity_idx_dict_batch
        ):
            result = []
            used_tail_id = []
            for relation in pred_relation:
                if relation["tail_id"] in used_tail_id:
                    continue
                used_tail_id.append(relation["tail_id"])
                ocr_info_head = ser_result[entity_idx_dict[relation["head_id"]]]
                ocr_info_tail = ser_result[entity_idx_dict[relation["tail_id"]]]
                result.append((ocr_info_head, ocr_info_tail))
            results.append(result)
        return results
