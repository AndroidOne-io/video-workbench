import numpy as np
from scipy import signal
SR = 48000; rng = np.random.default_rng(4)
def tt(d): return np.arange(int(d * SR)) / SR
def bp(x, lo, hi): b, a = signal.butter(2, [lo / (SR / 2), min(hi / (SR / 2), .99)], 'band'); return signal.lfilter(b, a, x)
def hp(x, f): b, a = signal.butter(2, f / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def make(k):
    if k == 'shine':
        t = tt(1.2); y = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 3) for f in (2093, 2637, 3136, 4186)) * .05
        y += hp(rng.standard_normal(len(t)), 6000) * np.exp(-((t - .25) / .2) ** 2) * .08
    elif k == 'scribble':
        t = tt(.35); y = bp(rng.standard_normal(len(t)), 1500, 6000) * (0.5 + 0.5 * np.sin(2 * np.pi * 18 * t)) * np.exp(-t * 4) * .2
    elif k == 'pop':
        t = tt(.16); y = np.sin(2 * np.pi * np.cumsum(900 * np.exp(-t * 25) + 350) / SR) * np.exp(-t * 30) * .18
    elif k == 'type':
        t = tt(.05); y = bp(rng.standard_normal(len(t)), 1500, 7000) * np.exp(-t * 160) * .2
    else:
        y = np.zeros(10)
    return np.stack([y, y], 1).astype(np.float32)
