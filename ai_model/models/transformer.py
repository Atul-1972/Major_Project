"""Swin-T pooled features and E2 classifier; no trained lesion weights supplied."""

from torch import nn
from torchvision.models import Swin_T_Weights, swin_t

from .weights import DEFAULT_CACHE, load_official_weights


WEIGHTS = Swin_T_Weights.IMAGENET1K_V1


class SwinClassifier(nn.Module):
    def __init__(self, backbone, classes):
        super().__init__()
        self.feature_dimension = backbone.head.in_features
        self.features = nn.Sequential(backbone.features, backbone.norm, backbone.permute, backbone.avgpool, backbone.flatten)
        self.classifier = nn.Linear(self.feature_dimension, classes)

    def forward(self, images):
        return self.classifier(self.features(images))


def build_transformer(num_classes=7, *, pretrained=True, cache_dir=DEFAULT_CACHE):
    if num_classes < 2:
        raise ValueError('At least two classes are required')
    backbone = swin_t(weights=None)
    initialization = {'architecture': 'swin_t', 'weights_enum': None, 'sha256': None, 'url': None}
    if pretrained:
        initialization.update(load_official_weights(backbone, WEIGHTS, cache_dir))
    return SwinClassifier(backbone, num_classes), initialization
