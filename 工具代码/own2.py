# v4b components: standalone titles w/ light sweep + glitch, particle tunnel bg, character medallions w/ cutouts
import sys; sys.path.insert(0, '/tmp/claude-0/mock'); sys.path.insert(0, '/tmp/claude-0/build')
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import own as o, style3 as st
W, H = 1920, 1080
FC = '/tmp/claude-0/fonts/cn/'
F_TITLE = FC + '优设标题黑.ttf'; F_BRUSH = FC + '庞门正道粗书体.ttf'; F_NICK = FC + '杨任东竹石体-Heavy.ttf'
def F(p, s): return ImageFont.truetype(p, s)

def text_img(t, fp, size, fill=(255, 255, 255, 255), spacing=0.0):
    f = F(fp, size); gap = int(size * spacing); asc, desc = f.getmetrics()
    tw = int(sum(f.getlength(c) for c in t) + gap * (len(t) - 1)) + 40
    im = Image.new('RGBA', (tw, asc + desc + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 20
    for c in t: d.text((x, 20 + asc), c, font=f, fill=fill, anchor='ls'); x += f.getlength(c) + gap
    return im.crop(im.getbbox())

# ---------------- cutout (general)
import onnxruntime as ort
_is = None
def cut(img_bgr):
    global _is
    if _is is None: _is = ort.InferenceSession('/tmp/claude-0/seg/isnet.onnx', providers=['CPUExecutionProvider'])
    x = cv2.resize(img_bgr, (1024, 1024))[..., ::-1].astype(np.float32) / 255 - 0.5
    m = _is.run(None, {_is.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)})[0][0, 0]
    m = (m - m.min()) / (m.max() - m.min() + 1e-6); m = cv2.resize(m, (img_bgr.shape[1], img_bgr.shape[0]))
    m = np.clip((m - 0.3) / 0.4, 0, 1)
    n, lab, stats, _ = cv2.connectedComponentsWithStats((m > 0.5).astype(np.uint8))
    if n > 2:
        big = stats[1:, cv2.CC_STAT_AREA].max(); keep = np.zeros(n, bool); keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= big * 0.25
        m = m * cv2.dilate(keep[lab].astype(np.uint8), np.ones((9, 9), np.uint8))
    return np.dstack([img_bgr, (m * 255).astype(np.uint8)])

# ---------------- metal title (angular display font, chrome, scratches) + light sweep
def metal_title(t, size=200, spacing=0.06):
    base = o.pad(text_img(t, F_TITLE, size, (255, 255, 255, 255), spacing), 20)
    w, h = base.size; a = np.array(base.split()[3]).astype(np.float32) / 255
    y = np.linspace(0, 1, h)[:, None]
    g = np.interp(y, [0, 0.42, 0.5, 0.58, 1], [255, 228, 120, 200, 128])
    g = np.repeat(g, w, 1)
    sc = (np.random.default_rng(3).random((h, w)) > 0.996).astype(np.float32); sc = cv2.blur(sc, (31, 1)) * 8
    g = g * (0.86 + 0.14 * st.streaks(w, h, 2.0)) + np.clip(sc, 0, 1) * 70
    rgb = np.stack([g * 0.98, g * 0.99, g * 1.04], -1)
    edge = cv2.dilate(a, np.ones((5, 5), np.uint8)) - a
    rgb = rgb * (1 - edge[..., None]) + 20 * edge[..., None]
    al = np.clip(a + edge, 0, 1)
    im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), al * 255]).astype(np.uint8), 'RGBA')
    return im
def sweep(img_bgra, phase, width=0.12, strength=1.0):
    """diagonal light sweep across alpha of img; phase 0..1"""
    out = img_bgra.copy().astype(np.float32); h, w = out.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    pos = (xx / w + yy / h * 0.35) / 1.35
    band = np.exp(-((pos - (phase * 1.4 - 0.2)) / width) ** 2) * strength
    a = out[..., 3:4] / 255
    out[..., :3] = out[..., :3] + band[..., None] * 230 * a
    return np.clip(out, 0, 255).astype(np.uint8)
def glow(img_bgra, color=(255, 170, 90), r=24, k=0.7):
    a = img_bgra[..., 3].astype(np.float32) / 255
    g = cv2.GaussianBlur(a, (0, 0), r) * k
    pad = r * 3; h, w = a.shape
    out = np.zeros((h + 2 * pad, w + 2 * pad, 4), np.float32)
    gg = cv2.GaussianBlur(np.pad(a, pad), (0, 0), r) * k
    out[..., :3] = np.array(color[::-1], np.float32); out[..., 3] = gg * 255
    src = img_bgra.astype(np.float32); sa = src[..., 3:4] / 255
    reg = out[pad:pad + h, pad:pad + w]
    reg[..., :3] = src[..., :3] * sa + reg[..., :3] * (1 - sa); reg[..., 3:4] = np.maximum(reg[..., 3:4], src[..., 3:4])
    return np.clip(out, 0, 255).astype(np.uint8)

# ---------------- heavy brush title (grey-white, dry edges)
def brush_title(t, size=330, spacing=0.02, col=(236, 236, 240)):
    base = o.pad(text_img(t, F_BRUSH, size, (255, 255, 255, 255), spacing), 30)
    a = np.array(base.split()[3]).astype(np.float32) / 255; h, w = a.shape
    n = np.random.default_rng(5).random((h * 2, w * 2)).astype(np.float32); n = cv2.blur(n, (1, int(size * 0.6)))
    M = cv2.getRotationMatrix2D((w, h), -20, 1); n = cv2.warpAffine(n, M, (w * 2, h * 2))[h // 2:h // 2 + h, w // 2:w // 2 + w]
    n = (n - n.mean()) / (n.std() + 1e-6)
    dist = cv2.distanceTransform((a > 0.5).astype(np.uint8), cv2.DIST_L2, 3); band = np.clip(1 - dist / (size * 0.05), 0, 1)
    a2 = a * (1 - (n < -0.9) * band * 0.9)
    y = np.linspace(0, 1, h)[:, None]
    c = np.array(col, np.float32)[None, None] * (1 - 0.18 * y)[..., None] * (0.93 + 0.05 * np.clip(n, -1, 1))[..., None]
    return Image.fromarray(np.dstack([np.clip(c[..., ::-1][..., ::-1], 0, 255), a2 * 255]).astype(np.uint8), 'RGBA')

def glitch(frame, amt, seed=0):
    if amt <= 0: return frame
    rng = np.random.default_rng(seed); f = frame.copy(); h, w = f.shape[:2]
    sh = int(18 * amt)
    f[..., 2] = np.roll(frame[..., 2], sh, 1); f[..., 0] = np.roll(frame[..., 0], -sh, 1)
    for _ in range(int(8 * amt) + 1):
        y0 = rng.integers(0, h - 40); hh = rng.integers(10, 60); dx = int(rng.integers(-60, 60) * amt)
        f[y0:y0 + hh] = np.roll(f[y0:y0 + hh], dx, 1)
    return f

# ---------------- animated particle tunnel (our version: orange/cyan vector anchor points)
_rng = np.random.default_rng(9)
PART = []
for ring in range(26):
    n = 40 + ring * 3; r0 = ring / 26
    for k in range(n):
        PART.append((2 * np.pi * k / n + ring * 0.13, r0, 1 if (k + ring) % 5 else 0, 2.2))
def tunnel(t, tint=(255, 138, 42), base=None):
    f = (o.bg() if base is None else base.copy()).astype(np.float32) * 0.7
    ov = np.zeros((H, W, 3), np.float32); cx, cy = W / 2, H / 2
    for ang, r0, kind, sz in PART:
        r = ((r0 + t * 0.12) % 1.0); rr = (r ** 2.2) * W * 0.9 + 40
        x = cx + rr * np.cos(ang); y = cy + rr * np.sin(ang) * 0.75
        s = sz * (0.4 + 1.6 * r); a = min(1, r * 3) * 0.9
        col = np.array((tint if kind else (78, 214, 232))[::-1], np.float32) * a
        if kind: cv2.rectangle(ov, (int(x - s), int(y - s)), (int(x + s), int(y + s)), col.tolist(), -1)
        else: cv2.circle(ov, (int(x), int(y)), int(s), col.tolist(), -1, cv2.LINE_AA)
    ov = cv2.GaussianBlur(ov, (0, 0), 1.0) + cv2.GaussianBlur(ov, (0, 0), 6) * 0.6
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); v = np.sqrt(((xx - cx) / W) ** 2 + ((yy - cy) / H) ** 2)
    f = f + ov; f *= (1 - np.clip(v - 0.25, 0, 1) * 1.2)[..., None]
    return np.clip(f, 0, 255).astype(np.uint8)

def halftone_bg(img, tint=(255, 120, 40), dim=0.55, cell=8):
    b = o.cover(img, W, H); g = cv2.cvtColor(b, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    small = cv2.resize(g, (W // cell, H // cell), interpolation=cv2.INTER_AREA)
    dots = np.zeros((H, W), np.float32)
    for (yy, xx), v in np.ndenumerate(small): cv2.circle(dots, (xx * cell + cell // 2, yy * cell + cell // 2), int(v * cell * 0.6), 1.0, -1, cv2.LINE_AA)
    t = np.array(tint[::-1], np.float32)
    out = dots[..., None] * t * dim + (1 - dots[..., None]) * t * 0.08
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); v = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
    out *= (1 - np.clip(v - 0.2, 0, 1) * 1.3)[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)

# ---------------- character medallion: dark disc + cutout subject placed low + bold nickname in the empty sides
DISC = {'orange': ((120, 60, 20), (40, 20, 10)), 'violet': ((90, 50, 150), (30, 16, 56)), 'cyan': ((20, 100, 120), (8, 34, 44)), 'blue': ((40, 60, 140), (12, 18, 50))}
def char_token(d, cut_bgra, nick=None, tint='orange', name=None, subj_scale=1.0, subj_dy=0.0, nick_col=(255, 214, 170)):
    S = 2; D = d * S; lt, dk = DISC[tint]
    yy, xx = np.mgrid[0:D, 0:D].astype(np.float32); c = D / 2; r = D / 2 - 3 * S
    dist = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / r
    lit = np.clip(np.sqrt((xx - c) ** 2 + (yy - c * 0.7) ** 2) / (r * 1.3), 0, 1)
    rgb = np.zeros((D, D, 3), np.float32)
    for k in range(3): rgb[..., k] = lt[k] * (1 - lit) + dk[k] * lit
    rim = np.clip(1 - np.abs(dist - 0.975) / 0.02, 0, 1)
    rgb = rgb * (1 - rim[..., None] * 0.7) + np.array([255, 200, 150]) * rim[..., None] * 0.7
    alpha = np.clip(0.94 + rim * 0.06, 0, 1) * np.clip((1 - dist) * r / 1.5, 0, 1)
    disc = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8), 'RGBA').resize((d, d), Image.LANCZOS)
    mask = Image.new('L', (d, d), 0); ImageDraw.Draw(mask).ellipse([2, 2, d - 3, d - 3], fill=255)
    layer = Image.new('RGBA', (d, d), (0, 0, 0, 0))
    # nickname chars behind subject, inside the disc sides
    if nick:
        a, b = nick; fs = int(d * 0.33)
        for ch, side in ((a, -1), (b, 1)):
            g = text_img(ch, F_NICK, fs, nick_col + (255,))
            gl = g.filter(ImageFilter.GaussianBlur(3)); dark = Image.new('RGBA', g.size, (30, 10, 0, 200)); dark.putalpha(g.split()[3].filter(ImageFilter.MaxFilter(7)))
            x = int(d / 2 + side * d * 0.29 - g.width / 2); y = int(d * 0.40 - g.height / 2)
            layer.alpha_composite(dark, (x, y)); layer.alpha_composite(g, (x, y))
    sub = Image.fromarray(cv2.cvtColor(cut_bgra, cv2.COLOR_BGRA2RGBA))
    bb = sub.getbbox(); sub = sub.crop(bb)
    wide = sub.width > sub.height * 1.15
    s = (min(d * 0.98 / sub.width, d * 0.66 / sub.height) if wide else min(d * 0.64 / sub.width, d * 0.80 / sub.height)) * subj_scale; sub = sub.resize((max(1, int(sub.width * s)), max(1, int(sub.height * s))), Image.LANCZOS)
    layer.alpha_composite(sub, ((d - sub.width) // 2, int((d * 0.93 if wide else d * 0.97) - sub.height + d * subj_dy)))
    if name:
        nm = text_img(name, st.F_MED, int(d * 0.06), (230, 210, 200, 220), 0.1); layer.alpha_composite(nm, ((d - nm.width) // 2, int(d * 0.12)))
    clipped = Image.new('RGBA', (d, d), (0, 0, 0, 0)); clipped.paste(layer, (0, 0), Image.composite(layer.split()[3], Image.new('L', (d, d), 0), mask))
    disc.alpha_composite(clipped)
    ring = Image.new('RGBA', (d, d), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([2, 2, d - 3, d - 3], outline=(255, 190, 130, 220), width=max(2, d // 120)); disc.alpha_composite(ring)
    out = o.pad(disc, 40); a = out.split()[3]
    gl = Image.new('RGBA', out.size, (255, 140, 60, 0)); gl.putalpha(a.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * 0.45)))
    res = Image.new('RGBA', out.size, (0, 0, 0, 0)); res.alpha_composite(gl); res.alpha_composite(out)
    return st.shadow(res, 18, (0, 14), 170, 20)
