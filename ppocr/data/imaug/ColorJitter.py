from paddle.vision.transforms import ColorJitter as pp_ColorJitter

__all__ = ["ColorJitter"]


class ColorJitter(object):
    def __init__(self, brightness=0, contrast=0, saturation=0, hue=0, **kwargs):
        self.aug = pp_ColorJitter(brightness, contrast, saturation, hue)

    def __call__(self, data):
        image = data["image"]
        image = self.aug(image)
        data["image"] = image
        return data
