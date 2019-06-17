"""
FCN - Fully Convolutional Neural Networks
Paper: https://people.eecs.berkeley.edu/~jonlong/long_shelhamer_fcn.pdf
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from collections import OrderedDict

from scratchai import nets
from scratchai.nets.common import InterLayer


__all__ = ['FCNHead', 'fcn_alexnet', 'fcn_resnet50', 'fcn_resnet101']


class FCNHead(nn.Module):
  def __init__(self, ic:int, oc:int=21, compress:int=4):
    super().__init__()
    inter_channels = ic // compress

    self.net = nn.Sequential(
      nn.Conv2d(ic, inter_channels, 3, 1, 1, bias=False),
      nn.BatchNorm2d(inter_channels),
      nn.ReLU(inplace=True),
      nn.Dropout(p=0.1),
      nn.Conv2d(inter_channels, oc, 1, 1, 0)
    )

  def forward(self, x): return self.net(x)


class FCN(nn.Module):
  """
  Implementation of the FCN model.

  Arguemnts
  ---------

  """
  def __init__(self, head_ic:int, nc=21, backbone=None, aux_classifier=None):
    super().__init__()
    self.backbone = backbone
    self.fcn_head = FCNHead(ic=head_ic, oc=nc)
    self.aux_classifier = aux_classifier

  def forward(self, x):
    out = OrderedDict()
    x_shape = x.shape[-2:]
    features_out = self.backbone(x)

    if self.aux_classifier is not None:
      aux_out = self.aux_classifier(features_out['aux'])
      out['aux'] = F.interpolate(aux_out, size=x_shape, mode='bilinear', 
                                 align_corners=False)

    x = self.fcn_head(features_out['out'])
    out['out'] = F.interpolate(x, size=x_shape, mode='bilinear', 
                               align_corners=False)
    return out


def fcn_alexnet(nc=21, aux:bool=True):
  backbone = InterLayer(nets.alexnet().features, {'9': 'aux', '12': 'out'})
  aux_classifier = FCNHead(ic=256, oc=nc) if aux else None
  return FCN(head_ic=256, backbone=backbone, nc=21, 
             aux_classifier=aux_classifier)


def fcn_resnet50():
  net = nets.resnet50()
  backbone = net.net[:20]
  return FCN(head_ic=2048, backbone=backbone)


def fcn_resnet101():
  net = nets.resnet101()
  backbone = net.net[:37]
  return FCN(head_ic=2048, backbone=backbone)
