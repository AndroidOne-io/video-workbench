const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..');
class Element{
 constructor(tag='DIV'){this.tagName=tag;this.children=[];this.dataset={};this.style={};this.hidden=false;this.value='';this.attrs={};this.listeners={};this.currentTime=0;this.paused=true;this.playbackRate=1;this.clientHeight=500;this.offsetTop=0;this.classList={add(){},remove(){}};}
 append(...els){this.children.push(...els)}setAttribute(k,v){this.attrs[k]=v}addEventListener(k,fn){this.listeners[k]=fn}getContext(){return {}}pause(){this.paused=true}async play(){this.paused=false}scrollTo(){}blur(){}click(){this.onclick?.()}getBoundingClientRect(){return {left:0,width:1000}}setPointerCapture(){}async requestFullscreen(){}
}
const els=Object.fromEntries([...fs.readFileSync(path.join(root,'player-ui.js'),'utf8').matchAll(/id="([^"]+)"/g)].map(m=>[m[1],new Element()]));
els.search.value='';const saved={},handlers={};const sandbox={console,performance,setTimeout,location:{protocol:'file:'},matchMedia:()=>({matches:false}),localStorage:{getItem:k=>saved[k],setItem:(k,v)=>saved[k]=v},document:{getElementById:id=>{assert(els[id],id);return els[id]},createElement:tag=>new Element(tag.toUpperCase()),fonts:{load:async()=>[]},addEventListener:(k,f)=>handlers[k]=f},requestAnimationFrame:()=>{}};
sandbox.window=sandbox;vm.createContext(sandbox);
vm.runInContext(`const D={DUR:6,FPS:30,artwork:[],subtitles:[[0,2,'第一句'],[2,4,'搜索目标'],[4,6,'最后一句']]};`,sandbox);
vm.runInContext(`const E={clamp:(v,a,b)=>Math.max(a,Math.min(v,b)),setVideoSources(){},setPreviewRate(){},setMode(){},syncVideos(){},videosSettled:async()=>{},allVideos:()=>[],probeVideos:async()=>[],busy:()=>false,loadImages:async()=>{}};const clamp=E.clamp;const SC=[{start:0,end:D.DUR,name:'全片'}];function frame(){}`,sandbox);
vm.runInContext(`window.VIDEO_PROJECT={id:'fixture',duration:D.DUR,fps:D.FPS,shots:SC,captions:D.subtitles,images:[],draw:frame};`,sandbox);
vm.runInContext(fs.readFileSync(path.join(root,'player.js'),'utf8'),sandbox);
(async()=>{
 await new Promise(r=>setTimeout(r,20));assert(sandbox.READY);assert(els.load.hidden);assert.equal(els.captionList.children.length,3);
 await sandbox.player.seek(2.03);assert.equal(sandbox.player.t,2.03);assert.equal(els.mix.currentTime,2.03);
 assert(sandbox.player.setSpeed(1.37));assert.equal(els.mix.playbackRate,1.37);assert.equal(saved['video-workbench-speed:fixture'],'1.37');assert(!sandbox.player.setSpeed(5));
 await sandbox.player.play();assert(sandbox.player.playing);assert(!els.mix.paused);sandbox.player.pause();assert(!sandbox.player.playing);assert(els.mix.paused);
 els.search.value='搜索';els.search.oninput();assert(els.captionList.children.filter(b=>!b.hidden).length===1);assert(els.captionList.children.some(b=>b.hidden));
 await sandbox.player.seek(999);assert(sandbox.player.t<6);await sandbox.player.seek(-2);assert.equal(sandbox.player.t,0);
 els.jump.value='0';els.jump.onchange();await new Promise(r=>setTimeout(r,10));assert.equal(sandbox.player.t,0);
 els.subtitles.onclick();assert.equal(els.subtitles.attrs['aria-pressed'],'false');els.mute.onclick();assert.equal(els.mix.muted,true);
 els.transcriptToggle.click();assert(els.transcript.hidden);els.transcriptToggle.click();assert(!els.transcript.hidden);
 handlers.keydown({target:{tagName:'DIV'},code:'ArrowRight',preventDefault(){}});await new Promise(r=>setTimeout(r,10));assert.equal(sandbox.player.t,1);
 sandbox.Etest=true;
 await assert.rejects(()=>sandbox.player.seek(NaN));
 vm.runInContext("E.videosSettled=async()=>{throw new Error('decode failure')}",sandbox);
 await assert.rejects(()=>sandbox.renderAt(2),/decode failure/);
 console.log('Player interactions passed: initialization, audio clock seeks, play/pause, custom speed persistence, search, bounds, first-shot jump, subtitles, mute, transcript, keyboard. Browser rendering/audio decoding are not covered.');
})().catch(e=>{console.error(e);process.exitCode=1});
