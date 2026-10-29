"""
piddlePS - a PostScript backend for the PIDDLE drawing module

   Magnus Lie Hetland

   1999
"""
from __future__ import annotations
from _io import StringIO
import math as math
from rdkit.sping.PS import psmetrics
import rdkit.sping.colors
from rdkit.sping.colors import Color
from rdkit.sping.colors import HexColor
import rdkit.sping.pid
from rdkit.sping.pid import AffineMatrix
from rdkit.sping.pid import Canvas
from rdkit.sping.pid import Font
from rdkit.sping.pid import StateSaver
from rdkit.sping.pid import getFileObject
__all__: list[str] = ['AffineMatrix', 'Bold', 'Canvas', 'Color', 'EpsDSC', 'Font', 'HexColor', 'Italic', 'PSCanvas', 'PSFontMapLatin1Enc', 'PSFontMapStdEnc', 'PiddleLegalFonts', 'PostScriptLevelException', 'PsDSC', 'Roman', 'StateSaver', 'StringIO', 'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond', 'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'cm', 'coral', 'cornflower', 'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgreen', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkturquoise', 'darkviolet', 'dashLineDefinition', 'deeppink', 'deepskyblue', 'dimgray', 'dodgerblue', 'figureArc', 'figureCurve', 'figureLine', 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia', 'gainsboro', 'getFileObject', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'green', 'greenyellow', 'grey', 'honeydew', 'hotpink', 'inch', 'indianred', 'indigo', 'ivory', 'keyBksp', 'keyClear', 'keyDel', 'keyDown', 'keyEnd', 'keyHome', 'keyLeft', 'keyPgDn', 'keyPgUp', 'keyRight', 'keyTab', 'keyUp', 'khaki', 'latin1FontEncoding', 'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow', 'lightgreen', 'lightgrey', 'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue', 'lightslategray', 'lightsteelblue', 'lightyellow', 'lime', 'limegreen', 'linen', 'linesep', 'magenta', 'maroon', 'math', 'mediumaquamarine', 'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen', 'mediumturquoise', 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'modControl', 'modShift', 'navajowhite', 'navy', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred', 'papayawhip', 'peachpuff', 'peru', 'pink', 'plum', 'powderblue', 'psmetrics', 'purple', 'red', 'rosybrown', 'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver', 'skyblue', 'slateblue', 'slategray', 'snow', 'springgreen', 'steelblue', 'tan', 'teal', 'thistle', 'tomato', 'transparent', 'turquoise', 'violet', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen']
class PostScriptLevelException(ValueError):
    pass
class PsDSC:
    def BeginPageStr(self, pageSetupStr, pageName = None):
        """
        Use this at the beginning of each page, feed it your setup code
                in the form of a string of postscript.  pageName is the "number" of the
                page.  By default it will be 0.
        """
    def EndPageStr(self):
        ...
    def __init__(self):
        ...
    def boundingBoxStr(self, x0, y0, x1, y1):
        """
        coordinates of bbox in default PS coordinates
        """
    def documentHeader(self):
        ...
class EpsDSC(PsDSC):
    def __init__(self):
        ...
    def documentHeader(self):
        ...
class PSCanvas(rdkit.sping.pid.Canvas):
    """
    This canvas is meant for generating encapsulated PostScript files
        (EPS) used for inclusion in other documents; thus really only
        single-page documents are supported.  For historical reasons and
        because they can be printed (a showpage is included), the files are
        given a .ps extension by default, and a primitive sort of multipage
        document can be generated using nextPage() or clear().  Use at your own
        risk!  Future versions of piddlePS will include an EPSCanvas and a
        PSCanvas which will clearly delineate between single and multipage
        documents.
    
        Note: All font encodings must be taken care in __init__, you can't add
              more after this
    """
    def _AsciiHexEncode(self, input):
        """
        Helper function used by images
        """
    def __init__(self, size = (300, 300), name = 'piddlePS', PostScriptLevel = 2, fontMapEncoding = {('helvetica', 'Roman'): 'Helvetica-Roman-ISOLatin1', ('helvetica', 'Bold'): 'Helvetica-Bold-ISOLatin1', ('helvetica', 'Italic'): 'Helvetica-Oblique-ISOLatin1', ('times', 'Roman'): 'Times-Roman-ISOLatin1', ('times', 'Bold'): 'Times-Bold-ISOLatin1', ('times', 'Italic'): 'Times-Italic-ISOLatin1', ('courier', 'Roman'): 'Courier-Roman-ISOLatin1', ('courier', 'Bold'): 'Courier-Bold-ISOLatin1', ('courier', 'Italic'): 'Courier-Oblique-ISOLatin1', ('symbol', 'Roman'): 'Symbol', ('symbol', 'Bold'): 'Symbol', ('symbol', 'Italic'): 'Symbol', 'EncodingName': 'Latin1Encoding'}):
        ...
    def _drawImageLevel1(self, image, x1, y1, x2 = None, y2 = None, **kwargs):
        """
        drawImage(self,image,x1,y1,x2=None,y2=None) : If x2 and y2 are omitted, they are
               calculated from image size.  (x1,y1) is upper left of image, (x2,y2) is lower right of
               image in piddle coordinates.
        """
    def _drawImageLevel2(self, image, x1, y1, x2 = None, y2 = None):
        ...
    def _drawStringOneLine(self, s, x, y, font = None, color = None, angle = 0, **kwargs):
        ...
    def _drawStringOneLineNoRot(self, s, x, y, font = None, **kwargs):
        ...
    def _escape(self, s):
        ...
    def _findExternalFontName(self, font):
        """
        Attempts to return proper font name.
                PDF uses a standard 14 fonts referred to
                by name. Default to self.defaultFont('Helvetica').
                The dictionary allows a layer of indirection to
                support a standard set of PIDDLE font names.
        """
    def _findFont(self, font):
        ...
    def _genArcCode(self, x1, y1, x2, y2, startAng, extent):
        """
        Calculate the path for an arc inscribed in rectangle defined by (x1,y1),(x2,y2)
        """
    def _psNextPage(self):
        """
        advance to next page of document.  
        """
    def _psPageSetupStr(self, pageheight, initialColor, font_family, font_size, line_width):
        """
        ps code for settin up coordinate system for page in accords w/ piddle standards
        """
    def _updateFillColor(self, color):
        ...
    def _updateFont(self, font):
        ...
    def _updateLineColor(self, color):
        ...
    def _updateLineWidth(self, width):
        ...
    def clear(self):
        """
        clear resets the canvas to it's default state.  Though this
                canvas is really only meant to be an EPS canvas, i.e., single page,
                for historical reasons we will allow multipage documents.  Thus
                clear will end the page, clear the canvas state back to default,
                and start a new page.  In the future, this PSCanvas will become
                EPSCanvas and will not support multipage documents.  In that case,
                the canvas will be reset to its default state and the file will be
                emptied of all previous drawing commands
        """
    def drawArc(self, x1, y1, x2, y2, startAng = 0, extent = 360, edgeColor = None, edgeWidth = None, fillColor = None, dash = None, **kwargs):
        """
        Draw a partial ellipse inscribed within the rectangle x1,y1,x2,y2,         starting at startAng degrees and covering extent degrees.   Angles         start with 0 to the right (+x) and increase counter-clockwise.         These should have x1<x2 and y1<y2.
        """
    def drawCurve(self, x1, y1, x2, y2, x3, y3, x4, y4, edgeColor = None, edgeWidth = None, fillColor = None, closed = 0, dash = None, **kwargs):
        ...
    def drawEllipse(self, x1, y1, x2, y2, edgeColor = None, edgeWidth = None, fillColor = None, dash = None, **kwargs):
        """
        Draw an orthogonal ellipse inscribed within the rectangle x1,y1,x2,y2.         These should have x1<x2 and y1<y2.
        """
    def drawFigure(self, partList, edgeColor = None, edgeWidth = None, fillColor = None, closed = 0, dash = None, **kwargs):
        ...
    def drawLine(self, x1, y1, x2, y2, color = None, width = None, dash = None, **kwargs):
        ...
    def drawLines(self, lineList, color = None, width = None, dash = None, **kwargs):
        ...
    def drawPolygon(self, pointlist, edgeColor = None, edgeWidth = None, fillColor = None, closed = 0, dash = None, **kwargs):
        ...
    def drawRoundRect(self, x1, y1, x2, y2, rx = 8, ry = 8, edgeColor = None, edgeWidth = None, fillColor = None, dash = None, **kwargs):
        """
        Draw a rounded rectangle between x1,y1, and x2,y2,         with corners inset as ellipses with x radius rx and y radius ry.         These should have x1<x2, y1<y2, rx>0, and ry>0.
        """
    def drawString(self, s, x, y, font = None, color = None, angle = 0, **kwargs):
        """
        drawString(self, s, x, y, font=None, color=None, angle=0)
                draw a string s at position x,y
        """
    def flush(self):
        ...
    def fontAscent(self, font = None):
        ...
    def fontDescent(self, font = None):
        ...
    def nextPage(self):
        ...
    def psBeginDocument(self):
        ...
    def psBeginPage(self, pageName = None):
        ...
    def psEndDocument(self):
        ...
    def psEndPage(self):
        ...
    def resetToDefaults(self):
        ...
    def save(self, file = None, format = None):
        """
        Write the current document to a file or stream and close the file
                Computes any final trailers, etc. that need to be done in order to
                produce a well formed postscript file.  At least for now though,
                it still allows you to add to the file after a save by not actually
                inserting the finalization code into self.code
        
                the format argument is not used
        """
    def stringWidth(self, s, font = None):
        """
        Return the logical width of the string if it were drawn         in the current font (defaults to self.font).
        """
def dashLineDefinition():
    ...
def latin1FontEncoding(fontname):
    """
    use this to generating PS code for re-encoding a font as ISOLatin1
        from font with name 'fontname' defines reencoded font, 'fontname-ISOLatin1'
    """
Bold: str = 'Bold'
Italic: str = 'Italic'
PSFontMapLatin1Enc: dict = {('helvetica', 'Roman'): 'Helvetica-Roman-ISOLatin1', ('helvetica', 'Bold'): 'Helvetica-Bold-ISOLatin1', ('helvetica', 'Italic'): 'Helvetica-Oblique-ISOLatin1', ('times', 'Roman'): 'Times-Roman-ISOLatin1', ('times', 'Bold'): 'Times-Bold-ISOLatin1', ('times', 'Italic'): 'Times-Italic-ISOLatin1', ('courier', 'Roman'): 'Courier-Roman-ISOLatin1', ('courier', 'Bold'): 'Courier-Bold-ISOLatin1', ('courier', 'Italic'): 'Courier-Oblique-ISOLatin1', ('symbol', 'Roman'): 'Symbol', ('symbol', 'Bold'): 'Symbol', ('symbol', 'Italic'): 'Symbol', 'EncodingName': 'Latin1Encoding'}
PSFontMapStdEnc: dict = {('helvetica', 'Roman'): 'Helvetica-Roman', ('helvetica', 'Bold'): 'Helvetica-Bold', ('helvetica', 'Italic'): 'Helvetica-Oblique', ('times', 'Roman'): 'Times-Roman', ('times', 'Bold'): 'Times-Bold', ('times', 'Italic'): 'Times-Italic', ('courier', 'Roman'): 'Courier-Roman', ('courier', 'Bold'): 'Courier-Bold', ('courier', 'Italic'): 'Courier-Oblique', ('symbol', 'Roman'): 'Symbol', ('symbol', 'Bold'): 'Symbol', ('symbol', 'Italic'): 'Symbol', 'EncodingName': 'StandardEncoding'}
PiddleLegalFonts: dict = {'helvetica': 'helvetica', 'times': 'times', 'courier': 'courier', 'serif': 'times', 'sansserif': 'helvetica', 'monospaced': 'courier', 'symbol': 'symbol'}
Roman: str = 'Roman'
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
linesep: str = '\n'
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
