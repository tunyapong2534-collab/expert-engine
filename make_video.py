import math, subprocess, wave, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from shoe import make_shoe

W, H, FPS, DUR = 1080, 1920, 30, 24.0
FD = "../fonts/"
from functools import lru_cache
@lru_cache(maxsize=None)
def F(sz, w="ExtraBold"): return ImageFont.truetype(FD+f"Prompt-{w}.ttf", max(4, sz))

def clamp(x, a=0, b=1): return max(a, min(b, x))
def ease_out(t): t = clamp(t); return 1-(1-t)**3
def ease_back(t):
    t = clamp(t); c1 = 1.70158; c3 = c1+1
    return 1 + c3*(t-1)**3 + c1*(t-1)**2
def prog(t, a, b): return clamp((t-a)/(b-a))

COLORS = {
    "red":   ((230,50,60),(30,30,40)),
    "blue":  ((40,110,230),(250,200,40)),
    "black": ((45,45,55),(240,90,40)),
}
SHOES = {k: make_shoe(*v) for k, v in COLORS.items()}

def grad(c1, c2):
    y = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(c1)*(1-y) + np.array(c2)*y).astype(np.uint8)
    return Image.fromarray(np.repeat(arr, W, axis=1), "RGB").convert("RGBA")
BG = {
    "dark":  grad((18,18,30),(60,20,50)),
    "warm":  grad((255,120,60),(220,40,80)),
    "cool":  grad((20,40,90),(10,140,180)),
    "gold":  grad((25,20,15),(90,60,10)),
}

shadow = Image.new("RGBA", (900, 160), (0,0,0,0))
ImageDraw.Draw(shadow).ellipse([40,40,860,120], fill=(0,0,0,130))
shadow = shadow.filter(ImageFilter.GaussianBlur(22))

def put_shoe(fr, shoe, cx, cy, scale, angle=0, alpha=1.0, shadow_on=True, lift=0):
    if scale <= 0.01 or alpha <= 0: return
    if shadow_on:
        s = shadow.resize((int(900*scale*max(0.6, 1-lift/400)), int(160*scale)))
        sa = s.split()[3].point(lambda v: int(v*alpha))
        s.putalpha(sa)
        fr.alpha_composite(s, (int(cx-s.width/2), int(cy+300*scale-s.height/2)))
    im = shoe.resize((int(1200*scale), int(700*scale)), Image.BICUBIC)
    if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        im.putalpha(im.split()[3].point(lambda v: int(v*alpha)))
    fr.alpha_composite(im, (int(cx-im.width/2), int(cy-lift-im.height/2)))

def text(fr, s, y, size, color=(255,255,255), alpha=1.0, dx=0, w="ExtraBold", stroke=0, stroke_color=(0,0,0), cx=W/2):
    if alpha <= 0: return
    layer = Image.new("RGBA", fr.size, (0,0,0,0))
    d = ImageDraw.Draw(layer)
    f = F(size, w)
    a = int(255*clamp(alpha))
    d.text((cx+dx, y), s, font=f, anchor="mm", fill=color+(a,),
           stroke_width=stroke, stroke_fill=stroke_color+(a,), language="th")
    fr.alpha_composite(layer)

def pill(fr, box, color, alpha=1.0, r=40):
    if alpha <= 0: return
    layer = Image.new("RGBA", fr.size, (0,0,0,0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius=r, fill=color+(int(255*clamp(alpha)),))
    fr.alpha_composite(layer)

def particles(fr, t, color=(255,255,255), n=26, seed=1):
    rng = np.random.default_rng(seed)
    layer = Image.new("RGBA", fr.size, (0,0,0,0)); d = ImageDraw.Draw(layer)
    for i in range(n):
        x0, sp, r, ph = rng.uniform(0,W), rng.uniform(40,140), rng.uniform(3,10), rng.uniform(0,H)
        y = (ph - t*sp) % H
        x = x0 + 25*math.sin(t*1.3+i)
        d.ellipse([x-r,y-r,x+r,y+r], fill=color+(70,))
    fr.alpha_composite(layer)

def flash(fr, t, at, dur=0.25):
    p = prog(t, at, at+dur)
    if 0 < p < 1:
        fr.alpha_composite(Image.new("RGBA", fr.size, (255,255,255,int(200*(1-p)))))

# ---------------- scenes ----------------
def scene_hook(t):  # 0-3.5
    fr = BG["dark"].copy(); particles(fr, t)
    p1 = ease_back(prog(t, 0.1, 0.6))
    text(fr, "เดินทั้งวัน", 520, 120, alpha=prog(t,0.1,0.4), dx=(1-p1)*-400)
    p2 = ease_back(prog(t, 0.5, 1.0))
    text(fr, "เท้ายังไม่ล้า?", 680, 120, color=(255,210,60), alpha=prog(t,0.5,0.8), dx=(1-p2)*400)
    # shoe zooms in from right
    ps = ease_out(prog(t, 1.0, 1.8))
    put_shoe(fr, SHOES["red"], W/2 + (1-ps)*1200, 1180, 0.82, angle=(1-ps)*-20, lift=20*math.sin(t*4))
    if t > 2.0:
        bounce = 1 + 0.06*math.sin((t-2.0)*10)*math.exp(-(t-2.0)*2)
        text(fr, "ต้องคู่นี้เลย!", 1600, int(100*bounce), alpha=prog(t,2.0,2.3), stroke=6, stroke_color=(230,50,60))
    return fr

def scene_reveal(t):  # 3.5-8
    fr = BG["warm"].copy(); particles(fr, t, seed=2)
    # rotating rays
    layer = Image.new("RGBA", fr.size, (0,0,0,0)); d = ImageDraw.Draw(layer)
    cx, cy = W/2, 1000
    for i in range(12):
        a = t*0.4 + i*math.pi/6
        d.polygon([(cx,cy),(cx+1600*math.cos(a),cy+1600*math.sin(a)),(cx+1600*math.cos(a+0.18),cy+1600*math.sin(a+0.18))], fill=(255,255,255,28))
    fr.alpha_composite(layer)
    flash(fr, t, 0)
    pin = ease_back(prog(t, 0.0, 0.7))
    text(fr, "NEW ARRIVAL", 300, 60, alpha=prog(t,0.2,0.5), w="Bold", color=(255,240,200))
    text(fr, "AIRSTEP X1", 420, int(150*max(pin,0.01)), alpha=prog(t,0,0.3), stroke=4, stroke_color=(120,20,40))
    put_shoe(fr, SHOES["red"], W/2, 1020, 0.86*(0.6+0.4*ease_back(prog(t,0.2,0.9))), angle=4*math.sin(t*2), lift=30+25*math.sin(t*3))
    text(fr, "รองเท้าวิ่ง & ใส่เที่ยว", 1500, 72, alpha=prog(t,1.2,1.6), dx=(1-ease_out(prog(t,1.2,1.7)))*300, w="Bold")
    text(fr, "ดีไซน์ใหม่ล่าสุด 2026", 1610, 56, alpha=prog(t,1.6,2.0), w="Regular", color=(255,235,220))
    return fr

FEATS = [("ultra light", "เบาหวิว", "เพียง 220 กรัม", (255,210,60)),
         ("cushion", "พื้นนุ่มเด้ง", "ลดแรงกระแทก 40%", (90,220,255)),
         ("breathe", "ระบายอากาศดี", "ผ้าตาข่าย 3D Knit", (120,240,150))]
def icon(fr, kind, cx, cy, col, a):
    layer = Image.new("RGBA", fr.size, (0,0,0,0)); d = ImageDraw.Draw(layer)
    c = col+(int(255*a),)
    d.ellipse([cx-60,cy-60,cx+60,cy+60], outline=c, width=8)
    if kind == "ultra light":  # feather
        d.polygon([(cx-30,cy+30),(cx+30,cy-35),(cx+5,cy+15)], fill=c); d.line([(cx-35,cy+38),(cx+25,cy-28)], fill=c, width=5)
    elif kind == "cushion":  # spring
        for k in range(4): d.arc([cx-35,cy-40+k*18,cx+35,cy-10+k*18], 0, 180, fill=c, width=7)
    else:  # wind
        for k, l in enumerate((50,35,45)): d.arc([cx-l,cy-35+k*25,cx+l,cy-5+k*25], 200, 360, fill=c, width=7)
    fr.alpha_composite(layer)

def scene_features(t):  # 8-15
    fr = BG["cool"].copy(); particles(fr, t, seed=3)
    flash(fr, t, 0)
    text(fr, "ทำไมต้อง AIRSTEP X1?", 220, 76, alpha=prog(t,0,0.3))
    put_shoe(fr, SHOES["blue"], W/2, 560, 0.62, angle=-6+3*math.sin(t*2), lift=15*math.sin(t*3))
    for i, (k, h, sub, col) in enumerate(FEATS):
        st = 0.6 + i*1.5
        p = ease_back(prog(t, st, st+0.6)); a = prog(t, st, st+0.3)
        y = 980 + i*290; dx = (1-p)*(700 if i % 2 == 0 else -700)
        pill(fr, [80+dx, y-110, W-80+dx, y+110], (255,255,255), alpha=0.14*a, r=50)
        icon(fr, k, 210+dx, y, col, a)
        text(fr, h, y-35, 72, color=col, alpha=a, dx=dx, cx=600)
        text(fr, sub, y+45, 50, alpha=a, dx=dx, w="Regular", cx=600)
    return fr

def scene_colors(t):  # 15-18.5
    fr = BG["dark"].copy(); particles(fr, t, seed=4)
    flash(fr, t, 0)
    text(fr, "มีให้เลือก 3 สี", 260, 96, alpha=prog(t,0,0.3), dx=(1-ease_out(prog(t,0,0.5)))*-300)
    names = [("red","แดงไฟ"),("blue","น้ำเงินสปีด"),("black","ดำสายลุย")]
    for i, (k, n) in enumerate(names):
        st = 0.3 + i*0.6
        p = ease_back(prog(t, st, st+0.5)); a = prog(t, st, st+0.25)
        y = 650 + i*430
        put_shoe(fr, SHOES[k], W/2 - 170 + (1-p)*900, y, 0.52, alpha=a, lift=10*math.sin(t*3+i))
        text(fr, n, y+10, 54, alpha=a, cx=W-150, w="Bold")
    text(fr, "ไซซ์ 36 - 45", 1810, 60, color=(255,210,60), alpha=prog(t,2.2,2.5))
    return fr

def scene_price(t):  # 18.5-21.5
    fr = BG["gold"].copy(); particles(fr, t, color=(255,210,60), seed=5)
    flash(fr, t, 0)
    pb = ease_back(prog(t, 0, 0.5))
    pill(fr, [140, 200, W-140, 380], (230,40,60), alpha=prog(t,0,0.2), r=90)
    text(fr, "โปรเปิดตัว ลด 50%", 290, int(84*max(pb,0.01)))
    put_shoe(fr, SHOES["red"], W/2, 760, 0.72, angle=-8, lift=20*math.sin(t*3))
    a = prog(t, 0.6, 0.9)
    text(fr, "ปกติ 2,590.-", 1210, 70, color=(200,200,200), alpha=a, w="Regular")
    if a > 0:
        sl = ease_out(prog(t, 0.9, 1.2))
        layer = Image.new("RGBA", fr.size, (0,0,0,0))
        ImageDraw.Draw(layer).line([(330,1215),(330+420*sl,1200)], fill=(230,40,60,255), width=10)
        fr.alpha_composite(layer)
    pp = ease_back(prog(t, 1.2, 1.7))
    pulse = 1 + 0.04*math.sin(t*8) if t > 1.7 else 1
    text(fr, "1,290.-", 1450, int(230*max(pp,0.01)*pulse), color=(255,210,60), stroke=8, stroke_color=(120,60,0))
    text(fr, "เหลือเพียง", 1290, 60, alpha=prog(t,1.2,1.4), w="Bold")
    text(fr, "*จำนวนจำกัด เฉพาะเดือนนี้เท่านั้น", 1700, 46, alpha=prog(t,1.8,2.1), w="Regular", color=(255,235,200))
    return fr

def scene_cta(t):  # 21.5-24
    fr = BG["warm"].copy(); particles(fr, t, seed=6)
    flash(fr, t, 0)
    put_shoe(fr, SHOES["red"], W/2, 640, 0.75, angle=6*math.sin(t*3), lift=30*abs(math.sin(t*3)))
    p = ease_back(prog(t, 0.1, 0.6))
    text(fr, "สั่งเลยวันนี้!", 1150, int(130*max(p,0.01)), stroke=6, stroke_color=(150,20,40))
    items = ["ส่งฟรีทั่วไทย", "เก็บเงินปลายทาง", "เปลี่ยนไซซ์ได้ฟรี"]
    for i, s in enumerate(items):
        st = 0.5 + i*0.25
        a = prog(t, st, st+0.2)
        text(fr, "✓ " if False else s, 1330+i*90, 58, alpha=a, dx=(1-ease_out(prog(t,st,st+0.4)))*200, w="Bold")
    pulse = 1 + 0.05*math.sin(t*9)
    bw, bh = 640*pulse, 140*pulse
    pill(fr, [W/2-bw/2, 1720-bh/2, W/2+bw/2, 1720+bh/2], (255,255,255), alpha=prog(t,1.2,1.4), r=70)
    text(fr, "กดตะกร้าเลย", 1720, int(70*pulse), color=(220,40,70), alpha=prog(t,1.2,1.4))
    return fr

SCENES = [(0, 3.5, scene_hook), (3.5, 8, scene_reveal), (8, 15, scene_features),
          (15, 18.5, scene_colors), (18.5, 21.5, scene_price), (21.5, 24, scene_cta)]

def frame_at(t):
    for a, b, fn in SCENES:
        if a <= t < b: return fn(t-a)
    return SCENES[-1][2](t-SCENES[-1][0])

# ---------------- music ----------------
def make_music(path):
    sr = 44100; n = int(sr*DUR); out = np.zeros(n)
    bpm = 120; beat = 60/bpm
    tt = np.arange(int(sr*0.4))/sr
    kick = np.sin(2*np.pi*(50+120*np.exp(-tt*30))*tt) * np.exp(-tt*9)
    rng = np.random.default_rng(0)
    th = np.arange(int(sr*0.06))/sr
    hat = rng.normal(0,1,len(th)) * np.exp(-th*70); hat = np.diff(hat, prepend=0)
    tc = np.arange(int(sr*0.2))/sr
    clap = rng.normal(0,1,len(tc)) * np.exp(-tc*25)
    roots = [57, 53, 48, 55]  # A F C G
    def add(sig, at, g):
        i = int(at*sr); j = min(n, i+len(sig))
        if i < n: out[i:j] += g*sig[:j-i]
    nb = int(DUR/beat)
    for b in range(nb):
        T = b*beat
        if T >= 0.9: add(kick, T, 0.9)
        add(hat, T+beat/2, 0.25)
        if b % 2 == 1 and T >= 0.9: add(clap, T, 0.3)
        r = roots[(b//4) % 4]
        for e in range(2):
            f = 440*2**((r-12-69)/12)
            tb = np.arange(int(sr*beat/2))/sr
            bass = np.sign(np.sin(2*np.pi*f*tb))*0.5 + np.sin(2*np.pi*f*tb)
            add(bass*np.exp(-tb*4), T+e*beat/2, 0.12 if T >= 0.9 else 0.05)
        # chord stab pluck on beats
        if b % 4 in (0, 2):
            tp = np.arange(int(sr*0.35))/sr
            chord = sum(np.sin(2*np.pi*440*2**((r+iv-69)/12)*tp) for iv in (0, 4 if r in (48,53,55) else 3, 7))
            add(chord*np.exp(-tp*8), T, 0.08)
    # whooshes at scene changes
    for a, _, _ in SCENES[1:]:
        tw = np.arange(int(sr*0.5))/sr
        w = rng.normal(0,1,len(tw)) * np.sin(np.pi*tw/0.5)**2
        w = np.convolve(w, np.ones(8)/8, mode="same")
        add(w, a-0.3, 0.25)
    fade = np.ones(n); fl = int(sr*1.0); fade[-fl:] = np.linspace(1,0,fl)
    out = np.tanh(out*1.2)*fade*0.8
    pcm = (out*32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stills":
        for t in [1.0, 3.0, 5.5, 13.0, 17.5, 20.5, 23.0]:
            frame_at(t).convert("RGB").resize((540,960)).save(f"still_{t:04.1f}.png")
        sys.exit()
    make_music("music.wav")
    out = sys.argv[1] if len(sys.argv) > 1 else "shoe_ad.mp4"
    p = subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),
                          "-i","-","-i","music.wav","-c:v","libx264","-preset","medium","-crf","20","-pix_fmt","yuv420p",
                          "-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",out], stdin=subprocess.PIPE)
    for i in range(int(DUR*FPS)):
        p.stdin.write(frame_at(i/FPS).convert("RGB").tobytes())
    p.stdin.close(); p.wait()
    print("done", out)
