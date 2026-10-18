from PIL import Image, ImageDraw, ImageFilter

S = 2  # supersample

def cr(points, n=14):
    """Closed Catmull-Rom spline through points."""
    out = []
    L = len(points)
    for i in range(L):
        p0, p1, p2, p3 = points[i-1], points[i], points[(i+1) % L], points[(i+2) % L]
        for k in range(n):
            t = k / n; t2 = t*t; t3 = t2*t
            x = 0.5*((2*p1[0]) + (-p0[0]+p2[0])*t + (2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2 + (-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
            y = 0.5*((2*p1[1]) + (-p0[1]+p2[1])*t + (2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2 + (-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
            out.append((x*S, y*S))
    return out

def poly(d, pts, fill, smooth=True):
    d.polygon(cr(pts) if smooth else [(x*S, y*S) for x, y in pts], fill=fill)

def make_shoe(main, accent, sole=(245, 245, 240), outsole=(40, 40, 48)):
    W, H = 1200, 700
    img = Image.new("RGBA", (W*S, H*S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # outsole + midsole
    d.rounded_rectangle([62*S,560*S,1160*S,622*S], radius=30*S, fill=outsole)
    d.rounded_rectangle([64*S,500*S,1150*S,595*S], radius=45*S, fill=sole)
    d.polygon([(900*S,505*S),(1140*S,468*S),(1168*S,520*S),(1150*S,560*S),(1000*S,560*S)], fill=sole)
    # midsole air window
    d.rounded_rectangle([170*S,535*S,390*S,572*S], radius=18*S, fill=accent+(200,))
    for x in range(200, 380, 30):
        d.line([(x*S,540*S),(x*S,567*S)], fill=(255,255,255,140), width=4*S)
    # upper
    upper = [(95,510),(108,330),(150,250),(240,232),(330,268),(420,280),(500,192),(560,160),(625,190),
             (700,290),(820,360),(960,410),(1080,445),(1145,482),(1132,520),(600,530)]
    poly(d, upper, main)
    # heel counter & toe cap
    poly(d, [(95,508),(104,360),(140,298),(230,330),(262,460),(240,515)], accent)
    poly(d, [(870,522),(945,420),(1060,445),(1145,482),(1135,520)], accent)
    # side wave stripe
    lighter = tuple(min(255, c+45) for c in main)
    poly(d, [(270,515),(330,380),(460,300),(640,300),(780,360),(860,520)], lighter)
    for k, (y0, x0, x1) in enumerate([(470,340,760),(430,380,720),(390,420,680)]):
        d.line([(x0*S,y0*S),(x1*S,(y0-40)*S)], fill=accent, width=(16-4*k)*S)
    d.ellipse([140*S,380*S,220*S,460*S], fill=lighter)
    d.line([(160*S,400*S),(200*S,440*S)], fill=accent, width=8*S)
    d.line([(200*S,400*S),(160*S,440*S)], fill=accent, width=8*S)
    # collar opening and tongue
    poly(d, [(155,258),(240,240),(332,272),(300,292),(200,284)], (30,30,36))
    poly(d, [(470,215),(530,145),(600,150),(625,200),(545,245)], tuple(min(255, c+30) for c in main))
    # laces
    for i in range(6):
        t = i/5
        x = 560 + t*270; y = 225 + t*150
        px, py = -0.486*30, 0.874*30
        for sg in (-1, 1):
            cx, cy = x+sg*px, y+sg*py
            d.ellipse([(cx-7)*S,(cy-7)*S,(cx+7)*S,(cy+7)*S], fill=(30,30,36))
        d.line([((x-px)*S,(y-py)*S),((x+px)*S,(y+py)*S)], fill=(250,250,250), width=10*S)
    # gloss highlight
    gl = Image.new("RGBA", img.size, (0,0,0,0))
    gd = ImageDraw.Draw(gl)
    poly(gd, [(160,300),(260,262),(400,300),(500,222),(560,200),(520,260),(420,330),(260,300)], (255,255,255,70))
    gl = gl.filter(ImageFilter.GaussianBlur(8*S))
    img.alpha_composite(gl)
    return img.resize((W, H), Image.LANCZOS)

if __name__ == "__main__":
    make_shoe((230,50,60),(30,30,40)).save("shoe_test.png")
