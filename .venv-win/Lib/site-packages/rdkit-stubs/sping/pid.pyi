"""
PIDDLE (Plug-In Drawing, Does Little Else)
2D Plug-In Drawing System

Magnus Lie Hetland
Andy Robinson
Joseph J. Strout
and others

February-March 1999

On coordinates: units are Big Points, approximately 1/72 inch.
The origin is at the top-left, and coordinates increase down (y)
and to the right (x).

"""
from __future__ import annotations
import rdkit.sping.colors
from rdkit.sping.colors import Color
from rdkit.sping.colors import HexColor
__all__: list[str] = ['AffineMatrix', 'Canvas', 'Color', 'Font', 'HexColor', 'StateSaver', 'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond', 'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'cm', 'coral', 'cornflower', 'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgreen', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkturquoise', 'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dodgerblue', 'figureArc', 'figureCurve', 'figureLine', 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia', 'gainsboro', 'getFileObject', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'green', 'greenyellow', 'grey', 'honeydew', 'hotpink', 'inch', 'indianred', 'indigo', 'ivory', 'keyBksp', 'keyClear', 'keyDel', 'keyDown', 'keyEnd', 'keyHome', 'keyLeft', 'keyPgDn', 'keyPgUp', 'keyRight', 'keyTab', 'keyUp', 'khaki', 'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow', 'lightgreen', 'lightgrey', 'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue', 'lightslategray', 'lightsteelblue', 'lightyellow', 'lime', 'limegreen', 'linen', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen', 'mediumturquoise', 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'modControl', 'modShift', 'navajowhite', 'navy', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred', 'papayawhip', 'peachpuff', 'peru', 'pink', 'plum', 'powderblue', 'purple', 'red', 'rosybrown', 'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver', 'skyblue', 'slateblue', 'slategray', 'snow', 'springgreen', 'steelblue', 'tan', 'teal', 'thistle', 'tomato', 'transparent', 'turquoise', 'violet', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen']
class StateSaver:
    """
    This is a little utility class for saving and restoring the
              default drawing parameters of a canvas.  To use it, add a line
              like this before changing any of the parameters:
    
                      saver = StateSaver(myCanvas)
    
              then, when "saver" goes out of scope, it will automagically
              restore the drawing parameters of myCanvas.
    """
    def __del__(self):
        ...
    def __init__(self, canvas):
        ...
class Font:
    """
    This class represents font typeface, size, and style.
    """
    def __cmp__(self, other):
        """
        Compare two fonts to see if they're the same.
        """
    def __init__(self, size = 12, bold = 0, italic = 0, underline = 0, face = None):
        ...
    def __repr__(self):
        ...
    def __setattr__(self, name, value):
        ...
class Canvas:
    """
    This is the base class for a drawing canvas.  The 'plug-in renderers'
              we speak of are really just classes derived from this one, which implement
              the various drawing methods.
    """
    def __init__(self, size = (300, 300), name = 'PIDDLE'):
        """
        Initialize the canvas, and set default drawing parameters.
                            Derived classes should be sure to call this method.
        """
    def arcPoints(self, x1, y1, x2, y2, startAng = 0, extent = 360):
        """
        Return a list of points approximating the given arc.
        """
    def canUpdate(self):
        """
        Returns 1 if the drawing can be meaningfully updated over time                     (e.g., screen graphics), 0 otherwise (e.g., drawing to a file).
        """
    def clear(self):
        """
        Call this to clear and reset the graphics context.
        """
    def curvePoints(self, x1, y1, x2, y2, x3, y3, x4, y4):
        """
        Return a list of points approximating the given Bezier curve.
        """
    def drawArc(self, x1, y1, x2, y2, startAng = 0, extent = 360, edgeColor = None, edgeWidth = None, fillColor = None, dash = None, **kwargs):
        """
        Draw a partial ellipse inscribed within the rectangle x1,y1,x2,y2,                     starting at startAng degrees and covering extent degrees.   Angles                     start with 0 to the right (+x) and increase counter-clockwise.                     These should have x1<x2 and y1<y2.
        """
    def drawCurve(self, x1, y1, x2, y2, x3, y3, x4, y4, edgeColor = None, edgeWidth = None, fillColor = None, closed = 0, dash = None, **kwargs):
        """
        Draw a Bezier curve with control points x1,y1 to x4,y4.
        """
    def drawEllipse(self, x1, y1, x2, y2, edgeColor = None, edgeWidth = None, fillColor = None, dash = None, **kwargs):
        """
        Draw an orthogonal ellipse inscribed within the rectangle x1,y1,x2,y2.                     These should have x1<x2 and y1<y2.
        """
    def drawFigure(self, partList, edgeColor = None, edgeWidth = None, fillColor = None, closed = 0, dash = None, **kwargs):
        """
        drawFigure(partList) -- draws a complex figure
                            partlist: a set of lines, curves, and arcs defined by a tuple whose
                                              first element is one of figureLine, figureArc, figureCurve
                                              and whose remaining 4, 6, or 8 elements are parameters.
        """
    def drawImage(self, image, x1, y1, x2 = None, y2 = None, **kwargs):
        """
        Draw a PIL Image into the specified rectangle.  If x2 and y2 are
                            omitted, they are calculated from the image size.
        """
    def drawLine(self, x1, y1, x2, y2, color = None, width = None, dash = None, **kwargs):
        """
        Draw a straight line between x1,y1 and x2,y2.
        """
    def drawLines(self, lineList, color = None, width = None, dash = None, **kwargs):
        """
        Draw a set of lines of uniform color and width.                      lineList: a list of (x1,y1,x2,y2) line coordinates.
        """
    def drawMultiLineString(self, s, x, y, font = None, color = None, angle = 0, **kwargs):
        """
        Breaks string into lines (on 
        , 
        , 
        
        , or 
        ), and calls drawString on each.
        """
    def drawPolygon(self, pointlist, edgeColor = None, edgeWidth = None, fillColor = None, closed = 0, dash = None, **kwargs):
        """
        drawPolygon(pointlist) -- draws a polygon
                            pointlist: a list of (x,y) tuples defining vertices
                            closed: if 1, adds an extra segment connecting the last point to the first
                            
        """
    def drawRect(self, x1, y1, x2, y2, edgeColor = None, edgeWidth = None, fillColor = None, dash = None, **kwargs):
        """
        Draw the rectangle between x1,y1, and x2,y2.                     These should have x1<x2 and y1<y2.
        """
    def drawRoundRect(self, x1, y1, x2, y2, rx = 8, ry = 8, edgeColor = None, edgeWidth = None, fillColor = None, dash = None, **kwargs):
        """
        Draw a rounded rectangle between x1,y1, and x2,y2,                     with corners inset as ellipses with x radius rx and y radius ry.                     These should have x1<x2, y1<y2, rx>0, and ry>0.
        """
    def drawString(self, s, x, y, font = None, color = None, angle = 0, **kwargs):
        """
        Draw a string starting at location x,y.
        """
    def flush(self):
        """
        Call this to indicate that any comamnds that have been issued                     but which might be buffered should be flushed to the screen
        """
    def fontAscent(self, font = None):
        """
        Find the ascent (height above base) of the given font.
        """
    def fontDescent(self, font = None):
        """
        Find the descent (extent below base) of the given font.
        """
    def fontHeight(self, font = None):
        """
        Find the height of one line of text (baseline to baseline) of the given font.
        """
    def getSize(self):
        ...
    def isInteractive(self):
        """
        Returns 1 if onClick, onOver, and onKey events are possible, 0 otherwise.
        """
    def save(self, file = None, format = None):
        """
        For backends that can be save to a file or sent to a
                            stream, create a valid file out of what's currently been
                            drawn on the canvas.  Trigger any finalization here.
                            Though some backends may allow further drawing after this call,
                            presume that this is not possible for maximum portability
        
                            file may be either a string or a file object with a write method
                                 if left as the default, the canvas's current name will be used
        
                            format may be used to specify the type of file format to use as
                                 well as any corresponding extension to use for the filename
                                 This is an optional argument and backends may ignore it if
                                 they only produce one file format.
        """
    def setInfoLine(self, s):
        """
        For interactive Canvases, displays the given string in the                     'info line' somewhere where the user can probably see it.
        """
    def stringBox(self, s, font = None):
        ...
    def stringWidth(self, s, font = None):
        """
        Return the logical width of the string if it were drawn                     in the current font (defaults to self.font).
        """
class AffineMatrix:
    def __init__(self, init = None):
        ...
    def rotate(self, theta):
        """
        counter clockwise rotation in standard SVG/libart coordinate system
        """
    def scale(self, sx, sy):
        ...
    def translate(self, tx, ty):
        ...
def getFileObject(file, openFlags = 'wb'):
    """
    Common code for every Canvas.save() operation takes a string
              or a potential file object and assures that a valid fileobj is returned
    """
__version__: str = '1.0.0'
__version_maj_number__: str = '1.0'
__version_min_number__: str = '0'
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
