import numbers
from collections import defaultdict

import numpy as np
import paddle


class DictCollator(object):
    """
    data batch
    """

    def __call__(self, batch):
        # todo：support batch operators
        data_dict = defaultdict(list)
        to_tensor_keys = []
        for sample in batch:
            for k, v in sample.items():
                if isinstance(v, (np.ndarray, paddle.Tensor, numbers.Number)):
                    if k not in to_tensor_keys:
                        to_tensor_keys.append(k)
                data_dict[k].append(v)
        for k in to_tensor_keys:
            data_dict[k] = paddle.to_tensor(data_dict[k])
        return data_dict


class ListCollator(object):
    """
    data batch
    """

    def __call__(self, batch):
        # todo：support batch operators
        data_dict = defaultdict(list)
        to_tensor_idxs = []
        for sample in batch:
            for idx, v in enumerate(sample):
                if isinstance(v, (np.ndarray, paddle.Tensor, numbers.Number)):
                    if idx not in to_tensor_idxs:
                        to_tensor_idxs.append(idx)
                data_dict[idx].append(v)
        for idx in to_tensor_idxs:
            data_dict[idx] = paddle.to_tensor(data_dict[idx])
        return list(data_dict.values())


class SSLRotateCollate(object):
    """
    bach: [
        [(4*3xH*W), (4,)]
        [(4*3xH*W), (4,)]
        ...
    ]
    """

    def __call__(self, batch):
        output = [np.concatenate(d, axis=0) for d in zip(*batch)]
        return output
