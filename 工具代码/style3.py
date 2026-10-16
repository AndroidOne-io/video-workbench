# v3 design system — modelled on reference style 2 (小Lin说)
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont
W, H = 1920, 1080
FD = '/tmp/claude-0/fonts/'
F_SMILEY = FD + 'smiley/SmileySans-Oblique.ttf'
F_BRUSH = FD + 'gf/ofl/mashanzheng/MaShanZheng-Regular.ttf'
F_BEBAS = FD + 'gf/ofl/bebasneue/BebasNeue-Regular.ttf'
F_BLACK = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
F_BOLD = '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
F_MED = '/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc'
F_LIGHT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Light.ttc'
F_DEMI = '/usr/share/fonts/opentype/noto/NotoSansCJK-DemiLight.ttc'
F_MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
F_EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
LAV = (201, 168, 255)
_fc = {}
def font(p, s):
    k = (p, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(p, s, index=2 if p.endswith('.ttc') else 0)
    return _fc[k]

def to_bgra(im): return cv2.cvtColor(np.array(im.convert('RGBA')), cv2.COLOR_RGBA2BGRA)
def to_pil(bgra): return Image.fromarray(cv2.cvtColor(bgra, cv2.COLOR_BGRA2RGBA))

def text(t, fp, size, fill=(255, 255, 255), spacing=0.0, stroke=0, stroke_fill=(0, 0, 0)):
    f = font(fp, size)
    if spacing == 0:
        bb = f.getbbox(t, stroke_width=stroke)
        im = Image.new('RGBA', (bb[2] - bb[0] + 8 + 2 * stroke, bb[3] - bb[1] + 8 + 2 * stroke), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((4 - bb[0] + stroke, 4 - bb[1] + stroke), t, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        return im
    f = font(fp, size); gap = int(size * spacing)
    asc, desc = f.getmetrics()
    tw = int(sum(f.getlength(ch) for ch in t) + gap * (len(t) - 1)) + 8 + 2 * stroke
    im = Image.new('RGBA', (tw, asc + desc + 8 + 2 * stroke), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 4 + stroke
    for ch in t:
        d.text((x, 4 + stroke + asc), ch, font=f, fill=fill, anchor='ls', stroke_width=stroke, stroke_fill=stroke_fill)
        x += f.getlength(ch) + gap
    bb = im.getbbox()
    return im.crop((0, bb[1], im.width, bb[3])) if bb else im

def pad(im, p):
    o = Image.new('RGBA', (im.width + 2 * p, im.height + 2 * p), (0, 0, 0, 0)); o.alpha_composite(im, (p, p)); return o

def shadow(im, r=14, off=(0, 8), a=150, p=30):
    s = Image.new('RGBA', (im.width + 2 * p, im.height + 2 * p), (0, 0, 0, 0))
    m = im.split()[3].point(lambda v: v * a // 255)
    blk = Image.new('RGBA', im.size, (0, 0, 0, 255)); blk.putalpha(m)
    s.alpha_composite(blk, (p + off[0], p + off[1])); s = s.filter(ImageFilter.GaussianBlur(r))
    s.alpha_composite(im, (p, p)); return s

def stack(ims, align='c', gap=0):
    w = max(i.width for i in ims); h = sum(i.height for i in ims) + gap * (len(ims) - 1)
    o = Image.new('RGBA', (w, h), (0, 0, 0, 0)); y = 0
    for i in ims:
        o.alpha_composite(i, ({'c': (w - i.width) // 2, 'l': 0, 'r': w - i.width}[align], y)); y += i.height + gap
    return o

def grad_fill(mask, stops):
    w, h = mask.size; pos = np.linspace(0, 1, h); cols = np.zeros((h, 3))
    for c in range(3): cols[:, c] = np.interp(pos, [s[0] for s in stops], [s[1][c] for s in stops])
    arr = np.zeros((h, w, 4), np.uint8); arr[..., :3] = cols[:, None, :].astype(np.uint8); arr[..., 3] = np.array(mask.split()[3])
    return Image.fromarray(arr, 'RGBA')

_rng = np.random.default_rng(11)
def streaks(w, h, scale=1.0, horiz=True):
    n = _rng.random((h, w)).astype(np.float32)
    k = (1, max(3, int(61 * scale))) if horiz else (max(3, int(61 * scale)), 1)
    n = cv2.blur(n, k); n = (n - n.min()) / (n.max() - n.min() + 1e-6)
    return n

# ------------------------------------------------------------------ title types
def metal(t, size=160, spacing=0.16, tint='silver', top=None, bottom=None):
    base = pad(text(t, F_BLACK, size, (255, 255, 255), spacing), 14)
    base = base.resize((int(base.width * 0.92), base.height), Image.LANCZOS)
    st = {'silver': [(0, (250, 250, 252)), (0.45, (214, 216, 224)), (0.52, (128, 130, 142)), (0.62, (196, 198, 210)), (1, (112, 114, 128))],
          'gold': [(0, (255, 246, 214)), (0.45, (238, 210, 140)), (0.52, (150, 112, 44)), (0.62, (226, 188, 108)), (1, (140, 98, 30))]}[tint]
    g = grad_fill(base, st)
    a = np.array(g).astype(np.float32)
    s = streaks(base.width, base.height, 1.5)
    a[..., :3] *= (0.82 + 0.3 * s)[..., None]
    scratches = (_rng.random((base.height, base.width)) > 0.9965).astype(np.float32)
    scratches = cv2.blur(scratches, (1, 25)) * 6
    a[..., :3] += (np.clip(scratches, 0, 1) * 60)[..., None]
    g = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    edge = Image.new('RGBA', base.size, (18, 18, 26, 255)); edge.putalpha(base.split()[3].filter(ImageFilter.MaxFilter(5)))
    o = Image.new('RGBA', base.size, (0, 0, 0, 0)); o.alpha_composite(edge); o.alpha_composite(g)
    parts = []
    if top: parts.append(text(top, F_MED, int(size * 0.24), (225, 225, 232), 0.35))
    parts.append(o)
    if bottom: parts.append(text(bottom, F_LIGHT, int(size * 0.13), (190, 190, 200), 0.18))
    return shadow(stack(parts, gap=int(size * 0.08)), 18, (0, 10), 200, 34)

def brush(t, size=300, sub=None):
    """dry-brush calligraphy (飞白): ragged edges + directional streak gaps, grey-white"""
    base = pad(text(t, F_BRUSH, size, (255, 255, 255), 0), 50)
    A = np.array(base.split()[3]).astype(np.float32) / 255
    k = max(3, int(size / 26)) | 1
    A = cv2.dilate(A, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    h, w = A.shape
    # ragged edge: displace by low-freq noise
    nx = cv2.GaussianBlur(_rng.random((h, w)).astype(np.float32), (0, 0), 2) * 6 - 3
    ny = cv2.GaussianBlur(_rng.random((h, w)).astype(np.float32), (0, 0), 2) * 6 - 3
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    amp = size / 45
    A = cv2.remap(A, gx + nx * amp, gy + ny * amp, cv2.INTER_LINEAR)
    # directional streaks (brush hairs) at ~ -25 deg
    n = _rng.random((h * 2, w * 2)).astype(np.float32)
    n = cv2.blur(n, (1, int(size * 0.9)))
    M = cv2.getRotationMatrix2D((w, h), -25, 1.0)
    n = cv2.warpAffine(n, M, (w * 2, h * 2))[h // 2:h // 2 + h, w // 2:w // 2 + w]
    n = (n - n.mean()) / (n.std() + 1e-6)
    dist = cv2.distanceTransform((A > 0.5).astype(np.uint8), cv2.DIST_L2, 3)
    band = np.clip(1 - dist / (size * 0.06), 0, 1)  # 1 near edges
    gaps = (n < -0.75).astype(np.float32) * (0.15 + 0.85 * band ** 1.5)
    A2 = np.clip(A * (1 - gaps), 0, 1)
    A2 = cv2.GaussianBlur(A2, (3, 3), 0)
    col = np.zeros((h, w, 3), np.float32)
    gyv = np.linspace(0, 1, h)[:, None]
    col[:] = (242 - 48 * gyv)[..., None]
    col *= (0.9 + 0.08 * np.clip(n, -1, 1))[..., None]
    arr = np.dstack([np.clip(col, 0, 255), A2 * 255]).astype(np.uint8)
    im = Image.fromarray(arr, 'RGBA'); im = im.crop(im.getbbox())
    out = im
    if sub:
        sb = text(sub, F_SMILEY, int(size * 0.24), (232, 232, 238))
        out = Image.new('RGBA', (im.width, im.height + sb.height // 2), (0, 0, 0, 0))
        out.alpha_composite(im, (0, 0)); out.alpha_composite(sb, (im.width - sb.width - 10, out.height - sb.height))
    return shadow(out, 20, (0, 10), 220, 40)

def number(num, unit='', cap='', color=(255, 255, 255), size=200, unit_col=(245, 214, 120)):
    n = text(num, F_BEBAS, size, color)
    row = [n]
    if unit:
        u = text(unit, F_SMILEY, int(size * 0.32), unit_col)
        r = Image.new('RGBA', (n.width + u.width + 10, n.height), (0, 0, 0, 0))
        r.alpha_composite(n, (0, 0)); r.alpha_composite(u, (n.width + 10, n.height - u.height - int(size * 0.04)))
        n = r
    parts = []
    if cap: parts.append(text(cap, F_MED, int(size * 0.17), (220, 220, 230), 0.25))
    parts.append(n)
    return shadow(stack(parts, gap=int(size * 0.04)), 14, (0, 8), 190, 26)

def stamp(t, color=(214, 38, 46), size=120, angle=-9):
    tx = text(t, F_BLACK, size, color + (255,), 0.06)
    p = int(size * 0.22); bw = max(6, size // 14)
    w, h = tx.width + 2 * p, tx.height + 2 * p
    im = Image.new('RGBA', (w + 2 * bw, h + 2 * bw), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width - 1, im.height - 1], outline=color + (255,), width=bw)
    d.rectangle([bw * 2, bw * 2, im.width - 1 - bw * 2, im.height - 1 - bw * 2], outline=color + (255,), width=max(2, bw // 3))
    im.alpha_composite(tx, (bw + p, bw + p))
    a = np.array(im).astype(np.float32)
    g = _rng.random(a.shape[:2]).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 1.6); g = (g - g.min()) / (g.max() - g.min())
    holes = (g < 0.30).astype(np.float32)
    a[..., 3] *= (1 - holes * 0.9) * (0.88 + 0.12 * _rng.random(a.shape[:2]))
    im = Image.fromarray(a.astype(np.uint8), 'RGBA').rotate(angle, resample=Image.BICUBIC, expand=True)
    return im

def sticker(src, size=260, border=12, angle=0):
    """src: PIL RGBA (emoji/cutout) -> white-outlined sticker"""
    s = size / max(src.size); im = src.resize((max(1, int(src.width * s)), max(1, int(src.height * s))), Image.LANCZOS)
    im = pad(im, border + 4)
    a = im.split()[3].point(lambda v: 255 if v > 40 else 0).filter(ImageFilter.MaxFilter(border * 2 + 1)).filter(ImageFilter.GaussianBlur(1.2))
    wht = Image.new('RGBA', im.size, (255, 255, 255, 255)); wht.putalpha(a)
    o = Image.new('RGBA', im.size, (0, 0, 0, 0)); o.alpha_composite(wht); o.alpha_composite(im)
    if angle: o = o.rotate(angle, resample=Image.BICUBIC, expand=True)
    return shadow(o, 10, (0, 8), 150, 20)

def photo_card(bgr, w, border=10, radius=14, angle=0):
    h = int(bgr.shape[0] * w / bgr.shape[1])
    im = Image.fromarray(cv2.cvtColor(cv2.resize(bgr, (w, h), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)).convert('RGBA')
    card = Image.new('RGBA', (w + 2 * border, h + 2 * border), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([0, 0, card.width - 1, card.height - 1], radius, fill=(255, 255, 255, 255))
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], max(2, radius - border // 2), fill=255)
    card.paste(im, (border, border), m)
    if angle: card = card.rotate(angle, resample=Image.BICUBIC, expand=True)
    return shadow(card, 18, (0, 12), 170, 36)

def emoji(ch, size=200):
    f = ImageFont.truetype(F_EMOJI, 109)
    im = Image.new('RGBA', (150, 150), (0, 0, 0, 0)); ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox()); s = size / max(im.size)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)

# ------------------------------------------------------------------ glass medallion (translucent)
TINTS = {'purple': ((150, 110, 255), (84, 50, 190)), 'blue': ((110, 160, 255), (40, 80, 190)),
         'green': ((110, 220, 170), (30, 120, 90)), 'gold': ((255, 226, 140), (170, 120, 30)),
         'grey': ((170, 176, 196), (70, 76, 96)), 'teal': ((110, 220, 220), (30, 110, 120)), 'red': ((255, 130, 130), (160, 40, 50))}
def glass(d, tint='purple', title='', sub='', top=None, number=None, active=1.0, title_size=None):
    S = 2; D = d * S
    lt, dk = TINTS[tint]
    yy, xx = np.mgrid[0:D, 0:D].astype(np.float32); c = D / 2; r = D / 2 - 3 * S
    dist = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / r
    lit = np.clip(np.sqrt((xx - c * 0.6) ** 2 + (yy - c * 0.45) ** 2) / (r * 1.7), 0, 1)
    rgb = np.zeros((D, D, 3), np.float32)
    for k in range(3): rgb[..., k] = lt[k] * (1 - lit) + dk[k] * lit
    if active < 1:
        g = rgb.mean(2, keepdims=True); rgb = rgb * active + (g * 0.55 + 20) * (1 - active)
    # alpha: translucent body, brighter rim
    body = (0.42 + 0.22 * dist ** 3) * (0.55 + 0.45 * active)
    rim = np.clip(1 - np.abs(dist - 0.975) / 0.025, 0, 1)
    inner = np.clip(1 - np.abs(dist - 0.905) / 0.006, 0, 1)
    rgb = rgb * (1 - rim[..., None] * 0.75) + 255 * rim[..., None] * 0.75
    rgb = rgb * (1 - inner[..., None] * 0.3) + 255 * inner[..., None] * 0.3
    alpha = np.clip(body + rim * 0.5 + inner * 0.25, 0, 0.95) * np.clip((1 - dist) * r / 1.5, 0, 1)
    arr = np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)
    im = Image.fromarray(arr, 'RGBA').resize((d, d), Image.LANCZOS)
    dr = ImageDraw.Draw(im)
    tc = (236, 238, 250, int(235 * (0.6 + 0.4 * active)))
    blk = []
    if top is not None: blk.append(top)
    if title:
        ts = title_size or int(d * (0.2 if len(title) <= 3 else 0.15))
        blk.append(text(title, F_MED, ts, tc, 0.12))
    if sub: blk.append(text(sub.upper(), F_DEMI, max(11, int(d * 0.05)), (230, 230, 245, int(150 * (0.6 + 0.4 * active))), 0.25))
    if blk:
        b = stack(blk, gap=int(d * 0.035))
        if b.width > d * 0.76: s = d * 0.76 / b.width; b = b.resize((int(b.width * s), int(b.height * s)), Image.LANCZOS)
        y0 = int(d / 2 - b.height / 2)
        # ornament line
        y_or = y0 - int(d * 0.06)
        x = d / 2 - d * 0.2
        while x < d / 2 + d * 0.2:
            dr.line([x, y_or, x + 3, y_or], fill=(255, 255, 255, 90), width=1); x += 7
        dr.polygon([(d / 2, y_or - 5), (d / 2 + 5, y_or), (d / 2, y_or + 5), (d / 2 - 5, y_or)], outline=(255, 255, 255, 140))
        im.alpha_composite(b, (int((d - b.width) / 2), y0))
    out = pad(im, 28)
    if number is not None:
        nb = max(34, d // 7); bd = Image.new('RGBA', (nb, nb), (0, 0, 0, 0)); q = ImageDraw.Draw(bd)
        q.ellipse([0, 0, nb - 1, nb - 1], fill=dk + (200,), outline=(255, 255, 255, 220), width=2)
        n = text(str(number), F_BEBAS, int(nb * 0.8), (255, 255, 255)); bd.alpha_composite(n, ((nb - n.width) // 2, (nb - n.height) // 2))
        out.alpha_composite(bd, (28 + d // 2 - nb // 2, 28 - nb // 2 + 4))
    a = out.split()[3]
    glow = Image.new('RGBA', out.size, dk + (0,)); glow.putalpha(a.filter(ImageFilter.GaussianBlur(16)).point(lambda v: int(v * 0.5 * active)))
    res = Image.new('RGBA', out.size, (0, 0, 0, 0)); res.alpha_composite(glow); res.alpha_composite(out)
    return res

def plate(label, value, unit='', size=58):
    l = text(label, F_MED, int(size * 0.5), (205, 205, 215))
    v = text(value, F_BEBAS, size, (255, 255, 255))
    u = text(unit, F_SMILEY, int(size * 0.42), (245, 214, 120)) if unit else None
    w = l.width + v.width + (u.width + 8 if u else 0) + 90; h = max(v.height, l.height) + 26
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(10, 12, 18, 225), outline=(170, 175, 195, 130), width=2)
    for (x, y, dx, dy) in [(4, 4, 1, 1), (w - 5, 4, -1, 1), (4, h - 5, 1, -1), (w - 5, h - 5, -1, -1)]:
        d.line([x, y, x + 10 * dx, y], fill=(220, 220, 235, 200), width=2); d.line([x, y, x, y + 10 * dy], fill=(220, 220, 235, 200), width=2)
    im.alpha_composite(l, (24, (h - l.height) // 2))
    d.line([l.width + 40, 10, l.width + 40, h - 10], fill=(170, 175, 195, 150), width=1)
    im.alpha_composite(v, (l.width + 58, (h - v.height) // 2))
    if u: im.alpha_composite(u, (l.width + 58 + v.width + 8, h - u.height - 14))
    return shadow(im, 12, (0, 8), 160, 24)

def tab(cn, en=''):
    t = text(cn, F_MED, 30, (238, 240, 250), 0.1); e = text(en.upper(), F_DEMI, 13, (150, 160, 190), 0.2) if en else None
    w = max(t.width, e.width if e else 0) + 70; h = 72 if e else 56
    im = Image.new('RGBA', (w + 24, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(0, 0), (w + 22, 0), (w, h - 1), (0, h - 1)], fill=(16, 22, 40, 215), outline=(120, 140, 200, 140))
    im.alpha_composite(t, (26, 8));
    if e: im.alpha_composite(e, (28, 12 + t.height))
    return shadow(im, 8, (0, 5), 130, 14)

def name_card(en, role, nick=None):
    t1 = text(en, F_LIGHT, 60, (246, 246, 250), 0.06); r = text(role, F_DEMI, 30, (215, 210, 230), 0.22)
    w = max(t1.width, r.width) + 110; h = t1.height + r.height + 76
    c = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 14, fill=(8, 8, 12, 175), outline=(255, 255, 255, 28), width=2)
    c.alpha_composite(t1, (48, 24)); d.line([48, 30 + t1.height + 10, w - 36, 30 + t1.height + 10], fill=(255, 255, 255, 90), width=2)
    c.alpha_composite(r, (48, 30 + t1.height + 26))
    out = pad(c, 30)
    if nick:
        nk = comic(nick, 74)
        big = Image.new('RGBA', (out.width + nk.width // 3, out.height + nk.height // 2), (0, 0, 0, 0))
        big.alpha_composite(out, (0, 0)); big.alpha_composite(nk, (big.width - nk.width, big.height - nk.height))
        out = big
    return shadow(out, 14, (0, 8), 150, 10)

def comic(t, size=80, tilt=-4):
    core = text(t, F_BLACK, size, (255, 255, 255)); sw = max(3, int(size * 0.07))
    out_ = text(t, F_BLACK, size, (90, 12, 6), 0, sw, (90, 12, 6))
    core = pad(core, sw)
    g = grad_fill(core, [(0, (255, 250, 160)), (0.5, (255, 206, 40)), (1, (240, 100, 16))])
    o = Image.new('RGBA', (out_.width + 6, out_.height + 6), (0, 0, 0, 0))
    ext = Image.new('RGBA', out_.size, (40, 4, 2, 255)); ext.putalpha(out_.split()[3])
    for k in range(1, 5): o.alpha_composite(ext, (k, k))
    o.alpha_composite(out_, (0, 0)); o.alpha_composite(g, ((out_.width - g.width) // 2, (out_.height - g.height) // 2))
    return shadow(o.rotate(tilt, resample=Image.BICUBIC, expand=True), 8, (0, 6), 150, 16)

def subtitle(t):
    s = text(t, F_SMILEY, 58, (255, 255, 255), 0, 3, (18, 16, 24))
    return shadow(pad(s, 4), 5, (0, 3), 200, 12)

# ------------------------------------------------------------------ layered backgrounds
_bgc = {}
def bg(kind='navy', backdrop=None, dim=0.2, grid=False, halftone=False, key=None):
    k = key or (kind, None if backdrop is None else id(backdrop), dim, grid, halftone)
    if k in _bgc: return _bgc[k]
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    base = {'navy': (37, 27, 22), 'purple': (44, 18, 30), 'char': (24, 20, 20)}[kind]  # BGR
    glow = {'navy': (90, 60, 40), 'purple': (150, 50, 110), 'char': (60, 50, 50)}[kind]
    img = np.zeros((H, W, 3), np.float32); img[:] = base
    if backdrop is not None:
        b = cv2.cvtColor(cv2.cvtColor(_cover(backdrop, W, H), cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR).astype(np.float32)
        if halftone:
            cell = 7; small = cv2.resize(b[..., 0], (W // cell, H // cell), interpolation=cv2.INTER_AREA) / 255
            dots = np.zeros((H, W), np.float32)
            for (yy, xx), v in np.ndenumerate(small):
                cv2.circle(dots, (xx * cell + cell // 2, yy * cell + cell // 2), int(v * cell * 0.62), 1.0, -1)
            b = b * (0.55 + 0.45 * dots[..., None])
        tint = np.array(glow, np.float32) / 255 * 0.5 + 0.5
        img = img * (1 - dim) + b * tint * dim
    cx, cy = W * 0.5, H * 0.45
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    img += (np.clip(1 - d / (W * 0.6), 0, 1) ** 2 * 0.6)[..., None] * np.array(glow, np.float32)
    rings = (np.abs((d % 150) - 75) > 73.2).astype(np.float32) * np.clip(1 - d / (W * 0.75), 0, 1)
    img += rings[..., None] * 7
    if grid:
        g = ((x.astype(int) % 60 == 0) | (y.astype(int) % 60 == 0)).astype(np.float32)
        img += g[..., None] * 7
    fab = streaks(W, H, 0.12) * 0.5 + streaks(W, H, 0.12, False) * 0.5
    img *= (0.94 + 0.12 * fab)[..., None]
    img += np.random.default_rng(5).normal(0, 2.0, img.shape)
    v = np.sqrt(((x - W / 2) / W) ** 2 + ((y - H / 2) / H) ** 2)
    img *= (1 - np.clip(v - 0.35, 0, 1) * 0.9)[..., None]
    out = np.clip(img, 0, 255).astype(np.uint8); _bgc[k] = out; return out

def _cover(img, w, h):
    ih, iw = img.shape[:2]; s = max(w / iw, h / ih)
    r = cv2.resize(img, (int(np.ceil(iw * s)), int(np.ceil(ih * s))), interpolation=cv2.INTER_CUBIC)
    y0 = (r.shape[0] - h) // 2; x0 = (r.shape[1] - w) // 2
    return r[y0:y0 + h, x0:x0 + w]
