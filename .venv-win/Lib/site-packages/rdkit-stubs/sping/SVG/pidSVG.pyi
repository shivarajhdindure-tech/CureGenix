"""
piddleSVG

This module implements an SVG PIDDLE canvas.
In other words, this is a PIDDLE backend that renders into a
SVG file.

Bits have been shamelessly cobbled from piddlePDF.py and/or
piddlePS.py

Greg Landrum (greglandrum@earthlink.net) 3/10/2000
"""
from __future__ import annotations
from math import acos
from math import acosh
from math import asin
from math import asinh
from math import atan
from math import atan2
from math import atanh
from math import cbrt
from math import ceil
from math import comb
from math import copysign
from math import cos
from math import cosh
from math import degrees
from math import dist
from math import erf
from math import erfc
from math import exp
from math import exp2
from math import expm1
from math import fabs
from math import factorial
from math import floor
from math import fmod
from math import frexp
from math import fsum
from math import gamma
from math import gcd
from math import hypot
from math import isclose
from math import isfinite
from math import isinf
from math import isnan
from math import isqrt
from math import lcm
from math import ldexp
from math import lgamma
from math import log
from math import log10
from math import log1p
from math import log2
from math import modf
from math import nextafter
from math import perm
from math import pow
from math import prod
from math import radians
from math import remainder
from math import sin
from math import sinh
from math import sqrt
from math import sumprod
from math import tanh
from math import trunc
from math import ulp
from rdkit.sping.PDF import pdfmetrics
import rdkit.sping.colors
from rdkit.sping.colors import Color
from rdkit.sping.colors import HexColor
import rdkit.sping.pid
from rdkit.sping.pid import AffineMatrix
from rdkit.sping.pid import Canvas
from rdkit.sping.pid import Font
from rdkit.sping.pid import StateSaver
from rdkit.sping.pid import getFileObject
__all__: list[str] = ['AffineMatrix', 'Canvas', 'Color', 'Font', 'HexColor', 'SVGCanvas', 'SVG_HEADER', 'StateSaver', 'acos', 'acosh', 'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'asin', 'asinh', 'atan', 'atan2', 'atanh', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond', 'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'cbrt', 'ceil', 'chartreuse', 'chocolate', 'cm', 'comb', 'copysign', 'coral', 'cornflower', 'cornsilk', 'cos', 'cosh', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgreen', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkturquoise', 'darkviolet', 'dashtest', 'deeppink', 'deepskyblue', 'degrees', 'dimgray', 'dist', 'dodgerblue', 'e', 'erf', 'erfc', 'exp', 'exp2', 'expm1', 'fabs', 'factorial', 'figureArc', 'figureCurve', 'figureLine', 'firebrick', 'floor', 'floralwhite', 'fmod', 'forestgreen', 'frexp', 'fsum', 'fuchsia', 'gainsboro', 'gamma', 'gcd', 'getFileObject', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'green', 'greenyellow', 'grey', 'honeydew', 'hotpink', 'hypot', 'inch', 'indianred', 'indigo', 'inf', 'isclose', 'isfinite', 'isinf', 'isnan', 'isqrt', 'ivory', 'keyBksp', 'keyClear', 'keyDel', 'keyDown', 'keyEnd', 'keyHome', 'keyLeft', 'keyPgDn', 'keyPgUp', 'keyRight', 'keyTab', 'keyUp', 'khaki', 'lavender', 'lavenderblush', 'lawngreen', 'lcm', 'ldexp', 'lemonchiffon', 'lgamma', 'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow', 'lightgreen', 'lightgrey', 'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue', 'lightslategray', 'lightsteelblue', 'lightyellow', 'lime', 'limegreen', 'linen', 'log', 'log10', 'log1p', 'log2', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen', 'mediumturquoise', 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'modControl', 'modShift', 'modf', 'nan', 'navajowhite', 'navy', 'nextafter', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred', 'papayawhip', 'pdfmetrics', 'peachpuff', 'perm', 'peru', 'pi', 'pink', 'plum', 'pow', 'powderblue', 'prod', 'purple', 'radians', 'red', 'remainder', 'rosybrown', 'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver', 'sin', 'sinh', 'skyblue', 'slateblue', 'slategray', 'snow', 'springgreen', 'sqrt', 'steelblue', 'sumprod', 'tan', 'tanh', 'tau', 'teal', 'test', 'test2', 'testit', 'thistle', 'tomato', 'transparent', 'trunc', 'turquoise', 'ulp', 'violet', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen']
class SVGCanvas(rdkit.sping.pid.Canvas):
    def _FormArcStr(self, x1, y1, x2, y2, theta1, extent):
        """
         Forms an arc specification for SVG
        
            
        """
    def _FormFontStr(self, font):
        """
         form what we hope is a valid SVG font string.
              Defaults to 'sansserif'
              This should work when an array of font faces are passed in.
            
        """
    def __init__(self, size = (300, 300), name = 'SVGCanvas', includeXMLHeader = True, extraHeaderText = ''):
        ...
    def _drawStringOneLine(self, line, x, y, fontStr, svgColor, **kwargs):
        ...
    def _findExternalFontName(self, font):
        """
        Attempts to return proper font name.
                PDF uses a standard 14 fonts referred to
                by name. Default to self.defaultFont('Helvetica').
                The dictionary allows a layer of indirection to
                support a standard set of sping.pid font names.
        """
    def _initOutput(self, includeXMLHeader = True, extraHeaderText = ''):
        ...
    def clear(self):
        ...
    def drawArc(self, x1, y1, x2, y2, theta1 = 0, extent = 360, edgeColor = None, edgeWidth = None, fillColor = None, dash = None, **kwargs):
        ...
    def drawCurve(self, x1, y1, x2, y2, x3, y3, x4, y4, edgeColor = None, edgeWidth = None, fillColor = ..., closed = 0, dash = None, **kwargs):
        ...
    def drawEllipse(self, x1, y1, x2, y2, edgeColor = None, edgeWidth = None, fillColor = ..., dash = None, **kwargs):
        ...
    def drawFigure(self, partList, edgeColor = None, edgeWidth = None, fillColor = None, closed = 0, dash = None, **kwargs):
        """
        drawFigure(partList) -- draws a complex figure
            partlist: a set of lines, curves, and arcs defined by a tuple whose
            first element is one of figureLine, figureArc, figureCurve
            and whose remaining 4, 6, or 8 elements are parameters.
        """
    def drawImage(self, image, x1, y1, x2 = None, y2 = None, **kwargs):
        """
              to the best of my knowledge, the only real way to get an image
              into SVG is to read it from a file.  So we'll save out to a PNG
              file, then set a link to that in the SVG.
            
        """
    def drawLine(self, x1, y1, x2, y2, color = None, width = None, dash = None, **kwargs):
        """
        Draw a straight line between x1,y1 and x2,y2.
        """
    def drawPolygon(self, pointlist, edgeColor = None, edgeWidth = None, fillColor = ..., closed = 0, dash = None, **kwargs):
        """
        drawPolygon(pointlist) -- draws a polygon
            pointlist: a list of (x,y) tuples defining vertices
            
        """
    def drawString(self, s, x, y, font = None, color = None, angle = 0, **kwargs):
        ...
    def flush(self):
        ...
    def fontAscent(self, font = None):
        ...
    def fontDescent(self, font = None):
        ...
    def save(self, file = None, format = None):
        """
        Hand hand this either a file= <filename> or
            file = <an open file object>.  By default, I've made the fomrat extension be
            .svg.  By default it saves the file to "self.name" + '.svg' 
        """
    def stringWidth(self, s, font = None):
        """
        Return the logical width of the string if it were drawn     in the current font (defaults to self.font).
        """
    def text(self):
        ...
def _ColorToSVG(color):
    """
     convenience function for converting a sping.pid color to an SVG color
    
      
    """
def _PointListToSVG(points, dupFirst = 0):
    """
     convenience function for converting a list of points to a string
          suitable for passing to SVG path operations
    
      
    """
def dashtest():
    ...
def test():
    ...
def test2():
    ...
def testit(canvas, s, x, y, font = None):
    ...
SVG_HEADER: str = '<?xml version="1.0" encoding="iso-8859-1"?>\n'
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
e: float = 2.718281828459045
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
inf: float
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
nan: float
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
pi: float = 3.141592653589793
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
tau: float = 6.283185307179586
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
