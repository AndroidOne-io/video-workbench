// Project-owned adapter. draw(ctx, seconds, subtitles) must be deterministic.
window.VIDEO_PROJECT={
 id:D.id,title:D.title,duration:D.DUR,fps:D.FPS,audio:D.audio,
 shots:D.shots.map(s=>({start:s.start+D.PRE,end:s.end+D.PRE,name:s.text})),
 captions:D.subs.map(([start,text,,end])=>[start+D.PRE,end+D.PRE,text]),
 images:window.ASSETS||[],fonts:D.fonts||[],draw:frame
};
