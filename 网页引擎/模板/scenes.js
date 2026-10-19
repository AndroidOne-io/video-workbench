// 每期主要改这里。动画只由 t 决定，不累计上一帧状态。
'use strict';
function titleCard(ctx, title, detail, t, start) {
  const u = easeOut(seg(t, start, start + .5));
  ctx.save(); ctx.globalAlpha = u;
  ctx.translate(0, (1-u)*36);
  ctx.textAlign = 'center'; ctx.fillStyle = '#f1c574';
  ctx.font = 'bold 108px sans-serif'; ctx.fillText(title, W/2, H*.43);
  ctx.fillStyle = '#d1d6e3'; ctx.font = '44px sans-serif';
  ctx.fillText(detail, W/2, H*.56); ctx.restore();
}
VIS[1] = (ctx, t) => titleCard(ctx, '浏览器实时预览', '改画面后刷新即可', t, S[1].start);
VIS[2] = (ctx, t) => {
  titleCard(ctx, '统一时间线', '镜头 字幕 音效共用时间坐标', t, S[2].start);
  E.dot(ctx, lerp(300, 1620, seg(t, S[2].start, S[2].end)), 740, 14, [241,197,116]);
};
// 接真实视频：在 project.json.sources 添加 camera: "media/camera.mp4"，再使用
// VIS[1] = (ctx,t) => full(ctx,'camera',2+(t-S[1].start),{rate:1});
// 使用 rate=r 时，源时间也必须是 sourceIn+(t-shotStart)*r。
