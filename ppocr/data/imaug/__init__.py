from __future__ import absolute_import, division, print_function, unicode_literals

from .ColorJitter import ColorJitter
from .copy_paste import CopyPaste
from .east_process import *
from .fce_aug import *
from .fce_targets import FCENetTargets
from .gen_table_mask import *
from .iaa_augment import IaaAugment
from .label_ops import *
from .make_border_map import MakeBorderMap
from .make_pse_gt import MakePseGt
from .make_shrink_map import MakeShrinkMap
from .operators import *
from .pg_process import *
from .randaugment import RandAugment
from .random_crop_data import EastRandomCropData, RandomCropImgMask
from .rec_img_aug import (
    ClsResizeImg,
    NRTRRecResizeImg,
    PRENResizeImg,
    RecAug,
    RecConAug,
    RecResizeImg,
    SARRecResizeImg,
    SRNRecResizeImg,
)
from .sast_process import *
from .ssl_img_aug import SSLRotateResize
from .vqa import *


def transform(data, ops=None):
    """transform"""
    if ops is None:
        ops = []
    for op in ops:
        data = op(data)
        if data is None:
            return None
    return data


def create_operators(op_param_list, global_config=None):
    """
    create operators based on the config

    Args:
        params(list): a dict list, used to create some operators
    """
    assert isinstance(op_param_list, list), "operator config should be a list"
    ops = []
    for operator in op_param_list:
        assert isinstance(operator, dict) and len(operator) == 1, "yaml format error"
        op_name = list(operator)[0]
        param = {} if operator[op_name] is None else operator[op_name]
        if global_config is not None:
            param.update(global_config)
        op = eval(op_name)(**param)
        ops.append(op)
    return ops
