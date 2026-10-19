// 播放器：音轨做主时钟；暂停/拖动时精确跳帧；window.renderAt(t) 给导出脚本用
'use strict';
(() => {
  const cv = document.getElementById('c'), ctx = cv.getContext('2d');
  const au = document.getElementById('mix');
  au.src = D.audio || 'mix.m4a';
  if (/[?&]proxy/.test(location.search)) au.src = '_proxy/mix.ogg';   // 自测用（测试浏览器不支持 AAC）；正常打开用 mix.m4a
  const DUR = D.DUR; const FPS = D.FPS;
  let tCur = 0, playing = false, exporting = false;

  // 资源清单（assets 里的所有图片）
  const ASSETS = window.ASSETS || [];
  const fmt = t => { t = Math.max(0, t); const m = Math.floor(t / 60); return `${m}:${(t - m * 60).toFixed(1).padStart(4, '0')}`; };

  // 进度条 + 镜头刻度 + 跳转菜单
  const track = document.getElementById('track'), fillEl = document.getElementById('fill'), head = document.getElementById('head');
  const jump = document.getElementById('jump'), nameEl = document.getElementById('shotName'), timeEl = document.getElementById('time');
  const speed = document.getElementById('speed'), speedPreset = document.getElementById('speedPreset');
  function setSpeed(rate) {
    if (!Number.isFinite(rate) || rate < 0.25 || rate > 4) return false;
    rate = Math.round(rate * 100) / 100;
    au.preservesPitch = true;
    au.playbackRate = rate;
    E.setPreviewRate(rate);
    speed.value = rate.toFixed(2);
    speedPreset.value = [0.5, 0.75, 1, 1.25, 1.5, 2].includes(rate) ? String(rate) : '';
    try { localStorage.setItem('video-workbench-speed:' + location.pathname, String(rate)); } catch (_) {}
    return true;
  }
  speed.onchange = () => { if (!setSpeed(Number(speed.value))) speed.value = au.playbackRate.toFixed(2); };
  speed.oninput = () => { const typed = speed.value; if (setSpeed(Number(typed))) speed.value = typed; };
  speed.onblur = speed.onchange;
  speed.onkeydown = e => { if (e.key === 'Enter') { speed.onchange(); speed.blur(); } };
  speedPreset.onchange = () => setSpeed(Number(speedPreset.value));
  try { if (!setSpeed(Number(localStorage.getItem('video-workbench-speed:' + location.pathname)))) setSpeed(1); } catch (_) { setSpeed(1); }
  jump.replaceChildren(new Option('跳到镜头…', ''));
  D.shots.forEach(s => jump.add(new Option(`${s.i} · ${s.text.slice(0, 16)}`, String(s.i))));
  D.shots.forEach(s => { const d = document.createElement('div'); d.className = 'tick'; d.style.left = ((s.start + D.PRE) / DUR * 100) + '%'; track.appendChild(d); });
  function ui() {
    const p = tCur / DUR * 100; fillEl.style.width = p + '%'; head.style.left = p + '%';
    timeEl.textContent = `${fmt(tCur)} / ${fmt(DUR)}`;
    const s = D.shots.find(x => x.start <= tCur - D.PRE && tCur - D.PRE < x.end); nameEl.textContent = s ? `第 ${s.i} 镜：${s.text}` : '冷开';
    document.getElementById('play').textContent = playing ? '❚❚ 暂停' : '▶ 播放';
  }
  function draw(t) { frame(ctx, t); E.syncVideos(); }
  function seek(t) { tCur = E.clamp(t, 0, DUR - 1 / FPS); au.currentTime = tCur; if (!playing) { E.setMode('seek'); draw(tCur); setTimeout(() => !playing && draw(tCur), 120); setTimeout(() => !playing && draw(tCur), 400); } ui(); }
  function play() { if (tCur >= DUR - 0.05) tCur = 0; au.currentTime = tCur; playing = true; E.setMode('play'); au.play().catch(() => {}); ui(); }
  function pause() { playing = false; au.pause(); E.setMode('seek'); tCur = au.currentTime; draw(tCur); ui(); }
  function loop() {
    if (playing) { tCur = au.currentTime; if (au.ended || tCur >= DUR) { pause(); } draw(tCur); ui(); }
    else if (!exporting && E.busy()) draw(tCur);                // 暂停/拖动时视频还在跳转：跳好之前一直重画，跳到位就自动更新
    requestAnimationFrame(loop);
  }
  let drag = false;
  const posT = e => { const r = track.getBoundingClientRect(); return E.clamp((e.clientX - r.left) / r.width, 0, 1) * DUR; };
  track.addEventListener('pointerdown', e => { drag = true; track.setPointerCapture(e.pointerId); if (playing) pause(); seek(posT(e)); });
  track.addEventListener('pointermove', e => { if (drag) seek(posT(e)); });
  track.addEventListener('pointerup', () => { drag = false; });
  document.getElementById('play').onclick = () => playing ? pause() : play();
  document.getElementById('full').onclick = () => (cv.requestFullscreen || cv.webkitRequestFullscreen).call(cv);
  jump.onchange = () => { const i = +jump.value; if (i) { if (playing) pause(); seek(S[i].start + D.PRE); } jump.value = ''; };
  document.addEventListener('keydown', e => {
    if (['SELECT', 'INPUT', 'TEXTAREA'].includes(e.target.tagName) || e.target.isContentEditable) return;
    if (e.code === 'Space') { e.preventDefault(); playing ? pause() : play(); }
    else if (e.key === 'ArrowLeft') seek(tCur - 1); else if (e.key === 'ArrowRight') seek(tCur + 1);
    else if (e.key === ',') { if (playing) pause(); seek(tCur - 1 / FPS); } else if (e.key === '.') { if (playing) pause(); seek(tCur + 1 / FPS); }
  });

  // 导出 / 截图：精确到帧（等视频跳到位再画）
  window.renderAt = async t => {
    exporting = true; tCur = t; E.setMode('seek'); playing = false; au.pause();   // 导出期间暂停播放器自己的重画，否则会把视频跳回旧时刻
    frame(ctx, t); E.syncVideos(); await E.videosSettled(); frame(ctx, t); exporting = false;   // 第一遍只为登记要用哪些视频的哪一刻；等全部跳到位后画最终一遍
    tCur = t; ui(); return true;
  };
  window.player = { seek, play, pause, get t() { return tCur; } };

  const load = document.getElementById('load');
  Promise.all([
    document.fonts.load('64px Sub'), document.fonts.load('64px Num'), document.fonts.load('64px Title'), document.fonts.load('64px Sharp'), document.fonts.load('64px Hand'),
    E.loadImages(ASSETS, (a, b) => { load.textContent = `正在加载素材… ${a} / ${b}`; }),
  ]).then(() => { load.style.display = 'none'; window.READY = true; seek(0); requestAnimationFrame(loop);
    E.probeVideos().then(bad => {                // 视频素材读不了时给出提示（多半是没用 serve.py 打开，或浏览器不支持 H.264）
      window.VIDEO_BAD = bad; if (!bad.length) return;
      const w = document.getElementById('warn'); w.style.display = 'block';
      w.textContent = `有 ${bad.length} 个视频素材读不出来（${bad.join('、')}）：请用 Chrome，并用 serve.py / 预览.command 打开，不要直接双击 html。`;
    });
  });
  // 实时帧率（播放时显示在右下角，方便判断电脑是否跟得上）
  let fc = 0, ft = performance.now(); const fpsEl = document.getElementById('fps');
  (function tick() { fc++; const n = performance.now(); if (n - ft > 1000) { fpsEl.textContent = playing ? `画面 ${Math.round(fc * 1000 / (n - ft))} fps` : ''; fc = 0; ft = n; } requestAnimationFrame(tick); })();
})();
