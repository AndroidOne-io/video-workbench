# "AI阿亮 · 鹈鹕考场" visual identity — own style, informed by 小Lin说's methods
import sys
sys.path.insert(0, '/tmp/claude-0/build')
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import style3 as st
from style3 import W, H, to_bgra, text, pad, shadow, stack, font

ORANGE = (255, 138, 42)      # 鹈鹕橙 — signature accent (pelican beak)
CYAN = (78, 214, 232)        # 电光青 — tech secondary
RED = (232, 64, 52)          # 红笔批改
INK = (13, 17, 30)           # base
PAPER = (246, 242, 232)      # exam paper

R = '/home/claude/aliang2052/tihuceshi'; P = R + '/分镜素材工程'

def imread(p):
    im = cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_UNCHANGED)
    if im.ndim == 2: im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
    if im.shape[2] == 4:
        a = im[..., 3:4].astype(np.float32) / 255; im = (im[..., :3] * a + 255 * (1 - a)).astype(np.uint8)
    return im
def grab(p, t):
    c = cv2.VideoCapture(p); c.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = c.read(); return f
def cover(img, w, h):
    ih, iw = img.shape[:2]; s = max(w / iw, h / ih)
    r = cv2.resize(img, (int(np.ceil(iw * s)), int(np.ceil(ih * s))), interpolation=cv2.INTER_CUBIC)
    y0 = (r.shape[0] - h) // 2; x0 = (r.shape[1] - w) // 2
    return np.ascontiguousarray(r[y0:y0 + h, x0:x0 + w])
def blit(dst, src, x, y, a=1.0):
    if not isinstance(src, np.ndarray): src = to_bgra(src)
    h, w = src.shape[:2]; x, y = int(x), int(y)
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x]
    al = (s[..., 3:4].astype(np.float32) / 255 if s.shape[2] == 4 else np.ones(s.shape[:2] + (1,), np.float32)) * a
    dst[y0:y1, x0:x1, :3] = (s[..., :3] * al + dst[y0:y1, x0:x1, :3] * (1 - al)).astype(np.uint8)
def put(dst, im, cx, cy, a=1.0):
    if not isinstance(im, np.ndarray): im = to_bgra(im)
    blit(dst, im, cx - im.shape[1] // 2, cy - im.shape[0] // 2, a)

# ------------------------------------------------------------------ background: blueprint / vector-construction
_bg = {}
def bg(backdrop=None, dim=0.18, tint='ink', key=None):
    k = key or (tint, id(backdrop) if backdrop is not None else None, dim)
    if k in _bg: return _bg[k].copy()
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    base = {'ink': (30, 17, 13), 'warm': (22, 18, 26), 'red': (26, 16, 34)}[tint]
    img = np.zeros((H, W, 3), np.float32); img[:] = base
    if backdrop is not None:
        b = cover(backdrop, W, H).astype(np.float32); g = b.mean(2, keepdims=True)
        b = cv2.GaussianBlur(g * 0.75 + b * 0.25, (0, 0), 2)
        img = img * (1 - dim) + b * dim
    # orange-ish warm glow low-left + cyan glow up-right
    d1 = np.sqrt(((x - W * 0.2) / W) ** 2 + ((y - H * 0.85) / H) ** 2)
    d2 = np.sqrt(((x - W * 0.8) / W) ** 2 + ((y - H * 0.2) / H) ** 2)
    img += (np.clip(0.55 - d1, 0, 1) ** 2 * 0.9)[..., None] * np.array(ORANGE[::-1], np.float32) * 0.35
    img += (np.clip(0.6 - d2, 0, 1) ** 2 * 0.9)[..., None] * np.array(CYAN[::-1], np.float32) * 0.28
    # dot grid
    dots = ((x.astype(int) % 40 == 0) & (y.astype(int) % 40 == 0)).astype(np.float32)
    dots = cv2.dilate(dots, np.ones((2, 2), np.uint8))
    img += dots[..., None] * 22
    # vector construction: bezier curves with anchor squares & handles (SVG motif)
    ov = np.zeros((H, W), np.float32)
    rng = np.random.default_rng(7)
    for _ in range(3):
        p0 = np.array([rng.uniform(-200, 400), rng.uniform(0, H)]); p3 = np.array([rng.uniform(W - 400, W + 200), rng.uniform(0, H)])
        p1 = p0 + [rng.uniform(300, 700), rng.uniform(-500, 500)]; p2 = p3 + [rng.uniform(-700, -300), rng.uniform(-500, 500)]
        t = np.linspace(0, 1, 400)[:, None]
        pts = ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3).astype(np.int32)
        cv2.polylines(ov, [pts], False, 1.0, 1, cv2.LINE_AA)
        for a_, h_ in [(p0, p1), (p3, p2)]:
            cv2.line(ov, tuple(a_.astype(int)), tuple(h_.astype(int)), 0.6, 1, cv2.LINE_AA)
            cv2.rectangle(ov, tuple((a_ - 5).astype(int)), tuple((a_ + 5).astype(int)), 1.0, 1)
            cv2.circle(ov, tuple(h_.astype(int)), 4, 1.0, 1, cv2.LINE_AA)
    img += ov[..., None] * np.array(CYAN[::-1], np.float32) * 0.18
    fab = st.streaks(W, H, 0.1) * 0.5 + st.streaks(W, H, 0.1, False) * 0.5
    img *= (0.95 + 0.1 * fab)[..., None]
    img += np.random.default_rng(1).normal(0, 2, img.shape)
    v = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H / 2) / H) ** 2)
    img *= (1 - np.clip(v - 0.32, 0, 1) * 1.0)[..., None]
    out = np.clip(img, 0, 255).astype(np.uint8); _bg[k] = out; return out.copy()

# ------------------------------------------------------------------ token: translucent glass disc + vector-anchor ring (signature)
TINT = {'orange': ((255, 176, 96), (196, 82, 18)), 'cyan': ((120, 228, 240), (20, 110, 140)), 'blue': ((120, 160, 255), (36, 64, 170)),
        'green': ((130, 226, 160), (24, 120, 72)), 'grey': ((170, 176, 196), (60, 66, 86)), 'red': ((255, 130, 120), (150, 30, 30)),
        'violet': ((180, 140, 255), (80, 50, 170)), 'paper': ((255, 250, 236), (200, 190, 170))}
def token(d, tint='cyan', title='', sub='', top=None, portrait=None, nick=None, anchors=True, active=1.0, title_size=None, num=None):
    S = 2; D = d * S; lt, dk = TINT[tint]
    yy, xx = np.mgrid[0:D, 0:D].astype(np.float32); c = D / 2; r = D / 2 - 3 * S
    dist = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / r
    lit = np.clip(np.sqrt((xx - c * 0.55) ** 2 + (yy - c * 0.4) ** 2) / (r * 1.8), 0, 1)
    rgb = np.zeros((D, D, 3), np.float32)
    for k in range(3): rgb[..., k] = lt[k] * (1 - lit) + dk[k] * lit
    body = 0.5 + 0.25 * dist ** 3
    if portrait is not None:
        p = cv2.cvtColor(cover(portrait, D, D), cv2.COLOR_BGR2RGB).astype(np.float32)
        rgb = p * 0.88 + np.array(dk, np.float32) * 0.12; body = np.ones_like(dist) * 0.98
    if active < 1:
        g = rgb.mean(2, keepdims=True); rgb = rgb * active + g * 0.5 * (1 - active); body = body * (0.55 + 0.45 * active)
    rim = np.clip(1 - np.abs(dist - 0.975) / 0.022, 0, 1)
    rgb = rgb * (1 - rim[..., None] * 0.8) + 255 * rim[..., None] * 0.8
    spec = np.clip(1 - ((xx - c) ** 2 / (r * 0.7) ** 2 + (yy - c * 0.42) ** 2 / (r * 0.3) ** 2), 0, 1) ** 2 * 0.14 * (yy < c)
    rgb += 255 * spec[..., None]
    alpha = np.clip(body + rim * 0.5, 0, 0.97) * np.clip((1 - dist) * r / 1.5, 0, 1)
    im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8), 'RGBA').resize((d, d), Image.LANCZOS)
    tc = (250, 250, 255, int(240 * (0.55 + 0.45 * active)))
    if portrait is None:
        blk = []
        if top is not None: blk.append(top)
        if title:
            ts = title_size or int(d * (0.22 if len(title) <= 3 else 0.16 if len(title) <= 6 else 0.12))
            blk.append(text(title, st.F_BLACK if any(ord(ch) > 127 for ch in title) else st.F_BOLD, ts, tc, 0.06 if any(ord(ch) > 127 for ch in title) else 0.02))
        if sub: blk.append(text(sub, st.F_MED, max(14, int(d * 0.075)), (255, 255, 255, int(190 * (0.55 + 0.45 * active))), 0.12))
        if blk:
            b = stack(blk, gap=int(d * 0.03))
            if b.width > d * 0.8: s = d * 0.8 / b.width; b = b.resize((int(b.width * s), int(b.height * s)), Image.LANCZOS)
            im.alpha_composite(b, (int((d - b.width) / 2), int(d / 2 - b.height / 2)))
    m = int(d * 0.12); out = pad(im, m)
    dr = ImageDraw.Draw(out)
    if anchors:  # vector selection ring with anchor squares — signature
        rr = d / 2 + m * 0.45; cx = cy = out.width / 2
        dr.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=ORANGE + (int(220 * active),), width=2)
        for ang in (0, 90, 180, 270):
            ax = cx + rr * np.cos(np.radians(ang)); ay = cy + rr * np.sin(np.radians(ang)); q = max(5, d // 40)
            dr.rectangle([ax - q, ay - q, ax + q, ay + q], fill=(20, 20, 28, 255), outline=ORANGE + (255,), width=2)
    if nick:
        a_, b_ = nick
        sz = int(d * 0.5)
        ga = brush_word(a_, sz, col=(255, 214, 170)); gb = brush_word(b_, sz, col=(255, 214, 170))
        ex = max(ga.width, gb.width) // 2
        out2 = Image.new('RGBA', (out.width + 2 * ex, out.height), (0, 0, 0, 0)); out2.alpha_composite(out, (ex, 0)); out = out2
        cy_ = out.height // 2
        out.alpha_composite(ga, (int(out.width / 2 - d * 0.5 - ga.width / 2), cy_ - ga.height // 2))
        out.alpha_composite(gb, (int(out.width / 2 + d * 0.5 - gb.width / 2), cy_ - gb.height // 2))
    if num is not None:
        nb = max(40, d // 6); bd = Image.new('RGBA', (nb, nb), (0, 0, 0, 0)); q = ImageDraw.Draw(bd)
        q.ellipse([0, 0, nb - 1, nb - 1], fill=(20, 20, 28, 240), outline=ORANGE + (255,), width=3)
        n = text(str(num), st.F_BEBAS, int(nb * 0.8), (255, 255, 255)); bd.alpha_composite(n, ((nb - n.width) // 2, (nb - n.height) // 2))
        out.alpha_composite(bd, (out.width // 2 - nb // 2, 0))
    a = out.split()[3]
    glow = Image.new('RGBA', out.size, dk + (0,)); glow.putalpha(a.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.5 * active)))
    res = Image.new('RGBA', out.size, (0, 0, 0, 0)); res.alpha_composite(glow); res.alpha_composite(out)
    return shadow(res, 16, (0, 14), 160, 24)

# ------------------------------------------------------------------ brush title (warm white, with orange "red-pen" underline)
def brush_word(t, size, glow=True, underline=False, col=None):
    im = st.brush(t, size)  # already shadowed
    if col is not None:
        a = np.array(im).astype(np.float32); a[..., :3] = a[..., :3] / 255 * np.array(col, np.float32); im = Image.fromarray(a.astype(np.uint8))
    if underline:
        w = im.width; o = Image.new('RGBA', (w, im.height + int(size * 0.25)), (0, 0, 0, 0)); o.alpha_composite(im, (0, 0))
        d = ImageDraw.Draw(o); y = im.height - int(size * 0.18)
        pts = [(w * 0.08 + i * w * 0.84 / 30, y + np.sin(i / 3) * size * 0.02) for i in range(31)]
        d.line(pts, fill=ORANGE + (235,), width=max(6, size // 18), joint='curve')
        im = o
    return im

def stamp(t, color=RED, size=150, angle=-10): return st.stamp(t, color, size, angle)

def paper_card(w, h, lines=True, title=None):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 14, fill=PAPER + (255,))
    if lines:
        for y in range(150, h - 40, 64): d.line([60, y, w - 60, y], fill=(200, 200, 210, 255), width=2)
    if title:
        d.rectangle([0, 0, w - 1, 100], fill=(236, 228, 210, 255)); d.line([0, 100, w, 100], fill=(210, 196, 170, 255), width=2)
    if title: im.alpha_composite(text(title, st.F_BLACK, 50, (60, 50, 40), 0.3), (60, 22))
    a = np.array(im).astype(np.float32); n = st.streaks(w, h, 0.05) * 0.5 + 0.5
    a[..., :3] *= (0.97 + 0.04 * n)[..., None]
    return shadow(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), 20, (0, 14), 170, 40)

def big_card(w, h, tint=(28, 30, 46), border=ORANGE):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 26, fill=tint + (232,), outline=border + (200,), width=3)
    d.line([30, 3, w - 30, 3], fill=(255, 255, 255, 70), width=1)
    return im

def name_card(en, role, nick=None):
    t1 = text(en, st.F_LIGHT, 80, (248, 248, 252), 0.05); r = text(role, st.F_MED, 38, (226, 222, 236), 0.2) if role else Image.new('RGBA', (1, 1))
    w = max(t1.width, r.width) + 130; h = t1.height + (r.height + 90 if role else 60)
    c = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 16, fill=(10, 12, 20, 190), outline=(255, 255, 255, 40), width=2)
    d.rectangle([0, 18, 8, h - 18], fill=ORANGE + (255,))
    c.alpha_composite(t1, (56, 26))
    if role: d.line([56, 40 + t1.height, w - 40, 40 + t1.height], fill=(255, 255, 255, 110), width=2); c.alpha_composite(r, (56, 56 + t1.height))
    out = pad(c, 40)
    if nick:
        nk = brush_word(nick, 150, col=ORANGE)
        big = Image.new('RGBA', (out.width + nk.width // 2, out.height + nk.height // 2), (0, 0, 0, 0))
        big.alpha_composite(out, (0, 0)); big.alpha_composite(nk, (big.width - nk.width, big.height - nk.height))
        out = big
    return shadow(out, 14, (0, 8), 150, 10)

def arrow(dst, p0, p1, col=ORANGE, w=5, dashed=False):
    c = col[::-1]
    p0 = np.array(p0, float); p1 = np.array(p1, float); v = p1 - p0; L = np.linalg.norm(v); u = v / L
    if dashed:
        for s in np.arange(0, L - 30, 26):
            a = p0 + u * s; b = p0 + u * min(s + 14, L - 30); cv2.line(dst, tuple(a.astype(int)), tuple(b.astype(int)), c, w, cv2.LINE_AA)
    else:
        cv2.line(dst, tuple(p0.astype(int)), tuple((p1 - u * 20).astype(int)), c, w, cv2.LINE_AA)
    n = np.array([-u[1], u[0]]); tip = p1; b1 = p1 - u * 34 + n * 16; b2 = p1 - u * 34 - n * 16
    cv2.fillPoly(dst, [np.array([tip, b1, b2]).astype(np.int32)], c, cv2.LINE_AA)

def red_circle(dst, cx, cy, rx, ry, w=9, ang=-8):
    pts = []
    for i in range(0, 380, 4):
        t = np.radians(i); jitter = 1 + 0.04 * np.sin(i / 23)
        pts.append((cx + rx * jitter * np.cos(t), cy + ry * jitter * np.sin(t) + i * 0.08))
    M = cv2.getRotationMatrix2D((cx, cy), ang, 1)
    pts = cv2.transform(np.array([pts], np.float32), M)[0].astype(np.int32)
    cv2.polylines(dst, [pts], False, RED[::-1], w, cv2.LINE_AA)
def red_x(dst, cx, cy, s, w=14):
    cv2.line(dst, (int(cx - s), int(cy - s)), (int(cx + s), int(cy + s * 0.9)), RED[::-1], w, cv2.LINE_AA)
    cv2.line(dst, (int(cx + s * 0.95), int(cy - s * 1.05)), (int(cx - s * 0.9), int(cy + s)), RED[::-1], w, cv2.LINE_AA)

# ------------------------------------------------------------------ host + cutout
import onnxruntime as ort
_seg = None
def host(t, z=1.0):
    f = grab(R + '/口播粗剪.mp4', t)
    w, h = 1280 / z, 720 / z; x0 = 640 - w / 2; y0 = max(0, min(720 - h, 230 - h * 0.3))
    M = np.float32([[W / w, 0, -x0 * W / w], [0, H / h, -y0 * H / h]])
    return cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
def cutout(frame):
    global _seg
    if _seg is None: _seg = ort.InferenceSession('/tmp/claude-0/seg/u2h.onnx', providers=['CPUExecutionProvider'])
    x = cv2.resize(frame, (320, 320))[..., ::-1].astype(np.float32) / 255
    x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
    o = _seg.run(None, {_seg.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    o = (o - o.min()) / (o.max() - o.min()); m = cv2.resize(o, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_LINEAR)
    m = np.clip((m - 0.35) / 0.3, 0, 1); m = cv2.GaussianBlur(m, (0, 0), 1.2)
    return np.dstack([frame, (m * 255).astype(np.uint8)])

def subtitle(dst, t):
    im = to_bgra(st.subtitle(t)); blit(dst, im, (W - im.shape[1]) // 2, H - 56 - im.shape[0])
def pip(dst, hf, x=60, y=None, d=290):
    y = H - 60 - d if y is None else y
    sq = cv2.resize(hf[40:540, 390:890] if hf.shape[0] == 720 else cv2.resize(hf, (1280, 720))[40:540, 390:890], (d, d), interpolation=cv2.INTER_AREA).astype(np.float32)
    m = np.zeros((d, d), np.float32); cv2.circle(m, (d // 2, d // 2), d // 2 - 4, 1, -1, cv2.LINE_AA); m = cv2.GaussianBlur(m, (0, 0), 2)[..., None]
    sh = np.zeros((d + 80, d + 80), np.float32); cv2.circle(sh, ((d + 80) // 2, (d + 80) // 2 + 10), d // 2, 0.6, -1); sh = cv2.GaussianBlur(sh, (0, 0), 18)[..., None]
    reg = dst[y - 40:y + d + 40, x - 40:x + d + 40].astype(np.float32); dst[y - 40:y + d + 40, x - 40:x + d + 40] = (reg * (1 - sh)).astype(np.uint8)
    reg = dst[y:y + d, x:x + d].astype(np.float32); dst[y:y + d, x:x + d] = (sq * m + reg * (1 - m)).astype(np.uint8)
    cv2.circle(dst, (x + d // 2, y + d // 2), d // 2 + 6, ORANGE[::-1], 2, cv2.LINE_AA)
