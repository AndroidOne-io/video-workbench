// 公共时间线适配层；所有时间单位为秒，素材路径相对本项目根目录。
'use strict';
const {W, H, clamp, lerp, seg, ease, easeOut} = E;
const PRE = D.PRE, EV = D.EV, VIS = {};
const S = Object.fromEntries(D.shots.map(s => [s.i, s]));
const shotAt = t => D.shots.find(s => s.start <= t && t < s.end);
E.setVideoSources(window.VSRC);
function full(ctx, key, ts, {rate = 1, crop = null} = {}) {
  const v = E.video(key, ts, rate);
  if (!E.ready(v)) return;
  const [w, h] = E.sizeOf(v);
  E.cover(ctx, v, 0, 0, W, H, .5, .5,
    crop ? [crop[0]*w, crop[1]*h, crop[2]*w, crop[3]*h] : null);
}
function frame(ctx, outputTime) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  ctx.shadowColor = 'transparent';
  ctx.fillStyle = '#10131c'; ctx.fillRect(0, 0, W, H);
  const t = outputTime - PRE, shot = shotAt(t);
  if (shot && VIS[shot.i]) VIS[shot.i](ctx, t);
  const sub = D.subs.find(([a, , , b]) => a <= t && t < b);
  if (sub) E.subtitle(ctx, sub[1]);
}
