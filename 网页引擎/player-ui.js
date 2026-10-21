// Shared player shell. Project text is assigned with textContent, never HTML.
'use strict';
(() => {
 const p=window.VIDEO_PROJECT;
 if(!p || typeof p.draw!=='function' || !Number.isFinite(p.duration) || p.duration<=0 || !Number.isFinite(p.fps) || p.fps<=0 || !p.id || !p.audio) throw new Error('Invalid VIDEO_PROJECT contract');
 document.body.insertAdjacentHTML('afterbegin',`
<header><div class="brand"><span class="mark" id="projectMark"></span><div><h1><span id="projectTitle"></span> <span>网页工程</span></h1><p id="projectSubtitle"></p></div></div><div class="header-tools"><span class="spec" id="projectSpec"></span><button id="transcriptToggle" aria-expanded="true" aria-controls="transcript">收起逐字稿</button></div></header>
<main>
 <section id="viewer" aria-label="视频预览">
  <div id="stage"><canvas id="c" width="1920" height="1080" aria-label="实时画面"></canvas><div id="load" role="status">正在准备工程…</div><button id="centerPlay" aria-label="播放视频">▶</button></div>
  <div class="shot-info"><span id="shotIndex">01</span><span id="shotName">正在载入</span><span id="fps">实时预览</span></div>
  <div id="bar">
   <div id="track" role="slider" tabindex="0" aria-label="视频进度" aria-valuemin="0" aria-valuemax="0" aria-valuenow="0"><div class="track-bg"></div><div id="fill"></div><div id="ticks"></div><div id="head"></div><span id="hoverTime"></span></div>
   <div class="controls"><div class="transport"><button id="play" class="primary" aria-label="播放">▶ 播放</button><button id="prev" title="上一帧（,）" aria-label="上一帧">Ⅰ‹</button><button id="next" title="下一帧（.）" aria-label="下一帧">›Ⅰ</button><span id="time">00:00.00 / 00:00.00</span></div><div class="settings"><label class="speed"><input id="speed" type="number" value="1.00" min="0.25" max="4" step="0.01" aria-label="播放倍速">×</label><select id="speedPreset" aria-label="常用倍速"><option value="" disabled>自定义</option><option value="0.5">0.5×</option><option value="0.75">0.75×</option><option value="1" selected>1× 正常</option><option value="1.25">1.25×</option><option value="1.5">1.5×</option><option value="2">2×</option></select><button id="subtitles" aria-pressed="true">字幕 开</button><button id="mute" aria-pressed="false">声音 开</button><button id="full">全屏</button></div></div>
   <div class="foot"><select id="jump" aria-label="跳到镜头"><option value="">跳到镜头…</option></select><span>空格 播放 / 暂停 <b>·</b> ← → 1 秒 <b>·</b> , . 逐帧</span><span id="status" role="status">正在载入</span></div>
  </div>
 </section>
 <aside id="transcript"><div class="aside-title"><h2>逐字稿</h2><span id="captionCount"></span></div><label class="search"><span>⌕</span><input id="search" type="search" placeholder="搜索台词，点击定位" aria-label="搜索逐字稿"></label><div id="captionList" aria-label="字幕时间列表"></div><div class="aside-foot" id="projectNote"></div></aside>
</main>
<div id="warn" role="alert" hidden></div>
<audio id="mix" preload="auto"></audio>
`);
 const $=id=>document.getElementById(id);
 document.title=(p.title||'视频')+' · 网页预览';
 $('projectTitle').textContent=p.title||'视频';
 $('projectMark').textContent=p.mark||'▶';
 $('projectSubtitle').textContent=p.subtitle||'';
 $('projectNote').textContent=p.note||'';
 $('projectSpec').textContent=`1920 × 1080 · ${p.fps} FPS`;
 $('track').setAttribute('aria-valuemax',String(p.duration));
 $('mix').src=p.audio;
})();
