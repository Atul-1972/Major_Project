"""E3 concatenation and E4 two-token attention on CNN/Transformer features."""

import hashlib
import json

import torch
from torch import nn

from .cnn import build_cnn
from .transformer import build_transformer


class DualFeatures(nn.Module):
    def __init__(self, cnn, transformer):
        super().__init__()
        self.cnn = nn.Sequential(cnn.features, cnn.avgpool, nn.Flatten(1))
        self.transformer = transformer.features

    def forward(self, images):
        return self.cnn(images), self.transformer(images)


class ConcatHead(nn.Module):
    def __init__(self, cnn_dim, transformer_dim, classes):
        super().__init__()
        self.head = nn.Sequential(nn.Dropout(0.2), nn.Linear(cnn_dim + transformer_dim, classes))

    def forward(self, features):
        return self.head(torch.cat(features, dim=1))


class AttentionHead(nn.Module):
    def __init__(self, cnn_dim, transformer_dim, classes, dimension=256, heads=4):
        super().__init__()
        self.cnn_projection = nn.Linear(cnn_dim, dimension)
        self.transformer_projection = nn.Linear(transformer_dim, dimension)
        self.branch_embeddings = nn.Parameter(torch.zeros(1, 2, dimension))
        nn.init.normal_(self.branch_embeddings, std=0.02)
        self.attention = nn.MultiheadAttention(dimension, heads, batch_first=True)
        self.norm = nn.LayerNorm(dimension)
        self.head = nn.Sequential(nn.Dropout(0.2), nn.Linear(dimension, classes))

    def forward(self, features):
        tokens = torch.stack((self.cnn_projection(features[0]), self.transformer_projection(features[1])), dim=1)
        tokens = tokens + self.branch_embeddings
        attended, _ = self.attention(tokens, tokens, tokens, need_weights=True)
        return self.head(self.norm(tokens + attended).mean(dim=1))


class FusionClassifier(nn.Module):
    def __init__(self, cnn, transformer, classes, attention=False):
        super().__init__()
        cnn_dim = cnn.classifier[-1].in_features
        transformer_dim = transformer.feature_dimension
        self.features = DualFeatures(cnn, transformer)
        self.classifier = (AttentionHead if attention else ConcatHead)(cnn_dim, transformer_dim, classes)

    def forward(self, images):
        return self.classifier(self.features(images))


def build_fusion(num_classes=7, *, attention=False, pretrained=True):
    cnn, cnn_init = build_cnn(num_classes, pretrained=pretrained)
    transformer, transformer_init = build_transformer(num_classes, pretrained=pretrained)
    branches = {'cnn': cnn_init, 'transformer': transformer_init}
    digest = hashlib.sha256(json.dumps(branches, sort_keys=True).encode()).hexdigest() if pretrained else None
    initialization = {'architecture': 'fusion_attention' if attention else 'fusion_concat', 'branches': branches,
                      'sha256': digest, 'digest_scope': 'canonical branch initialization metadata; branch file hashes stored separately',
                      'weights_enum': 'IMAGENET1K_V1 for both branches' if pretrained else None}
    return FusionClassifier(cnn, transformer, num_classes, attention), initialization
