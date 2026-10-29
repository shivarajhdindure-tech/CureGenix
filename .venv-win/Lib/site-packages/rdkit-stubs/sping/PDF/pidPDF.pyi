"""
This is the PIDDLE back end for PDF.  It acts as a wrapper
over the pdfgen.Canvas class, and translates between the
PIDDLE graphics state and the PDF/PostScript one. It only
exposes PIDDLE methods; however, it has an attribute
self.pdf which offers numerous lower-level drawing routines.
"""
from __future__ import annotations
from math import cos
from math import sin
import os as os
from rdkit.sping.PDF import pdfgen
from rdkit.sping.PDF import pdfgeom
from rdkit.sping.PDF import pdfmetrics
import rdkit.sping.colors
from rdkit.sping.colors import Color
from rdkit.sping.colors import HexColor
from rdkit.sping import pagesizes
import rdkit.sping.pid
from rdkit.sping.pid import AffineMatrix
from rdkit.sping.pid import Canvas
from rdkit.sping.pid import Font
from rdkit.sping.pid import StateSaver
from rdkit.sping.pid import getFileObject
__all__: list[str] = ['AffineMatrix', 'Canvas', 'Color', 'DEFAULT_PAGE_SIZE', 'Font', 'HexColor', 'PDFCanvas', 'StateSaver', 'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond', 'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'cm', 'coral', 'cornflower', 'cornsilk', 'cos', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgreen', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkturquoise', 'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dodgerblue', 'figureArc', 'figureCurve', 'figureLine', 'firebrick', 'floralwhite', 'font_face_map', 'forestgreen', 'fuchsia', 'gainsboro', 'getFileObject', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'green', 'greenyellow', 'grey', 'honeydew', 'hotpink', 'inch', 'indianred', 'indigo', 'ivory', 'keyBksp', 'keyClear', 'keyDel', 'keyDown', 'keyEnd', 'keyHome', 'keyLeft', 'keyPgDn', 'keyPgUp', 'keyRight', 'keyTab', 'keyUp', 'khaki', 'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow', 'lightgreen', 'lightgrey', 'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue', 'lightslategray', 'lightsteelblue', 'lightyellow', 'lime', 'limegreen', 'linen', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen', 'mediumturquoise', 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'modControl', 'modShift', 'navajowhite', 'navy', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'os', 'pagesizes', 'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred', 'papayawhip', 'pdfgen', 'pdfgeom', 'pdfmetrics', 'peachpuff', 'peru', 'pi', 'pink', 'plum', 'powderblue', 'ps_font_map', 'purple', 'red', 'rosybrown', 'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver', 'sin', 'skyblue', 'slateblue', 'slategray', 'snow', 'springgreen', 'steelblue', 'tan', 'teal', 'test', 'thistle', 'tomato', 'transparent', 'turquoise', 'violet', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen']
class PDFCanvas(rdkit.sping.pid.Canvas):
    """
    This works by accumulating a list of strings containing
          PDF page marking operators, as you call its methods.  We could
          use a big string but this is more efficient - only concatenate
          it once, with control over line ends.  When
          done, it hands off the stream to a PDFPage object.
    """
    def __init__(self, size = None, name = 'pidPDF.pdf', pagesize = (595.275590551181, 841.8897637795275)):
        ...
    def __setattr__(self, key, value):
        ...
    def _endPath(self, path, edgeColor, fillColor):
        """
        in PIDDLE, the edge and fil colors might be transparent,
                    and might also be None, in which case they should be taken
                    from the defaults.  This leads to a standard 10 lines of code
                    when closing each shape, which are wrapped up here.  Use
                    these if you implement new PIDDLE shapes.
        """
    def _escape(self, s):
        """
        PDF escapes are like Python ones, but brackets need slashes before them too.
                    Use Python's repr function and chop off the quotes first
        """
    def _findPostScriptFontName(self, font):
        """
        Attempts to return proper font name.
        """
    def _resetDefaults(self):
        """
        Only used in setup - persist from page to page
        """
    def _updateFillColor(self, color):
        """
        Triggered when someone assigns to defaultFillColor
        """
    def _updateFont(self, font):
        """
        Triggered when someone assigns to defaultFont
        """
    def _updateLineColor(self, color):
        """
        Triggered when someone assigns to defaultLineColor
        """
    def _updateLineWidth(self, width):
        """
        Triggered when someone assigns to defaultLineWidth
        """
    def canUpdate(self):
        ...
    def clear(self):
        """
        Not wll defined for file formats, use same as ShowPage
        """
    def drawArc(self, x1, y1, x2, y2, startAng = 0, extent = 90, edgeColor = None, edgeWidth = None, fillColor = None, dash = None, **kwargs):
        """
        This draws a PacMan-type shape connected to the centre.  One
                    idiosyncrasy - if you specify an edge color, it apples to the
                    outer curved rim but not the radial edges.
        """
    def drawCurve(self, x1, y1, x2, y2, x3, y3, x4, y4, edgeColor = None, edgeWidth = None, fillColor = None, closed = 0, dash = None, **kwargs):
        """
        This could do two totally different things.  If not closed,
                    just does a bezier curve so fill is irrelevant.  If closed,
                    it is actually a filled shape.
        """
    def drawEllipse(self, x1, y1, x2, y2, edgeColor = None, edgeWidth = None, fillColor = None, dash = None, **kwargs):
        ...
    def drawImage(self, image, x1, y1, x2 = None, y2 = None, **kwargs):
        """
        Draw a PIL Image or image filename into the specified rectangle.
                    If x2 and y2 are omitted, they are calculated from the image size.
                    
        """
    def drawLine(self, x1, y1, x2, y2, color = None, width = None, dash = None, **kwargs):
        """
        Calls the underlying methods in pdfgen.canvas.  For the
                    highest performance, use canvas.setDefaultFont and
                    canvas.setLineWidth, and draw batches of similar
                    lines together.
        """
    def drawLines(self, lineList, color = None, width = None, dash = None, **kwargs):
        """
        Draws several distinct lines, all with same color
                    and width, efficiently
        """
    def drawLiteral(self, literal):
        ...
    def drawPolygon(self, pointlist, edgeColor = None, edgeWidth = None, fillColor = None, closed = 0, dash = None, **kwargs):
        """
        As it says.  Easy with paths!
        """
    def drawRect(self, x1, y1, x2, y2, edgeColor = None, edgeWidth = None, fillColor = None, dash = None, **kwargs):
        ...
    def drawString(self, s, x, y, font = None, color = None, angle = 0, **kwargs):
        """
        As it says, but many options to process.  It translates
                    user space rather than text space, in case underlining is
                    needed on rotated text.  It cheats and does literals
                    for efficiency, avoiding changing the python graphics state.
        """
    def flush(self):
        ...
    def fontAscent(self, font = None):
        ...
    def fontDescent(self, font = None):
        ...
    def fontHeight(self, font = None):
        ...
    def isInteractive(self):
        ...
    def resetDefaults(self):
        """
        If you drop down to a lower level, PIDDLE can lose
                    track of the current graphics state.  Calling this after
                    wards ensures that the canvas is updated to the same
                    defaults as PIDDLE thinks they should be.
        """
    def save(self, file = None, format = None):
        """
        Saves the file.  If holding data, do
                    a showPage() to save them having to.
        """
    def setInfoLine(self, s):
        ...
    def showPage(self):
        """
        ensure basic settings are the same after a page break
        """
    def stringWidth(self, s, font = None):
        """
        Return the logical width of the string if it were drawn             in the current font (defaults to self.font).
        """
def test():
    ...
DEFAULT_PAGE_SIZE: tuple = (595.275590551181, 841.8897637795275)
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
figureArc: int = 2
figureCurve: int = 3
figureLine: int = 1
firebrick: rdkit.sping.colors.Color
floralwhite: rdkit.sping.colors.Color
font_face_map: dict = {'serif': 'times', 'sansserif': 'helvetica', 'monospaced': 'courier', 'arial': 'helvetica'}
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
pi: float = 3.141592653589793
pink: rdkit.sping.colors.Color
plum: rdkit.sping.colors.Color
powderblue: rdkit.sping.colors.Color
ps_font_map: dict = {('times', 0, 0): 'Times-Roman', ('times', 1, 0): 'Times-Bold', ('times', 0, 1): 'Times-Italic', ('times', 1, 1): 'Times-BoldItalic', ('courier', 0, 0): 'Courier', ('courier', 1, 0): 'Courier-Bold', ('courier', 0, 1): 'Courier-Oblique', ('courier', 1, 1): 'Courier-BoldOblique', ('helvetica', 0, 0): 'Helvetica', ('helvetica', 1, 0): 'Helvetica-Bold', ('helvetica', 0, 1): 'Helvetica-Oblique', ('helvetica', 1, 1): 'Helvetica-BoldOblique', ('symbol', 0, 0): 'Symbol', ('symbol', 1, 0): 'Symbol', ('symbol', 0, 1): 'Symbol', ('symbol', 1, 1): 'Symbol', ('zapfdingbats', 0, 0): 'ZapfDingbats', ('zapfdingbats', 1, 0): 'ZapfDingbats', ('zapfdingbats', 0, 1): 'ZapfDingbats', ('zapfdingbats', 1, 1): 'ZapfDingbats'}
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
