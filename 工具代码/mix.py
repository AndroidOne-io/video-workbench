# Music + SFX mixer driven by a cue sheet. Usage: mix.py cues.json out.wav
import json, subprocess, sys, numpy as np
SR = 48000
MD = '/tmp/claude-0/music/ts/materials/audio/音乐素材/'
def load(p, ss=0, t=None):
    cmd = ['ffmpeg', '-loglevel', 'error', '-ss', str(max(0, ss))] + (['-t', str(t)] if t else []) + ['-i', p, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).reshape(-1, 2).copy()
def lufs(x):
    p = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', '-af', 'ebur128', '-f', 'null', '-'], input=x.astype(np.float32).tobytes(), capture_output=True)
    for ln in p.stderr.decode().splitlines()[::-1]:
        if ln.strip().startswith('I:'):
            v = float(ln.split()[1]); return v if v > -70 else -70
C = json.load(open(sys.argv[1])); END = C['end']; N = int(END * SR) + SR
voice = np.zeros((N, 2), np.float32)
for seg in C['voice']:  # {src, ss, dur, at, lufs}
    if seg['at'] >= END: continue
    x = load(seg['src'], seg['ss'], min(seg['dur'], END - seg['at'] + 0.1)); x *= 10 ** ((seg.get('lufs', -16) - lufs(x)) / 20)
    fz = min(240, len(x) // 2); x[:fz] *= np.linspace(0, 1, fz)[:, None]; x[-fz:] *= np.linspace(1, 0, fz)[:, None]
    i = int(seg['at'] * SR)
    if i >= N: continue
    x = x[:N - i]; voice[i:i + len(x)] += x
env = np.convolve(np.abs(voice).mean(1), np.ones(4800) / 4800, 'same')
speech = np.clip(env / (np.percentile(env[env > 0] if (env > 0).any() else env, 90) * 0.3 + 1e-9), 0, 1)
speech = np.convolve(speech, np.ones(9600) / 9600, 'same')
music = np.zeros((N, 2), np.float32)
for m in C['music']:  # {file, src, at, until, fade_in, fade_out, level(LUFS when unducked)}
    d = m['until'] - m['at']; x = load(MD + '音乐/' + m['file'], m['src'], d + 0.1)[:int(d * SR)]
    if len(x) == 0: continue
    ref = lufs(load(MD + '音乐/' + m['file'], m.get('ref_ss', m['src']), 20))
    x *= 10 ** ((m.get('level', -20) - ref) / 20)
    fi, fo = int(m.get('fade_in', 0.05) * SR), int(m.get('fade_out', 0.3) * SR)
    if fi: x[:fi] *= np.linspace(0, 1, min(fi, len(x)))[:, None][:len(x[:fi])]
    if fo: x[-fo:] *= np.linspace(1, 0, min(fo, len(x)))[:, None]
    i = int(m['at'] * SR); j = min(N, i + len(x)); music[i:j] += x[:j - i]
g = 1 - (1 - 10 ** (C.get('duck_db', -9) / 20)) * speech
for a, b, gain in C.get('swell', []):  # force unducked gain in pauses
    i0, i1 = int(a * SR), int(b * SR); g[i0:i1] = np.maximum(g[i0:i1], gain)
for a, b in C.get('dip', []):  # silence right before a hit
    i0, i1 = int(a * SR), int(b * SR); g[i0:i1] *= 0.08
music *= g[:, None]
sfx = np.zeros((N, 2), np.float32)
for s in C['sfx']:  # {file, at, gain_db, align:'start'|'end'|'peak'}
    x = load(MD + '音效/' + s['file']); x *= 10 ** ((s.get('gain_db', -18) - lufs(x)) / 20)
    if s.get('align') == 'end': at = s['at'] - len(x) / SR
    elif s.get('align') == 'peak': at = s['at'] - np.argmax(np.abs(x).mean(1)) / SR
    else: at = s['at']
    i = int(at * SR); x = x[max(0, -i):]; i = max(0, i); j = min(N, i + len(x)); sfx[i:j] += x[:j - i]
for s in C.get('synth', []):
    import synthfx; x = synthfx.make(s['kind']) * 10 ** (s.get('gain_db', 0) / 20)
    i = int(s['at'] * SR); j = min(N, i + len(x)); sfx[i:j] += x[:j - i]
mix = (voice + music + sfx)[:int(END * SR)]
e = int(END * SR); fo = int(0.8 * SR); mix[e - fo:e] *= np.linspace(1, 0, fo)[:, None]
x = mix.astype(np.float32).tobytes()
base = ['ffmpeg', '-hide_banner', '-nostats', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-']
p = subprocess.run(base + ['-af', 'loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json', '-f', 'null', '-'], input=x, capture_output=True)
js = p.stderr.decode(); mm = json.loads(js[js.rindex('{'):js.rindex('}') + 1])
af = 'loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=true'.format(**mm)
subprocess.run(base + ['-af', af, '-c:a', 'pcm_s16le', '-y', sys.argv[2]], input=x, check=True, capture_output=True)
print('voice', lufs(voice), 'music', lufs(music), 'sfx', lufs(sfx))
