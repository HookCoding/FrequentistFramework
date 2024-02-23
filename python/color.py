from __future__ import print_function
import ROOT

warm_palette = [ROOT.kAzure+5, ROOT.kSpring-8 , ROOT.kOrange-2, ROOT.kRed-7  ]
classic_palette8 = [ROOT.kBlue-4, ROOT.kAzure+5, ROOT.kSpring-8 , ROOT.kOrange-2, ROOT.kRed-7  ]

# 1001 solid
# fill_styles = [3001, 3002, 0, 3004, 3005, 3006] 
# fill_styles = [3245, 3295, 3254, 3250, 3225, 3275]
fill_styles = [3245, 3254, 3445, 3454, 3295, 3250]
marker_styles_full = [ROOT.kFullCircle,ROOT.kFullSquare,ROOT.kFullTriangleUp,ROOT.kFullTriangleDown,ROOT.kFullDiamond,ROOT.kFullCross,ROOT.kFullStar]
marker_styles_open = [ROOT.kOpenCircle,ROOT.kOpenSquare,ROOT.kOpenTriangleUp,ROOT.kOpenTriangleDown,ROOT.kOpenDiamond,ROOT.kOpenCross,ROOT.kOpenStar]

def getMarkerStyle(index):
    return marker_styles_full[index]

def getMarkerStyleOpen(index):
    return marker_styles_open[index]

def getMarkerStyles():
    return marker_styles_full

def getMarkerStylesOpen():
    return marker_styles_open

def getFillStyles():
    return fill_styles

# def getFillStyle(index):
#     if index == 0: return 1001
#     elif index == 1: return 3001
#     else: return 0

#     c = fill_styles.pop(0)
#     fill_styles.append(c)
#     return c

def getFillStyle(index):
    return fill_styles[index]

def hslToRgb(h, s, l):
    (r,g,b) = (0,0,0)
    if s == 0:
        print('achromatic')
        (r, g, b) = (l, l, l); # achromatic
    else:
        def hue2rgb(p, q, t):
            if t < 0 : t += 1;
            if t > 1 : t -= 1;
            if t < 1./6: return p + (q - p) * 6 * t;
            if t < 1./2: return q;
            if t < 2./3: return p + (q - p) * (2./3 - t) * 6;
            return p;
        
        q = l * (1 + s) if l < 0.5  else l + s - l * s;
        p = 2 * l - q;
        r = hue2rgb(p, q, h + 1./3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1./3);
    
    return (r, g, b)
    #return [math.round(r * 255), math.round(g * 255), math.round(b * 255)];


def colorInterpolate(col1, col2,  w = 0.5):
    c1 = ROOT.gROOT.GetColor(col1);
    c2 = ROOT.gROOT.GetColor(col2);

    # get intermediate RGB
    r = c1.GetRed()  * (1 - w) + c2.GetRed()  * w;
    g = c1.GetGreen()* (1 - w) + c2.GetGreen()* w;
    b = c1.GetBlue() * (1 - w) + c2.GetBlue() * w;
    
    return ROOT.TColor.GetColor(r, g, b);

def getInterpolatedColorSteps(startC, endC, n):
    if n == 0: return []
    elif n == 1:
        return [colorInterpolate(startC,endC,0.5)]
    listcolors = []
    for i in range (1,n+1):
        listcolors.append(colorInterpolate(startC, endC, i*1.0/(n+1)))

    return listcolors

def getColorSteps(n):
    print("Making color steps for {0} inputs".format(n))
    (C0, C1, C2, C3, C4, C5) = (ROOT.kBlue+2, ROOT.kAzure+5, ROOT.kSpring-8 , ROOT.kOrange-2, ROOT.kRed-7, ROOT.kMagenta+1)
    base_colors = [C1, C2, C3, C4, C5]
    if n == 1: return [C1]
    elif n == 2: return [C1, C4]
    elif n == 3: return [C1,C3,C4]
    elif n == 4: return [C1,C2,C3,C4]
    elif n == 5: return [C0, C1,C2,C3,C4]
    #elif n == 6: return [C0, C1,C2,C3,C4, C5]
    else:
        n_extra = n-len(base_colors)
        
        n_spacers = len(base_colors) - 1
        print(n_extra, n_spacers, n_extra/n_spacers, n_extra%n_spacers)
        #if n_spacers%n_padding == 0: 
        #spacers01 = getInterpolatedColorSteps(C0,C1, n_extra//n_spacers + 1 if n_extra%n_spacers > 0 else 0)
        spacers12 = getInterpolatedColorSteps(C1,C2, n_extra//n_spacers )
        spacers23 = getInterpolatedColorSteps(C2,C3, n_extra//n_spacers  + (1 if n_extra%n_spacers > 0 else 0))
        spacers34 = getInterpolatedColorSteps(C3,C4, n_extra//n_spacers  + (1 if n_extra%n_spacers > 1 else 0))
        spacers45 = getInterpolatedColorSteps(C4,C5, n_extra//n_spacers  + (1 if n_extra%n_spacers > 2 else 0))
        '''elif n_spacers%4 == 1: 
            spacers01 = getInterpolatedColorSteps(C0,C1, n_spacers/4 )
            spacers12 = getInterpolatedColorSteps(C1,C2, n_spacers/4 )
            spacers23 = getInterpolatedColorSteps(C2,C3, n_spacers/4 )
            spacers34 = getInterpolatedColorSteps(C3,C4, n_spacers/4+1 )
        elif n_spacers%4 == 2: 
            spacers01 = getInterpolatedColorSteps(C0,C1, n_spacers/4 )
            spacers12 = getInterpolatedColorSteps(C1,C2, n_spacers/4 )
            spacers23 = getInterpolatedColorSteps(C2,C3, n_spacers/4+1 )
            spacers34 = getInterpolatedColorSteps(C3,C4, n_spacers/4+1 )
        elif n_spacers%4 == 3: 
            spacers01 = getInterpolatedColorSteps(C0,C1, n_spacers/4+1 )
            spacers12 = getInterpolatedColorSteps(C1,C2, n_spacers/4 )
            spacers23 = getInterpolatedColorSteps(C2,C3, n_spacers/4+1 )
            spacers34 = getInterpolatedColorSteps(C3,C4, n_spacers/4+1 )'''

        print(len(spacers12), len(spacers23),len(spacers34), len(spacers45))
        color_spectrum = [C1] + spacers12  + [C2] +spacers23+ [C3] + spacers34+  [C4] + spacers45 + [C5]
        print(color_spectrum)
        return(color_spectrum)

