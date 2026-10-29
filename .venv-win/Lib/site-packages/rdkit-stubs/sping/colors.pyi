from __future__ import annotations
__all__: list[str] = ['Color', 'HexColor', 'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond', 'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'coral', 'cornflower', 'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgreen', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkturquoise', 'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dodgerblue', 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia', 'gainsboro', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'green', 'greenyellow', 'grey', 'honeydew', 'hotpink', 'indianred', 'indigo', 'ivory', 'khaki', 'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow', 'lightgreen', 'lightgrey', 'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue', 'lightslategray', 'lightsteelblue', 'lightyellow', 'lime', 'limegreen', 'linen', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen', 'mediumturquoise', 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'navajowhite', 'navy', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred', 'papayawhip', 'peachpuff', 'peru', 'pink', 'plum', 'powderblue', 'purple', 'red', 'rosybrown', 'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver', 'skyblue', 'slateblue', 'slategray', 'snow', 'springgreen', 'steelblue', 'tan', 'teal', 'thistle', 'tomato', 'transparent', 'turquoise', 'violet', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen']
class Color:
    """
    This class is used to represent color.  Components red, green, blue 
              are in the range 0 (dark) to 1 (full intensity).
    """
    def __add__(self, x):
        ...
    def __cmp__(self, other):
        ...
    def __div__(self, x):
        ...
    def __hash__(self):
        ...
    def __init__(self, red = 0, green = 0, blue = 0):
        """
        Initialize with red, green, blue in range [0-1].
        """
    def __mul__(self, x):
        ...
    def __rdiv__(self, x):
        ...
    def __repr__(self):
        ...
    def __rmul__(self, x):
        ...
    def __setattr__(self, name, value):
        ...
    def __sub__(self, x):
        ...
    def __truediv__(self, x):
        ...
    def toHexRGB(self):
        """
        Convert the color back to an integer suitable for the 
        """
    def toHexStr(self):
        ...
def HexColor(val):
    """
    This class converts a hex string, or an actual integer number,
              into the corresponding color.  E.g., in "AABBCC" or 0xAABBCC,
              AA is the red, BB is the green, and CC is the blue (00-FF).
    """
aliceblue: Color
antiquewhite: Color
aqua: Color
aquamarine: Color
azure: Color
beige: Color
bisque: Color
black: Color
blanchedalmond: Color
blue: Color
blueviolet: Color
brown: Color
burlywood: Color
cadetblue: Color
chartreuse: Color
chocolate: Color
coral: Color
cornflower: Color
cornsilk: Color
crimson: Color
cyan: Color
darkblue: Color
darkcyan: Color
darkgoldenrod: Color
darkgray: Color
darkgreen: Color
darkkhaki: Color
darkmagenta: Color
darkolivegreen: Color
darkorange: Color
darkorchid: Color
darkred: Color
darksalmon: Color
darkseagreen: Color
darkslateblue: Color
darkslategray: Color
darkturquoise: Color
darkviolet: Color
deeppink: Color
deepskyblue: Color
dimgray: Color
dodgerblue: Color
firebrick: Color
floralwhite: Color
forestgreen: Color
fuchsia: Color
gainsboro: Color
ghostwhite: Color
gold: Color
goldenrod: Color
gray: Color
green: Color
greenyellow: Color
grey: Color
honeydew: Color
hotpink: Color
indianred: Color
indigo: Color
ivory: Color
khaki: Color
lavender: Color
lavenderblush: Color
lawngreen: Color
lemonchiffon: Color
lightblue: Color
lightcoral: Color
lightcyan: Color
lightgoldenrodyellow: Color
lightgreen: Color
lightgrey: Color
lightpink: Color
lightsalmon: Color
lightseagreen: Color
lightskyblue: Color
lightslategray: Color
lightsteelblue: Color
lightyellow: Color
lime: Color
limegreen: Color
linen: Color
magenta: Color
maroon: Color
mediumaquamarine: Color
mediumblue: Color
mediumorchid: Color
mediumpurple: Color
mediumseagreen: Color
mediumslateblue: Color
mediumspringgreen: Color
mediumturquoise: Color
mediumvioletred: Color
midnightblue: Color
mintcream: Color
mistyrose: Color
moccasin: Color
navajowhite: Color
navy: Color
oldlace: Color
olive: Color
olivedrab: Color
orange: Color
orangered: Color
orchid: Color
palegoldenrod: Color
palegreen: Color
paleturquoise: Color
palevioletred: Color
papayawhip: Color
peachpuff: Color
peru: Color
pink: Color
plum: Color
powderblue: Color
purple: Color
red: Color
rosybrown: Color
royalblue: Color
saddlebrown: Color
salmon: Color
sandybrown: Color
seagreen: Color
seashell: Color
sienna: Color
silver: Color
skyblue: Color
slateblue: Color
slategray: Color
snow: Color
springgreen: Color
steelblue: Color
tan: Color
teal: Color
thistle: Color
tomato: Color
transparent: Color
turquoise: Color
violet: Color
wheat: Color
white: Color
whitesmoke: Color
yellow: Color
yellowgreen: Color
