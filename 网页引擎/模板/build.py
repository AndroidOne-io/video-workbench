"""数据构建只写 JSON/JS；示例用静音 WAV 提供时钟，不生成视频。"""
import json
import html
import uuid
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build():
    p = json.loads((ROOT / 'project.json').read_text())
    if not p.get('id'):
        p['id'] = str(uuid.uuid4())
        (ROOT/'project.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n')
    shots = p['shots']
    assert shots and len({s['i'] for s in shots}) == len(shots)
    assert shots[0]['start'] == 0
    assert all(0 <= s['start'] < s['end'] for s in shots)
    assert all(abs(a['end'] - b['start']) < 1e-6 for a,b in zip(shots,shots[1:]))
    fps, duration = p['fps'], shots[-1]['end']
    assert 0 < fps <= 120
    by_id = {s['i']: s for s in shots}
    subs = []
    for a, text, i, b in p['subs']:
        assert i in by_id and by_id[i]['start'] <= a < b <= by_id[i]['end']
        # 不机械删除语气词。完整校对后输入；顿号统一为单个空格。
        text = text.replace('、', ' ')
        assert not any(c in text for c in '，。？！：；“”「」（）…'), text
        subs.append([a, text, i, b])
    assert all(a[3] <= b[0] for a,b in zip(subs,subs[1:]))
    assert all(0 <= t <= duration for t in p['events'].values())
    audio = p['audio']
    if audio == '_demo-clock.wav':
        with wave.open(str(ROOT / audio), 'wb') as f:
            f.setparams((1,2,16000,0,'NONE','not compressed'))
            f.writeframes(bytes(round(duration*16000)*2))
    elif not (ROOT / audio).is_file():
        raise FileNotFoundError(f'先准备混音文件：{audio}')
    d = dict(id=p['id'],title=p['title'],fonts=p.get('fonts',[]),W=1920,H=1080,FPS=fps,PRE=0,TOTAL=duration,DUR=duration,
             shots=shots,subs=subs,EV=p['events'],audio=audio)
    for filename, var, data in [('data.js','D',d),('sources.js','VSRC',p['sources']),
                                ('assets.js','ASSETS',p['images'])]:
        (ROOT / filename).write_text(f'window.{var} = '+json.dumps(data,ensure_ascii=False)+';\n')
    scripts=['data.js','engine.js','sources.js','assets.js','common.js']+p.get('sceneScripts',['scenes.js'])+['preview.js','player-ui.js','player.js']
    for src in scripts:
        path=(ROOT/src).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file() or path.suffix!='.js':
            raise ValueError(f'场景脚本必须是项目内的 JS 文件：{src}')
    (ROOT/'index.html').write_text('<!doctype html>\n<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>视频预览</title><link rel="stylesheet" href="style.css"><link rel="stylesheet" href="fonts.css"></head><body>\n'+'\n'.join(f'<script src="{html.escape(src,quote=True)}"></script>' for src in scripts)+'\n</body></html>\n')
    print(f'已生成时间线 {duration:g}s；{len(shots)} 镜；{len(subs)} 条字幕')


if __name__ == '__main__':
    build()
