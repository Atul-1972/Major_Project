"""Declared E1-E4 model constructors, shared by fitting, smoke and evaluation."""

from .cnn import build_cnn
from .transformer import build_transformer
from .fusion import build_fusion


ARCHITECTURES = {'E1': 'efficientnet_v2_s', 'E2': 'swin_t', 'E3': 'fusion_concat', 'E4': 'fusion_attention'}


def build_model(config, num_classes=7, *, pretrained=True):
    experiment = config['experiment']
    if ARCHITECTURES.get(experiment) != config['architecture']:
        raise ValueError('Experiment and architecture do not match the declared protocol')
    if experiment == 'E1':
        return build_cnn(num_classes, pretrained=pretrained)
    if experiment == 'E2':
        return build_transformer(num_classes, pretrained=pretrained)
    return build_fusion(num_classes, attention=experiment == 'E4', pretrained=pretrained)
