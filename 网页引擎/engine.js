// 网页播放引擎（通用部分）：纯 JS + Canvas 2D，不依赖 npm。
// 画面函数只依赖时间 t（纯函数），所以可以实时播放、任意拖动，也可以逐帧导出。
// 坐标统一是 1920×1080 的画布像素；颜色 [r,g,b] 0–255。
'use strict';
const E = (() => {
  const W = 1920, H = 1080;

  // ------------------------------------------------------------------ 数学 / 缓动
  const clamp = (x, a, b) => Math.min(Math.max(x, a), b);
  const seg = (t, a, b) => clamp((t - a) / Math.max(b - a, 1e-6), 0, 1);
  const lerp = (a, b, u) => a + (b - a) * u;
  const ease = u => { u = clamp(u, 0, 1); return u * u * (3 - 2 * u); };
  const easeOut = (u, p = 3) => { u = clamp(u, 0, 1); return 1 - Math.pow(1 - u, p); };
  const easeIn = (u, p = 3) => { u = clamp(u, 0, 1); return Math.pow(u, p); };
  const backOut = (u, s = 1.7) => { u = clamp(u, 0, 1) - 1; return u * u * ((s + 1) * u + s) + 1; };
  const rgb = (c, k = 1, a = 1) => `rgba(${Math.round(clamp(c[0] * k, 0, 255))},${Math.round(clamp(c[1] * k, 0, 255))},${Math.round(clamp(c[2] * k, 0, 255))},${a})`;
  function rng(seed) {                       // 确定性随机数（震动、故障用）
    let s = (seed >>> 0) || 1;
    const next = () => { s |= 0; s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
    next.normal = () => { const u = Math.max(next(), 1e-9), v = next(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); };
    return next;
  }

  // ------------------------------------------------------------------ 资源
  const IMG = {};
  function loadImages(list, onProgress) {
    let done = 0;
    return Promise.all(list.map(name => new Promise(res => {
      const im = new Image(); im.decoding = 'async';
      im.onload = im.onerror = () => { done++; onProgress && onProgress(done, list.length); res(); };
      im.src = 'assets/' + name; IMG[name.replace(/\.(png|jpg)$/, '')] = im;
    })));
  }
  const img = name => IMG[name];

  // ------------------------------------------------------------------ 离屏画布
  const _tmp = {};
  function tmp(key, w = W, h = H) {
    let c = _tmp[key];
    if (!c || c.width !== w || c.height !== h) { c = document.createElement('canvas'); c.width = w; c.height = h; _tmp[key] = c; }
    return c;
  }

  // ------------------------------------------------------------------ 视频池：播放时用原生播放 + 漂移校正，拖动/导出时精确跳帧
  const VSRC = {};
  const pool = {};                              // key → [{el, want, rate, used}]
  let MODE = 'seek';                            // 'play' | 'seek'
  let previewRate = 1;                          // 仅预览，素材时间和导出帧不变
  function setVideoSources(map) { Object.assign(VSRC, map); }
  function slotOf(key, slot) {
    pool[key] = pool[key] || [];
    while (pool[key].length <= slot) {
      const el = document.createElement('video');
      el.src = VSRC[key]; el.muted = true; el.playsInline = true; el.preload = 'auto'; el.crossOrigin = 'anonymous';
      pool[key].push({ el, want: 0, rate: 1, used: false });
    }
    return pool[key][slot];
  }
  // 返回可以直接画的画面：视频解好了就先拷一份到缓存画布再返回缓存；正在跳转/还没解出来时返回上一帧的缓存。
  // 这样高倍速快进（每帧都要跳转）或播放中校正跳转时，画面不会一闪一闪（第 43、44 镜就是 20–35 倍速）。
  let FRAME = 0;
  function video(key, ts, rate = 1, slot = 0) {
    const s = slotOf(key, slot), el = s.el, d = el.duration;
    s.want = Math.max(0, isFinite(d) ? Math.min(ts, d - 0.05) : ts); s.rate = rate; s.used = true;
    const ok = el.readyState >= 2 && !el.seeking && el.videoWidth > 0;
    if (ok && s.at !== FRAME) {
      if (!s.cache || s.cache.width !== el.videoWidth || s.cache.height !== el.videoHeight) {
        s.cache = document.createElement('canvas'); s.cache.width = el.videoWidth; s.cache.height = el.videoHeight; s.filled = false;
      }
      s.cache.getContext('2d').drawImage(el, 0, 0); s.filled = true; s.at = FRAME;
    }
    return s.filled ? s.cache : el;
  }
  function syncVideos() {
    FRAME++;
    for (const key in pool) for (const s of pool[key]) {
      const el = s.el;
      if (!s.used) { if (!el.paused) el.pause(); continue; }
      s.used = false;
      const rate = s.rate * previewRate;
      const live = MODE === 'play' && rate >= 0.25 && rate <= 8;
      if (live) {
        if (Math.abs(el.playbackRate - rate) > 1e-3) el.playbackRate = rate;
        if (el.paused) { el.currentTime = s.want; el.play().catch(() => {}); }
        else if (Math.abs(el.currentTime - s.want) > 0.18 + 0.04 * rate && !el.seeking) el.currentTime = s.want;
      } else {
        if (!el.paused) el.pause();
        if (Math.abs(el.currentTime - s.want) > 0.02 && !el.seeking) el.currentTime = s.want;
      }
    }
  }
  async function videosSettled(maxMs = 30000) {  // 导出用：等所有用到的视频跳到位、画面解出来（机器忙时多等，最多 30 秒）
    const t0 = performance.now();
    for (;;) {
      const ps = [];
      for (const key in pool) for (const s of pool[key]) {
        if (s.el.error) continue;                    // 解不了的素材（比如浏览器不支持 H.264）不等
        const el = s.el, d = el.duration, want = isFinite(d) ? Math.max(0, Math.min(s.want, d - 0.05)) : s.want;
        if (Math.abs(el.currentTime - want) > 0.02 && !el.seeking) el.currentTime = want;
        if (el.seeking || el.readyState < 2 || Math.abs(el.currentTime - want) > 0.02) ps.push(new Promise(r => {
          const done = () => { el.removeEventListener('seeked', done); el.removeEventListener('loadeddata', done); r(); };
          el.addEventListener('seeked', done); el.addEventListener('loadeddata', done); setTimeout(done, 1000);
        }));
      }
      if (!ps.length || performance.now() - t0 > maxMs) {     // 跳转完成后，新画面要再等一两帧才真正能被 drawImage 取到
        await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 0)))); return;
      }
      await Promise.all(ps);
    }
  }
  function probeVideos(timeout = 20000) {         // 检查每个视频素材能不能解码：返回解不了的 key 列表
    return Promise.all(Object.keys(VSRC).map(k => new Promise(r => {
      const el = slotOf(k, 0).el; if (el.readyState >= 2) return r(null); if (el.error) return r(k);
      const ok = () => r(null), bad = () => r(k);
      el.addEventListener('loadeddata', ok, { once: true }); el.addEventListener('error', bad, { once: true }); setTimeout(() => r(el.readyState >= 1 ? null : k), timeout);
    }))).then(a => a.filter(Boolean));
  }
  function busy() { for (const k in pool) for (const s of pool[k]) if (s.el.seeking) return true; return false; }
  function allVideos() { const r = []; for (const k in pool) for (const s of pool[k]) r.push(s.el); return r; }
  const ready = el => el && (el.readyState >= 2 || el instanceof HTMLImageElement || el instanceof HTMLCanvasElement);
  const sizeOf = el => el instanceof HTMLVideoElement ? [el.videoWidth || 1920, el.videoHeight || 1080] : [el.width, el.height];

  // ------------------------------------------------------------------ 基本绘制
  function put(ctx, im, cx, cy, a = 1, scale = 1, angle = 0) {   // angle：度，正 = 逆时针（和 Python 一致）
    if (!im || a <= 0.003 || !ready(im)) return;
    const [w, h] = sizeOf(im);
    ctx.save(); ctx.globalAlpha *= clamp(a, 0, 1); ctx.translate(cx, cy);
    if (angle) ctx.rotate(-angle * Math.PI / 180);
    if (scale !== 1) ctx.scale(scale, scale);
    ctx.drawImage(im, -w / 2, -h / 2, w, h); ctx.restore();
  }
  function cover(ctx, src, x, y, w, h, fx = 0.5, fy = 0.5, crop = null) {   // 等比裁切铺满 (x,y,w,h)；crop=[sx,sy,sw,sh] 先裁源
    if (!ready(src)) return;
    const [iw0, ih0] = sizeOf(src); const [sx0, sy0, iw, ih] = crop || [0, 0, iw0, ih0];
    const s = Math.max(w / iw, h / ih); const cw = w / s, ch = h / s;
    ctx.drawImage(src, sx0 + (iw - cw) * fx, sy0 + (ih - ch) * fy, cw, ch, x, y, w, h);
  }
  function fill(ctx, color, a = 1, op = 'source-over') {
    ctx.save(); ctx.globalCompositeOperation = op; ctx.globalAlpha = a; ctx.fillStyle = color; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.fillRect(0, 0, W, H); ctx.restore();
  }
  const flash = (ctx, k) => { if (k > 0.003) fill(ctx, '#fff', Math.min(1, k), 'lighter'); };
  // 调色：去饱和 + 偏暖 + 压暗（对应 Python grade）
  function grade(ctx, x, y, w, h, sat = 0.75, dim = 1, warm = true) {
    ctx.save();
    if (sat < 1) { ctx.globalCompositeOperation = 'saturation'; ctx.globalAlpha = 1 - sat; ctx.fillStyle = '#808080'; ctx.fillRect(x, y, w, h); }
    if (warm) { ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = 1; ctx.fillStyle = 'rgb(255,246,229)'; ctx.fillRect(x, y, w, h); }
    if (dim < 1) { ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1 - dim; ctx.fillStyle = '#000'; ctx.fillRect(x, y, w, h); }
    ctx.restore();
  }
  // 整帧缩放（Python zoom：围绕 (fx,fy) 放大 z 倍）：在画之前 begin，画完 end
  function zoomBegin(ctx, z, fx = 0.5, fy = 0.5) {
    ctx.save(); const w = W / z, h = H / z; const x0 = (W - w) * fx, y0 = (H - h) * fy;
    ctx.transform(z, 0, 0, z, -x0 * z, -y0 * z);
  }
  const zoomEnd = ctx => ctx.restore();

  // ------------------------------------------------------------------ 后期：甩镜 / 震动 / 故障（对当前整帧做）
  function snapshot(ctx) { const c = tmp('snap'); const g = c.getContext('2d'); g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, W, H); g.drawImage(ctx.canvas, 0, 0); return c; }
  function whip(ctx, k, horiz = true) {
    if (k <= 0.01) return; const n = 5 + 120 * k; const c = snapshot(ctx); const m = 9;
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    for (let i = 0; i < m; i++) { const d = (i / (m - 1) - 0.5) * n; ctx.globalAlpha = i === 0 ? 1 : 1 / (i + 1); ctx.drawImage(c, horiz ? d : 0, horiz ? 0 : d); }
    ctx.restore();
  }
  function shake(ctx, k, seed) {
    if (k <= 0.01) return; const r = rng(seed); const dx = r.normal() * 14 * k, dy = r.normal() * 14 * k; const c = snapshot(ctx);
    ctx.save(); ctx.setTransform(1 + 0.02 * k, 0, 0, 1 + 0.02 * k, dx - W * 0.01 * k, dy - H * 0.01 * k); ctx.drawImage(c, 0, 0); ctx.restore();
  }
  function glitch(ctx, amt, seed) {
    if (amt <= 0.01) return; const r = rng(seed); const c = snapshot(ctx);
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    for (let i = 0; i < 6 + 18 * amt; i++) {
      const y = Math.floor(r() * (H - 20)), hh = 4 + Math.floor(r() * 36), dx = r.normal() * 60 * amt;
      ctx.drawImage(c, 0, y, W, hh, dx, y, W, hh);
    }
    const sh = 10 * amt; ctx.globalCompositeOperation = 'screen'; ctx.globalAlpha = 0.35 * amt;
    ctx.drawImage(c, sh, 0); ctx.drawImage(c, -sh, 0); ctx.restore();
  }

  // ------------------------------------------------------------------ 透视卡片（对应 Python persp / dim_except / hl_bar）
  function solveH(src, dst) {                    // 4 点 → 3×3 单应矩阵
    const A = [], b = [];
    for (let i = 0; i < 4; i++) {
      const [x, y] = src[i], [u, v] = dst[i];
      A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.push(u);
      A.push([0, 0, 0, x, y, 1, -v * x, -v * y]); b.push(v);
    }
    for (let c = 0; c < 8; c++) {                // 高斯消元
      let p = c; for (let r = c + 1; r < 8; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
      [A[c], A[p]] = [A[p], A[c]]; [b[c], b[p]] = [b[p], b[c]];
      for (let r = 0; r < 8; r++) if (r !== c) { const f = A[r][c] / A[c][c]; for (let k = c; k < 8; k++) A[r][k] -= f * A[c][k]; b[r] -= f * b[c]; }
    }
    const h = b.map((v, i) => v / A[i][i]); return [h[0], h[1], h[2], h[3], h[4], h[5], h[6], h[7], 1];
  }
  const mapPt = (M, x, y) => { const w = M[6] * x + M[7] * y + M[8]; return [(M[0] * x + M[1] * y + M[2]) / w, (M[3] * x + M[4] * y + M[5]) / w]; };
  function projQuad(w, h, cx, cy, scale = 1, ry = 0, rx = 0, rz = 0, f = 2200) {
    const ay = ry * Math.PI / 180, ax = rx * Math.PI / 180, az = rz * Math.PI / 180;
    const cyA = Math.cos(ay), syA = Math.sin(ay), cxA = Math.cos(ax), sxA = Math.sin(ax), czA = Math.cos(az), szA = Math.sin(az);
    return [[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]].map(([x, y]) => {
      x *= scale; y *= scale; let z = 0;
      // Rx
      let y1 = y * cxA - z * sxA, z1 = y * sxA + z * cxA; y = y1; z = z1;
      // Ry
      let x1 = x * cyA + z * syA; z1 = -x * syA + z * cyA; x = x1; z = z1;
      // Rz
      x1 = x * czA - y * szA; y1 = x * szA + y * czA; x = x1; y = y1;
      const zz = z + f; return [cx + x * f / zz, cy + y * f / zz];
    });
  }
  function roundedOutline(w, h, r, n = 6) {      // 圆角矩形轮廓点（卡片坐标）
    const pts = []; r = Math.min(r, w / 2, h / 2);
    const corners = [[w - r, r, -Math.PI / 2], [w - r, h - r, 0], [r, h - r, Math.PI / 2], [r, r, Math.PI]];
    for (const [cx, cy, a0] of corners) for (let i = 0; i <= n; i++) { const a = a0 + i / n * Math.PI / 2; pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); }
    return pts;
  }
  function pathPoly(ctx, pts) { ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); }
  // src 的 crop=[sx,sy,sw,sh] 映射到 w×h 的卡片，按单应矩阵 M 画到屏幕（三角形细分近似透视）
  function drawWarped(ctx, src, crop, w, h, M, n = 10, radius = 0, alpha = 1) {
    if (!ready(src)) return;
    ctx.save(); ctx.globalAlpha *= alpha;
    if (radius > 0) { pathPoly(ctx, roundedOutline(w, h, radius).map(([x, y]) => mapPt(M, x, y))); ctx.clip(); }
    const P = []; for (let j = 0; j <= n; j++) { P.push([]); for (let i = 0; i <= n; i++) P[j].push(mapPt(M, w * i / n, h * j / n)); }
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
      const x0 = w * i / n, x1 = w * (i + 1) / n, y0 = h * j / n, y1 = h * (j + 1) / n;
      tri(ctx, src, crop, w, h, [x0, y0, x1, y0, x0, y1], [P[j][i], P[j][i + 1], P[j + 1][i]]);
      tri(ctx, src, crop, w, h, [x1, y0, x1, y1, x0, y1], [P[j][i + 1], P[j + 1][i + 1], P[j + 1][i]]);
    }
    ctx.restore();
  }
  function tri(ctx, src, crop, w, h, s, d) {      // 卡片坐标三角形 s → 屏幕三角形 d 的仿射；源 crop 铺满 0..w × 0..h
    const [u0, v0, u1, v1, u2, v2] = s; const [[x0, y0], [x1, y1], [x2, y2]] = d;
    const det = (u1 - u0) * (v2 - v0) - (u2 - u0) * (v1 - v0); if (Math.abs(det) < 1e-9) return;
    const a = ((x1 - x0) * (v2 - v0) - (x2 - x0) * (v1 - v0)) / det, b = ((y1 - y0) * (v2 - v0) - (y2 - y0) * (v1 - v0)) / det;
    const c = ((x2 - x0) * (u1 - u0) - (x1 - x0) * (u2 - u0)) / det, dd = ((y2 - y0) * (u1 - u0) - (y1 - y0) * (u2 - u0)) / det;
    const e = x0 - a * u0 - c * v0, f = y0 - b * u0 - dd * v0;
    const mx = (x0 + x1 + x2) / 3, my = (y0 + y1 + y2) / 3;
    const ex = p => { const dx = p[0] - mx, dy = p[1] - my, L = Math.hypot(dx, dy) || 1; return [p[0] + dx / L * 0.9, p[1] + dy / L * 0.9]; };   // 外扩一点，盖住拼缝
    ctx.save(); pathPoly(ctx, [ex(d[0]), ex(d[1]), ex(d[2])]); ctx.clip();
    ctx.transform(a, b, c, dd, e, f); ctx.drawImage(src, crop[0], crop[1], crop[2], crop[3], 0, 0, w, h);
    ctx.restore();
  }
  // 透视卡片：把 src（可裁切 crop）做成 w×h 的卡片，绕 Y/X/Z 转后透视贴到 (cx,cy)；返回卡片坐标 → 屏幕的单应矩阵
  function persp(ctx, src, w, h, cx, cy, o = {}) {
    const { scale = 1, ry = 0, rx = 0, rz = 0, a = 1, shadowK = 0.6, f = 2200, crop = null, radius = 22, border = 0, borderCol = '#e1e4ec', n = 10 } = o;
    const q = projQuad(w, h, cx, cy, scale, ry, rx, rz, f);
    const M = solveH([[0, 0], [w, 0], [w, h], [0, h]], q);
    if (!ready(src)) return M;
    const [iw, ih] = sizeOf(src); const cr = crop || [0, 0, iw, ih];
    const outline = roundedOutline(w, h, radius).map(([x, y]) => mapPt(M, x, y));
    if (shadowK > 0) {
      ctx.save(); ctx.globalAlpha *= a; ctx.shadowColor = `rgba(0,0,0,${0.85 * shadowK})`; ctx.shadowBlur = 56; ctx.shadowOffsetY = 26;
      pathPoly(ctx, outline); ctx.fillStyle = '#000'; ctx.fill(); ctx.restore();
    }
    drawWarped(ctx, src, cr, w, h, M, n, radius, a);
    if (border > 0) { ctx.save(); ctx.globalAlpha *= a; pathPoly(ctx, outline); ctx.lineWidth = border * 2; ctx.strokeStyle = borderCol; ctx.stroke(); ctx.restore(); }
    return M;
  }
  // 透视卡片上，除了 box（卡片坐标）以外压暗
  function dimExcept(ctx, M, w, h, box, k = 0.55, radius = 22) {
    const outer = roundedOutline(w, h, radius).map(([x, y]) => mapPt(M, x, y));
    const [x0, y0, x1, y1] = box; const inner = [[x0, y0], [x0, y1], [x1, y1], [x1, y0]].map(([x, y]) => mapPt(M, x, y));
    ctx.save(); ctx.beginPath();
    outer.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath();
    inner.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath();
    ctx.fillStyle = `rgba(0,0,0,${k})`; ctx.fill('evenodd'); ctx.restore();
  }
  function quadOf(M, box) { const [x0, y0, x1, y1] = box; return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]].map(([x, y]) => mapPt(M, x, y)); }
  function bboxOf(pts) { const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]); return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)]; }
  function hlBar(ctx, x0, y0, x1, y1, u, col, a = 0.42) {   // 高亮条从左往右扫
    const xe = lerp(x0, x1, easeOut(u)); if (xe <= x0) return;
    ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = rgb(col, 1, Math.min(1, a * 1.6)); ctx.fillRect(x0, y0, xe - x0, y1 - y0);
    ctx.globalCompositeOperation = 'source-over'; ctx.fillStyle = rgb(col, 1, a * 0.35); ctx.fillRect(x0, y0, xe - x0, y1 - y0); ctx.restore();
  }

  // ------------------------------------------------------------------ 字：字幕 / 数字 / 金属字扫光
  function subtitle(ctx, txt, y = H - 92) {
    if (!txt) return;
    ctx.save(); ctx.font = '64px Sub'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    try { ctx.letterSpacing = '1.3px'; } catch (e) {}
    ctx.lineJoin = 'round'; ctx.lineWidth = 8; ctx.strokeStyle = 'rgb(8,10,16)';
    ctx.shadowColor = 'rgba(0,0,0,0.63)'; ctx.shadowBlur = 6; ctx.shadowOffsetY = 3;
    ctx.strokeText(txt, W / 2, y); ctx.shadowColor = 'transparent'; ctx.fillStyle = 'rgb(242,245,250)'; ctx.fillText(txt, W / 2, y); ctx.restore();
  }
  function number(ctx, str, cx, cy, size, col, a = 1, scale = 1) {   // Bebas 数字 + 同色辉光 + 投影
    if (a <= 0.003) return;
    ctx.save(); ctx.globalAlpha *= a; ctx.translate(cx, cy); ctx.scale(scale, scale);
    ctx.font = `${size}px Num`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillStyle = rgb(col);
    ctx.shadowColor = 'rgba(0,0,0,0.75)'; ctx.shadowBlur = 16; ctx.shadowOffsetY = 10; ctx.fillText(str, 0, 0);
    ctx.shadowColor = rgb(col, 1, 0.6); ctx.shadowBlur = 26; ctx.shadowOffsetY = 0; ctx.fillText(str, 0, 0);
    ctx.restore();
  }
  function sweep(im, u, width = 0.14, k = 1, key = 'sweep') {      // 金属字扫光：返回一张带亮带的画布
    if (!ready(im)) return im;
    const [w, h] = sizeOf(im); const c = tmp(key, w, h), g = c.getContext('2d');
    g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; g.clearRect(0, 0, w, h); g.drawImage(im, 0, 0);
    if (u <= 0 || u >= 1) return c;
    const L = w + h * 0.35, cc = lerp(-0.2, 1.3, u) * L, sg = width * w, nn = 1 + 0.35 * 0.35;
    const P = s => [s / nn, 0.35 * s / nn];
    const [ax, ay] = P(cc - 3 * sg), [bx, by] = P(cc + 3 * sg);
    const gr = g.createLinearGradient(ax, ay, bx, by);
    [[0, 0.011], [1 / 6, 0.135], [1 / 3, 0.61], [0.5, 1], [2 / 3, 0.61], [5 / 6, 0.135], [1, 0.011]].forEach(([p, v]) => gr.addColorStop(p, `rgba(255,255,255,${v * k})`));
    g.globalCompositeOperation = 'source-atop'; g.fillStyle = gr; g.fillRect(0, 0, w, h); g.globalCompositeOperation = 'source-over';
    return c;
  }
  // 发光线条/点：在 lighter 模式下画，带同色辉光
  function glowBegin(ctx, col, blur = 14, k = 1) { ctx.save(); ctx.globalCompositeOperation = 'lighter'; ctx.shadowColor = rgb(col, 1, Math.min(1, 0.9 * k)); ctx.shadowBlur = blur; }
  const glowEnd = ctx => ctx.restore();
  function dot(ctx, x, y, r, col, k = 1) { ctx.fillStyle = rgb(col, k); ctx.beginPath(); ctx.arc(x, y, Math.max(0.5, r), 0, Math.PI * 2); ctx.fill(); }
  function ring(ctx, x, y, r, col, k = 1, lw = 3) { ctx.strokeStyle = rgb(col, k); ctx.lineWidth = lw; ctx.beginPath(); ctx.arc(x, y, Math.max(0.5, r), 0, Math.PI * 2); ctx.stroke(); }
  function line(ctx, pts, col, k = 1, lw = 3) { ctx.strokeStyle = rgb(col, k); ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); }

  // ------------------------------------------------------------------ 图层 + 快速模糊（缩小再放大，所有浏览器都支持）
  function layer(key = 'L') { const c = tmp('layer_' + key); const g = c.getContext('2d'); g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.shadowColor = 'transparent'; g.clearRect(0, 0, W, H); return g; }
  function blurred(src, r, key = 'b') {           // 返回 src 模糊后的小画布（画回去时放大即可）
    const [w, h] = sizeOf(src); const s = Math.max(1, r * 0.85); let cur = src, cw = w, ch = h, i = 0;
    while (cw / 2 >= w / s && cw > 8) {            // 每次缩一半，保证平滑
      const nw = Math.max(2, Math.round(cw / 2)), nh = Math.max(2, Math.round(ch / 2)); const c = tmp(`${key}_${i++}`, nw, nh); const g = c.getContext('2d');
      g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'copy'; g.imageSmoothingQuality = 'high'; g.drawImage(cur, 0, 0, nw, nh); g.globalCompositeOperation = 'source-over';
      cur = c; cw = nw; ch = nh;
    }
    return cur;
  }
  // 把图层叠加到画面（lighter），glows=[[半径, 强度], ...] 对应 Python 的 f += lay + blur(lay, r)*k
  function addLayer(ctx, g, k = 1, glows = [], op = 'lighter') {
    const c = g.canvas || g; ctx.save(); ctx.globalCompositeOperation = op;   // 跟随当前变换（zoomBegin 里也一起放大）
    if (k > 0) { ctx.globalAlpha = Math.min(1, k); ctx.drawImage(c, 0, 0); }
    for (const [r, kk] of glows) { const b = blurred(c, r, 'gl' + r); ctx.globalAlpha = Math.min(1, kk); ctx.drawImage(b, 0, 0, W, H); if (kk > 1) { ctx.globalAlpha = Math.min(1, kk - 1); ctx.drawImage(b, 0, 0, W, H); } }
    ctx.restore();
  }
  function blurDraw(ctx, src, r, x = 0, y = 0, w = W, h = H, a = 1, op = 'source-over') { const b = blurred(src, r, 'bd'); ctx.save(); ctx.globalAlpha *= a; ctx.globalCompositeOperation = op; ctx.drawImage(b, x, y, w, h); ctx.restore(); }

  return { W, H, clamp, seg, lerp, ease, easeOut, easeIn, backOut, rgb, rng, IMG, img, loadImages, tmp, setVideoSources, video, syncVideos, videosSettled, allVideos, probeVideos, busy,
    ready, sizeOf, put, cover, fill, flash, grade, zoomBegin, zoomEnd, whip, shake, glitch, solveH, mapPt, projQuad, roundedOutline, pathPoly, drawWarped,
    persp, dimExcept, quadOf, bboxOf, hlBar, subtitle, number, sweep, glowBegin, glowEnd, dot, ring, line, layer, blurred, addLayer, blurDraw,
    setMode: m => { MODE = m; }, getMode: () => MODE,
    setPreviewRate: rate => { previewRate = rate; }, _pool: pool };
})();
