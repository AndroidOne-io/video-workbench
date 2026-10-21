// Shared player. Only E and VIDEO_PROJECT are required; no project-specific globals.
'use strict';
(() => {
 const project=window.VIDEO_PROJECT,clamp=E.clamp;
 const $=id=>document.getElementById(id),cv=$('c'),ctx=cv.getContext('2d'),au=$('mix');
 let current=0,playing=false,ready=false,showSubs=true,rendering=false,seekVersion=0,activeCaption=-1,lastScroll=0;
 const captions=[...(project.captions||[])].sort((a,b)=>a[0]-b[0]);
 const shots=project.shots||[],artwork=project.images||[];
 const storageKey='video-workbench-speed:'+project.id;
 const lastFrame=(Math.ceil(project.duration*project.fps)-1)/project.fps;
 const fmt=t=>`${String(Math.floor(Math.max(0,t)/60)).padStart(2,'0')}:${(Math.max(0,t)%60).toFixed(2).padStart(5,'0')}`;
 const warn=message=>{$('warn').textContent=message;$('warn').hidden=false;};
 const playButton=$('play'),center=$('centerPlay');playButton.disabled=true;center.disabled=true;
 function ui(){
  $('time').textContent=`${fmt(current)} / ${fmt(project.duration)}`;
  const pc=current/project.duration*100;$('fill').style.width=pc+'%';$('head').style.left=pc+'%';$('track').setAttribute('aria-valuenow',current.toFixed(3));$('track').setAttribute('aria-valuetext',fmt(current));
  const i=shots.findIndex(s=>s.start<=current&&current<s.end);$('shotIndex').textContent=String(i+1).padStart(2,'0');$('shotName').textContent=i>=0?shots[i].name:'口播';
  playButton.textContent=playing?'❚❚ 暂停':'▶ 播放';playButton.setAttribute('aria-label',playing?'暂停':'播放');center.hidden=playing;
  const j=captions.findIndex(s=>s[0]<=current&&current<s[1]);
  if(j!==activeCaption){if(activeCaption>=0)captionButtons[activeCaption].classList.remove('active');activeCaption=j;if(j>=0){const item=captionButtons[j];item.classList.add('active');if(playing&&!$('search').value&&performance.now()-lastScroll>3500){const list=$('captionList');list.scrollTo({top:item.offsetTop-list.offsetTop-list.clientHeight/2,behavior:'smooth'});}}}
 }
 function draw(){project.draw(ctx,current,showSubs);E.syncVideos();}
 function pause(){playing=false;au.pause();E.setMode('seek');current=clamp(au.currentTime,0,lastFrame);ui();}
 async function seek(time,strict=false){
  if(!Number.isFinite(time))throw new Error('Invalid seek time');
  const version=++seekVersion;playing=false;au.pause();current=clamp(time,0,lastFrame);au.currentTime=current;E.setMode('seek');rendering=true;$('status').textContent='正在定位…';ui();
  try{draw();await E.videosSettled(15000);if(version!==seekVersion)return;draw();$('status').textContent='已就绪';}
  catch(e){warn('画面定位失败：'+e.message);if(strict)throw e;}
  finally{if(version===seekVersion)rendering=false;}
 }
 async function play(){
  if(!ready)return;if(current>=lastFrame-.01)await seek(0);
  ++seekVersion;rendering=false;au.currentTime=current;
  try{await au.play();playing=true;E.setMode('play');$('status').textContent='播放中';ui();}
  catch(e){playing=false;warn('声音暂时无法播放，请再次点击播放。'+e.message);ui();}
 }
 const toggle=()=>playing?(pause(),draw(),$('status').textContent='已暂停'):play();
 playButton.onclick=center.onclick=toggle;cv.onclick=toggle;
 $('prev').onclick=()=>seek(current-1/project.fps);$('next').onclick=()=>seek(current+1/project.fps);
 let rate=1;
 function setSpeed(value){if(!Number.isFinite(value)||value<.25||value>4)return false;rate=Math.round(value*100)/100;au.preservesPitch=true;au.playbackRate=rate;E.setPreviewRate(rate);$('speed').value=rate.toFixed(2);$('speedPreset').value=[.5,.75,1,1.25,1.5,2].includes(rate)?String(rate):'';try{localStorage.setItem(storageKey,String(rate));}catch(_){}return true;}
 $('speed').onchange=()=>{if(!setSpeed(Number($('speed').value)))$('speed').value=rate.toFixed(2);};
 $('speed').onkeydown=e=>{if(e.key==='Enter'){$('speed').onchange();$('speed').blur();}};
 $('speedPreset').onchange=()=>setSpeed(Number($('speedPreset').value));
 try{if(!setSpeed(Number(localStorage.getItem(storageKey))))setSpeed(1);}catch(_){setSpeed(1);}
 $('subtitles').onclick=()=>{showSubs=!showSubs;$('subtitles').setAttribute('aria-pressed',String(showSubs));$('subtitles').textContent='字幕 '+(showSubs?'开':'关');draw();};
 $('mute').onclick=()=>{au.muted=!au.muted;$('mute').setAttribute('aria-pressed',String(au.muted));$('mute').textContent='声音 '+(au.muted?'关':'开');};
 $('full').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await $('stage').requestFullscreen();}catch(_){warn('当前浏览器无法进入全屏，请使用 Chrome 打开。');}};
 $('transcriptToggle').onclick=()=>{const hidden=!$('transcript').hidden;$('transcript').hidden=hidden;$('transcriptToggle').textContent=hidden?'展开逐字稿':'收起逐字稿';$('transcriptToggle').setAttribute('aria-expanded',String(!hidden));};
 if(matchMedia('(max-width:760px)').matches)$('transcriptToggle').click();
 const captionButtons=captions.map(([start,end,txt])=>{const b=document.createElement('button');b.className='caption';b.dataset.start=start;const time=document.createElement('time');time.textContent=fmt(start).slice(0,5);const text=document.createElement('span');text.textContent=txt;b.append(time,text);b.onclick=()=>seek(start);$('captionList').append(b);return b;});
 $('captionCount').textContent=captions.length+' 句';
 $('captionList').addEventListener('wheel',()=>lastScroll=performance.now(),{passive:true});$('captionList').addEventListener('touchstart',()=>lastScroll=performance.now(),{passive:true});
 $('search').oninput=()=>{const term=$('search').value.trim().toLowerCase();let count=0;captionButtons.forEach((b,i)=>{b.hidden=!captions[i][2].toLowerCase().includes(term);if(!b.hidden)count++;});$('captionCount').textContent=count+' 句';};
 shots.forEach((s,i)=>{let tick=document.createElement('span');tick.className='tick';tick.style.left=s.start/project.duration*100+'%';$('ticks').append(tick);let option=document.createElement('option');option.value=s.start;option.textContent=`${String(i+1).padStart(2,'0')} · ${fmt(s.start).slice(0,5)} ${s.name}`;$('jump').append(option);});
 $('jump').onchange=()=>{if($('jump').value!=='')seek(Number($('jump').value));$('jump').value='';};
 const track=$('track');let dragging=false;
 const position=e=>{const r=track.getBoundingClientRect();return clamp((e.clientX-r.left)/r.width,0,1)*project.duration;};
 track.onpointerdown=e=>{if(!ready)return;dragging=true;track.setPointerCapture(e.pointerId);seek(position(e));};
 track.onpointermove=e=>{let t=position(e);$('hoverTime').textContent=fmt(t);$('hoverTime').style.left=clamp(t/project.duration*100,3,97)+'%';if(dragging)seek(t);};
 track.onpointerup=track.onpointercancel=()=>dragging=false;
 document.addEventListener('keydown',e=>{if(!ready||['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName)||e.target.isContentEditable)return;if(['Space','ArrowLeft','ArrowRight','Home','End'].includes(e.code))e.preventDefault();if(e.code==='Space')toggle();else if(e.code==='ArrowLeft')seek(current-1);else if(e.code==='ArrowRight')seek(current+1);else if(e.key===',')seek(current-1/project.fps);else if(e.key==='.')seek(current+1/project.fps);else if(e.code==='Home')seek(0);else if(e.code==='End')seek(lastFrame);});
 au.addEventListener('error',()=>{pause();warn('配乐音轨无法读取，请检查项目音轨是否完整。');});
 au.addEventListener('ended',()=>{playing=false;current=lastFrame;E.setMode('seek');draw();ui();$('status').textContent='播放结束';});
 au.addEventListener('waiting',()=>{$('status').textContent='音轨缓冲中…';E.setMode('seek');});
 au.addEventListener('playing',()=>{if(playing){E.setMode('play');$('status').textContent='播放中';}});
 let lastTick=performance.now(),frames=0;
 function loop(){
  if(ready&&!rendering){if(playing){current=clamp(au.currentTime,0,lastFrame);draw();ui();}else if(E.busy())draw();}
  frames++;let now=performance.now();if(now-lastTick>=1000){$('fps').textContent=playing?`${Math.round(frames*1000/(now-lastTick))} fps · ${rate.toFixed(2)}×`:'实时预览';frames=0;lastTick=now;}
  requestAnimationFrame(loop);
 }
 window.player={seek,play,pause,setSpeed,get t(){return current;},get playing(){return playing;}};
 window.renderAt=async t=>{if(!ready)throw new Error('Player is not ready');await seek(t,true);return true;};
 window.previewDiagnostics=()=>({ready,current,playing,rate,sceneCount:shots.length,artwork:artwork.length,videoErrors:E.allVideos().filter(v=>v.error).map(v=>({src:v.src,error:v.error.message}))});
 Promise.all([...(project.fonts||[]).map(font=>document.fonts.load(font)),E.loadImages(artwork,(a,b)=>{$('load').textContent=`正在加载素材 ${a} / ${b}`;})]).then(async()=>{
  // Preload original sources once so cuts can start immediately; no proxies.
  const failures=await E.probeVideos(20000);window.VIDEO_BAD=failures;if(failures.length)warn('以下素材未能加载：'+failures.join('、')+'。请检查素材文件，并使用 Chrome。');
  await seek(0,true);ready=true;window.READY=true;playButton.disabled=center.disabled=false;$('load').hidden=true;requestAnimationFrame(loop);
 }).catch(e=>{warn('工程加载失败：'+e.message);$('load').textContent='素材未能完整加载，请检查文件后刷新';});
})();
