from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from __future__ import annotations
import _io
import math as math
import os as os
import pickle as pickle
from rdkit.sping.PIL.pidPIL import PILCanvas
from rdkit.sping.PIL.pidPIL import test
from rdkit.sping.PIL.pidPIL import test2
from rdkit.sping.PIL.pidPIL import testit
import rdkit.sping.colors
from rdkit.sping.colors import Color
from rdkit.sping.colors import HexColor
from rdkit.sping.pid import AffineMatrix
from rdkit.sping.pid import Canvas
from rdkit.sping.pid import Font
from rdkit.sping.pid import StateSaver
from rdkit.sping.pid import getFileObject
from .pidPIL import *
__all__: list[str] = ['AffineMatrix', 'Canvas', 'Color', 'Font', 'HexColor', 'Image', 'ImageDraw', 'ImageFont', 'PILCanvas', 'StateSaver', 'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond', 'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'cm', 'coral', 'cornflower', 'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgreen', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkturquoise', 'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dodgerblue', 'f', 'figureArc', 'figureCurve', 'figureLine', 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia', 'gainsboro', 'getFileObject', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'green', 'greenyellow', 'grey', 'honeydew', 'hotpink', 'inch', 'indianred', 'indigo', 'ivory', 'keyBksp', 'keyClear', 'keyDel', 'keyDown', 'keyEnd', 'keyHome', 'keyLeft', 'keyPgDn', 'keyPgUp', 'keyRight', 'keyTab', 'keyUp', 'khaki', 'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow', 'lightgreen', 'lightgrey', 'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue', 'lightslategray', 'lightsteelblue', 'lightyellow', 'lime', 'limegreen', 'linen', 'magenta', 'maroon', 'math', 'mediumaquamarine', 'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen', 'mediumturquoise', 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'modControl', 'modShift', 'navajowhite', 'navy', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'os', 'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred', 'papayawhip', 'peachpuff', 'peru', 'pickle', 'pidPIL', 'pink', 'plum', 'powderblue', 'purple', 'red', 'rosybrown', 'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver', 'skyblue', 'slateblue', 'slategray', 'snow', 'springgreen', 'steelblue', 'tan', 'teal', 'test', 'test2', 'testit', 'thistle', 'tomato', 'transparent', 'turquoise', 'violet', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen']
aliceblue: rdkit.sping.colors.Color
antiquewhite: rdkit.sping.colors.Color
aqua: rdkit.sping.colors.Color
aquamarine: rdkit.sping.colors.Color
azure: rdkit.sping.colors.Color
beige: rdkit.sping.colors.Color
bisque: rdkit.sping.colors.Color
black: rdkit.sping.colors.Color
blanchedalmond: rdkit.sping.colors.Color
blue: rdkit.sping.colors.Color
blueviolet: rdkit.sping.colors.Color
brown: rdkit.sping.colors.Color
burlywood: rdkit.sping.colors.Color
cadetblue: rdkit.sping.colors.Color
chartreuse: rdkit.sping.colors.Color
chocolate: rdkit.sping.colors.Color
cm: float = 28.346456692913385
coral: rdkit.sping.colors.Color
cornflower: rdkit.sping.colors.Color
cornsilk: rdkit.sping.colors.Color
crimson: rdkit.sping.colors.Color
cyan: rdkit.sping.colors.Color
darkblue: rdkit.sping.colors.Color
darkcyan: rdkit.sping.colors.Color
darkgoldenrod: rdkit.sping.colors.Color
darkgray: rdkit.sping.colors.Color
darkgreen: rdkit.sping.colors.Color
darkkhaki: rdkit.sping.colors.Color
darkmagenta: rdkit.sping.colors.Color
darkolivegreen: rdkit.sping.colors.Color
darkorange: rdkit.sping.colors.Color
darkorchid: rdkit.sping.colors.Color
darkred: rdkit.sping.colors.Color
darksalmon: rdkit.sping.colors.Color
darkseagreen: rdkit.sping.colors.Color
darkslateblue: rdkit.sping.colors.Color
darkslategray: rdkit.sping.colors.Color
darkturquoise: rdkit.sping.colors.Color
darkviolet: rdkit.sping.colors.Color
deeppink: rdkit.sping.colors.Color
deepskyblue: rdkit.sping.colors.Color
dimgray: rdkit.sping.colors.Color
dodgerblue: rdkit.sping.colors.Color
f: _io.BufferedReader
figureArc: int = 2
figureCurve: int = 3
figureLine: int = 1
firebrick: rdkit.sping.colors.Color
floralwhite: rdkit.sping.colors.Color
forestgreen: rdkit.sping.colors.Color
fuchsia: rdkit.sping.colors.Color
gainsboro: rdkit.sping.colors.Color
ghostwhite: rdkit.sping.colors.Color
gold: rdkit.sping.colors.Color
goldenrod: rdkit.sping.colors.Color
gray: rdkit.sping.colors.Color
green: rdkit.sping.colors.Color
greenyellow: rdkit.sping.colors.Color
grey: rdkit.sping.colors.Color
honeydew: rdkit.sping.colors.Color
hotpink: rdkit.sping.colors.Color
inch: int = 72
indianred: rdkit.sping.colors.Color
indigo: rdkit.sping.colors.Color
ivory: rdkit.sping.colors.Color
keyBksp: str = '\x08'
keyClear: str = '\x1b'
keyDel: str = '\x7f'
keyDown: str = '\x1f'
keyEnd: str = '\x04'
keyHome: str = '\x01'
keyLeft: str = '\x1c'
keyPgDn: str = '\x0c'
keyPgUp: str = '\x0b'
keyRight: str = '\x1d'
keyTab: str = '\t'
keyUp: str = '\x1e'
khaki: rdkit.sping.colors.Color
lavender: rdkit.sping.colors.Color
lavenderblush: rdkit.sping.colors.Color
lawngreen: rdkit.sping.colors.Color
lemonchiffon: rdkit.sping.colors.Color
lightblue: rdkit.sping.colors.Color
lightcoral: rdkit.sping.colors.Color
lightcyan: rdkit.sping.colors.Color
lightgoldenrodyellow: rdkit.sping.colors.Color
lightgreen: rdkit.sping.colors.Color
lightgrey: rdkit.sping.colors.Color
lightpink: rdkit.sping.colors.Color
lightsalmon: rdkit.sping.colors.Color
lightseagreen: rdkit.sping.colors.Color
lightskyblue: rdkit.sping.colors.Color
lightslategray: rdkit.sping.colors.Color
lightsteelblue: rdkit.sping.colors.Color
lightyellow: rdkit.sping.colors.Color
lime: rdkit.sping.colors.Color
limegreen: rdkit.sping.colors.Color
linen: rdkit.sping.colors.Color
magenta: rdkit.sping.colors.Color
maroon: rdkit.sping.colors.Color
mediumaquamarine: rdkit.sping.colors.Color
mediumblue: rdkit.sping.colors.Color
mediumorchid: rdkit.sping.colors.Color
mediumpurple: rdkit.sping.colors.Color
mediumseagreen: rdkit.sping.colors.Color
mediumslateblue: rdkit.sping.colors.Color
mediumspringgreen: rdkit.sping.colors.Color
mediumturquoise: rdkit.sping.colors.Color
mediumvioletred: rdkit.sping.colors.Color
midnightblue: rdkit.sping.colors.Color
mintcream: rdkit.sping.colors.Color
mistyrose: rdkit.sping.colors.Color
moccasin: rdkit.sping.colors.Color
modControl: int = 2
modShift: int = 1
navajowhite: rdkit.sping.colors.Color
navy: rdkit.sping.colors.Color
oldlace: rdkit.sping.colors.Color
olive: rdkit.sping.colors.Color
olivedrab: rdkit.sping.colors.Color
orange: rdkit.sping.colors.Color
orangered: rdkit.sping.colors.Color
orchid: rdkit.sping.colors.Color
palegoldenrod: rdkit.sping.colors.Color
palegreen: rdkit.sping.colors.Color
paleturquoise: rdkit.sping.colors.Color
palevioletred: rdkit.sping.colors.Color
papayawhip: rdkit.sping.colors.Color
peachpuff: rdkit.sping.colors.Color
peru: rdkit.sping.colors.Color
pink: rdkit.sping.colors.Color
plum: rdkit.sping.colors.Color
powderblue: rdkit.sping.colors.Color
purple: rdkit.sping.colors.Color
red: rdkit.sping.colors.Color
rosybrown: rdkit.sping.colors.Color
royalblue: rdkit.sping.colors.Color
saddlebrown: rdkit.sping.colors.Color
salmon: rdkit.sping.colors.Color
sandybrown: rdkit.sping.colors.Color
seagreen: rdkit.sping.colors.Color
seashell: rdkit.sping.colors.Color
sienna: rdkit.sping.colors.Color
silver: rdkit.sping.colors.Color
skyblue: rdkit.sping.colors.Color
slateblue: rdkit.sping.colors.Color
slategray: rdkit.sping.colors.Color
snow: rdkit.sping.colors.Color
springgreen: rdkit.sping.colors.Color
steelblue: rdkit.sping.colors.Color
tan: rdkit.sping.colors.Color
teal: rdkit.sping.colors.Color
thistle: rdkit.sping.colors.Color
tomato: rdkit.sping.colors.Color
transparent: rdkit.sping.colors.Color
turquoise: rdkit.sping.colors.Color
violet: rdkit.sping.colors.Color
wheat: rdkit.sping.colors.Color
white: rdkit.sping.colors.Color
whitesmoke: rdkit.sping.colors.Color
yellow: rdkit.sping.colors.Color
yellowgreen: rdkit.sping.colors.Color
