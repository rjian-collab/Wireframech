import numpy as np, wave
SR = 44100; BPM = 140; STEP = 60 / BPM / 4; BAR = STEP * 16
TOTAL = 838 / 30
N = int(TOTAL * SR) + SR
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)          # stereo buses
music = np.zeros(N); kickTrig = []

def t_of(bar, step): return ((bar - 1) * 16 + step) * STEP
def add(buf, x, t, g=1.0):
    i = int(t * SR); j = min(N, i + len(x))
    if i < N: buf[i:j] += x[:j - i] * g
def env_exp(n, tau): return np.exp(-np.arange(n) / SR / tau)
def noise(n): return rng.standard_normal(n)
def onepole_lp(x, fc):
    if np.ndim(fc) == 0:
        from scipy.signal import lfilter
        a = np.exp(-2 * np.pi * fc / SR); return lfilter([1 - a], [1, -a], x)
    a = np.exp(-2 * np.pi * np.asarray(fc) / SR); y = np.zeros_like(x); s = 0.0
    a = np.broadcast_to(a, x.shape)
    for i in range(len(x)): s = (1 - a[i]) * x[i] + a[i] * s; y[i] = s
    return y
def lp_fast(x, fc):  # constant-cutoff one-pole via lfilter-free cumulative approach (scipy-less)
    from numpy.lib.stride_tricks import sliding_window_view
    return onepole_lp(x, fc)
def hp(x, fc): return x - onepole_lp(x, fc)
def bp(x, lo, hi): return onepole_lp(hp(x, lo), hi)
def saw(freq, n, phase0=0.0):
    ph = (phase0 + np.cumsum(np.broadcast_to(freq, (n,)) / SR)) % 1.0
    return 2 * ph - 1
def note_hz(name):
    names = {'C':0,'C#':1,'D':2,'D#':3,'E':4,'F':5,'F#':6,'G':7,'G#':8,'A':9,'A#':10,'Bb':10,'B':11}
    o = int(name[-1]); k = name[:-1]
    return 440 * 2 ** ((names[k] + 12 * (o + 1) - 69) / 12)

# ---------- instruments ----------
def kick():
    n = int(0.4 * SR); t = np.arange(n) / SR
    f = 45 + 105 * np.exp(-t / 0.04); ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / 0.25); x[:60] += noise(60) * np.linspace(0.6, 0, 60)
    return np.tanh(2.5 * x)
def snare():
    n = int(0.3 * SR); t = np.arange(n) / SR
    x = bp(noise(n), 900, 4000) * np.exp(-t / 0.15) * 1.6 + np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.08) * 0.8
    return np.tanh(1.5 * x)
def clap():
    n = int(0.25 * SR); x = np.zeros(n)
    for k in range(3):
        i = int(k * 0.010 * SR); m = int(0.008 * SR); x[i:i + m] += noise(m)
    t = np.arange(n) / SR; x += bp(noise(n), 800, 2500) * np.exp(-t / 0.1)
    return x * 0.8
def hat(open_=False):
    n = int((0.3 if open_ else 0.06) * SR); t = np.arange(n) / SR
    return hp(noise(n), 7000) * np.exp(-t / (0.25 if open_ else 0.035))
def bass_note(freq, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = 0.5 * saw(freq * 2 ** (5 / 1200), n) + 0.5 * saw(freq * 2 ** (-5 / 1200), n, 0.3) + 0.6 * np.sin(2 * np.pi * freq * t)
    x = onepole_lp(x, 250 + 650 * np.exp(-t / 0.15))
    a = np.minimum(1, t / 0.005) * np.where(t < dur - 0.05, 1.0, np.maximum(0, (dur - t) / 0.05))
    return np.tanh(3 * x) * a
def lead_note(freq, dur, bright=3000):
    n = int((dur + 0.2) * SR); t = np.arange(n) / SR
    vib = 1 + 0.0087 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.15)
    x = sum(saw(freq * vib * 2 ** (c / 1200), n, k * 0.17) for k, c in enumerate([-12, -7, 0, 7, 12])) / 3
    x += 0.35 * saw(freq * 2 * vib, n)
    x = onepole_lp(onepole_lp(x, bright), bright * 1.4)
    a = np.minimum(1, t / 0.01); a = a * np.where(t < 0.11, 1 - 0.3 * (t / 0.11), 0.7)
    a = a * np.where(t < dur, 1, np.exp(-(t - dur) / 0.06))
    return x * a
def pad_chord(freqs, dur):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for f in freqs:
        for c in (-9, 0, 9): x += saw(f * 2 ** (c / 1200), n, rng.random())
    x = onepole_lp(x, 1500) / (3 * len(freqs))
    return x * np.minimum(1, t / 0.3) * np.minimum(1, (dur - t) / 0.2 + 0.0)
def riser(dur):
    n = int(dur * SR); t = np.arange(n) / SR; u = t / dur
    nz = bp(noise(n), 300 + 3000 * u ** 2, 600 + 9000 * u ** 2)
    f = 80 * (10 ** u); sw = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return (nz * 1.2 + sw * 0.4) * u ** 2
def impact():
    n = int(1.4 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 40 * t + 6 * np.exp(-t / 0.05)) * np.exp(-t / 0.5) + onepole_lp(noise(n), 300) * np.exp(-t / 0.4) * 2
    return np.tanh(1.8 * x)
def crash():
    n = int(1.6 * SR); t = np.arange(n) / SR
    return hp(noise(n), 5000) * np.exp(-t / 0.9)
def whoosh():
    n = int(0.5 * SR); t = np.arange(n) / SR; u = t / 0.5
    x = bp(noise(n), 1500 + 3000 * u, 3000 + 4000 * u) * np.sin(np.pi * u) ** 1.5 * 2.5
    x += np.sin(2 * np.pi * 1200 * t + 0.3 * np.sin(2 * np.pi * 500 * t)) * np.exp(-t / 0.15) * 0.25
    return x
def boom():
    n = int(1.2 * SR); t = np.arange(n) / SR
    f = 35 + 55 * np.exp(-t / 0.12); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.6)
    x += onepole_lp(noise(n), 500) * np.exp(-t / 0.25) * 2.5; x[:int(0.003 * SR)] += noise(int(0.003 * SR)) * 1.5
    return np.tanh(4 * x) * 0.8
def clank():
    n = int(0.25 * SR); t = np.arange(n) / SR
    return bp(noise(n), 2500, 4000) * np.exp(-t / 0.03) + (np.sin(2 * np.pi * 880 * t) + np.sin(2 * np.pi * 1320 * t)) * np.exp(-t / 0.05) * 0.5
def power_chord():
    n = int(2.2 * SR); t = np.arange(n) / SR
    x = sum(saw(note_hz(nm) * 2 ** (c / 1200), n, rng.random()) for nm in ['A1', 'A2', 'E3', 'A3', 'E4'] for c in (-8, 8)) / 6
    return np.tanh(2 * onepole_lp(x, 4000)) * np.exp(-t / 0.9) * np.minimum(1, t / 0.005)

K, SN, CL, HC, HO = kick(), snare(), clap(), hat(), hat(True)
CHORDS = {1: 'Am', 2: 'F', 3: 'Am', 4: 'F', 5: 'Dm', 6: 'E', 7: 'Dm', 8: 'E', 9: 'Am', 10: 'F', 11: 'Dm', 12: 'E', 13: 'Am', 14: 'F', 15: 'Dm', 16: 'Am'}
PAD = {'Am': ['A3', 'C4', 'E4'], 'F': ['F3', 'A3', 'C4'], 'Dm': ['D3', 'F3', 'A3'], 'E': ['E3', 'G#3', 'B3']}
ROOT = {'Am': 55.0, 'F': 43.65, 'Dm': 73.42, 'E': 82.41}
GAP0, GAP1 = t_of(8, 12), t_of(9, 0)
drums = np.zeros(N); bassb = np.zeros(N); leadb = np.zeros(N); padb = np.zeros(N); fxb = np.zeros(N)

for bar in range(1, 17):
    ch = CHORDS[bar]
    # pads (all but bar 16)
    if bar < 16:
        add(padb, pad_chord([note_hz(n) for n in PAD[ch]], BAR), t_of(bar, 0), 0.55 if bar > 2 else 0.35)
    # drums
    if 3 <= bar <= 15 and bar != 8:
        for st in (0, 4, 8, 12):
            if bar == 15 and st >= 8: break
            add(drums, K, t_of(bar, st), 1.0); kickTrig.append(t_of(bar, st))
    if bar == 8:
        for st in (0, 4, 8): add(drums, K, t_of(bar, st)); kickTrig.append(t_of(bar, st))
    if 3 <= bar <= 14 and bar not in (7, 8):
        for st in (4, 12): add(drums, SN, t_of(bar, st), 0.55); add(drums, CL, t_of(bar, st), 0.35)
        hstep = 1 if bar >= 9 else 2
        for st in range(0, 16, hstep): add(drums, HC, t_of(bar, st), 0.12 if st % 2 else 0.2)
        if bar >= 9:
            for st in (2, 6, 10, 14): add(drums, HO, t_of(bar, st), 0.1)
        else: add(drums, HO, t_of(bar, 14), 0.12)
        if bar % 2 == 0: add(drums, clank(), t_of(bar, 10), 0.25)
    if bar == 7:
        for st in range(0, 16, 2): add(drums, SN, t_of(bar, st), 0.25 + 0.2 * st / 16)
    if bar == 8:
        for st in range(0, 12): add(drums, SN, t_of(bar, st), 0.35 + 0.4 * st / 12)
    if bar == 12:
        for st in (12, 13, 14, 15): add(drums, SN, t_of(bar, st), 0.5)
    if bar == 15:
        for st in range(0, 8, 2): add(drums, SN, t_of(bar, st), 0.5)
    # bass
    if 3 <= bar <= 15:
        gate = 0.8 if bar >= 9 else 0.5
        for st in range(0, 16, 2):
            if bar == 8 and st >= 12: break
            f = ROOT[ch] * (2 if st % 4 == 2 else 1)
            add(bassb, bass_note(f, 2 * STEP * gate), t_of(bar, st), 0.55)
    if bar == 16: add(bassb, bass_note(55.0, 2.0) * np.exp(-np.arange(int(2.0 * SR)) / SR / 0.9), t_of(16, 0), 0.6)

# lead
MA = [('A3', 0), ('C4', 2), ('E4', 4), ('A4', 6), ('G4', 8), ('E4', 10), ('C4', 12), ('D4', 14)]
MB = [('F4', 0), ('E4', 2), ('A4', 4, 4), ('C5', 8), ('B4', 10), ('A4', 12), ('E4', 14)]
INV11 = [('A5', 0), ('F5', 2), ('D5', 4), ('A4', 6), ('B4', 8), ('D5', 10), ('F5', 12), ('E5', 14)]
INV12 = [('C5', 0), ('D5', 2), ('A4', 4, 4), ('F4', 8), ('G4', 10), ('A4', 12), ('D5', 14)]
def up(m, k=1): return [(n[:-1] + str(int(n[-1]) + k),) + tuple(r) for n, *r in m]
def play(m, bar, gain, bright=3000):
    for item in m:
        nm, st = item[0], item[1]; ln = item[2] if len(item) > 2 else 2
        add(leadb, lead_note(note_hz(nm), ln * STEP * 0.9, bright), t_of(bar, st), gain)
play(MA, 5, 0.22, 2200); play(MB, 6, 0.22, 2200)
for st in range(0, 16, 2): add(leadb, lead_note(note_hz('A4'), STEP * 0.8, 1500 + 200 * st), t_of(7, st), 0.12 + 0.01 * st)
for st in range(0, 12, 2): add(leadb, lead_note(note_hz('A4'), STEP * 0.8, 3000 + 300 * st), t_of(8, st), 0.18 + 0.01 * st)
play(up(MA), 9, 0.3, 4200); play(up(MB), 10, 0.3, 4200)
play(INV11, 11, 0.3, 4200); play(INV12, 12, 0.3, 4200)
play(up(MA), 13, 0.3, 4200); play([x for x in up(MB) if x[1] < 14] + [('E5', 14, 1), ('A5', 15, 1)], 14, 0.3, 4200)
add(leadb, lead_note(note_hz('A5'), BAR * 0.95, 4200), t_of(15, 0), 0.3)

# fx: intro riser, build riser, drop impact, end hit, and picture-synced hits (frame/30)
add(fxb, riser(2 * BAR), 0, 0.45)
add(fxb, riser(GAP0 - t_of(7, 0)), t_of(7, 0), 0.5)
add(fxb, impact(), GAP1, 0.9); add(fxb, crash(), GAP1, 0.35)
END = t_of(16, 0)
add(fxb, impact(), END, 0.9); add(fxb, crash(), END, 0.4); add(leadb, power_chord(), END, 0.5)
SYNC = [[103,'boom'],[142,'whoosh'],[154,'whoosh'],[232,'boom'],[309,'whoosh'],[348,'whoosh'],[399,'whoosh'],[412,'boom'],[425,'boom'],
        [463,'whoosh'],[469,'whoosh'],[502,'boom'],[579,'boom'],[604,'whoosh'],[630,'boom'],[656,'boom'],[669,'whoosh'],[675,'whoosh'],[694,'boom'],[707,'boom']]
import json, os
if os.path.exists('sync.json'): SYNC = json.load(open('sync.json'))
for fr, kind in SYNC:
    if kind == 'mg':
        n = int(0.07 * SR); t = np.arange(n) / SR
        add(fxb, np.tanh(3 * (bp(noise(n), 600, 3500) * np.exp(-t / 0.018) * 2 + np.sin(2 * np.pi * 110 * t) * np.exp(-t / 0.03))), fr / 30, 0.16)
    else: add(fxb, boom() if kind == 'boom' else whoosh(), fr / 30, 0.55 if kind == 'boom' else 0.3)

# silence gap
gi, gj = int(GAP0 * SR), int(GAP1 * SR)
for b in (drums, bassb, leadb, padb): b[gi:gj] *= np.linspace(1, 0, gj - gi) ** 8

# sidechain duck
duck = np.ones(N)
for tk in kickTrig:
    i = int(tk * SR); n = int(0.3 * SR); j = min(N, i + n)
    duck[i:j] = np.minimum(duck[i:j], 1 - 0.5 * np.exp(-np.arange(j - i) / SR / 0.12))
mix = drums * 0.9 + (bassb + padb) * duck + leadb * (0.6 + 0.4 * duck) + fxb
# high shelf-ish brightening + soft clip + normalise
mix = mix + 0.25 * hp(mix, 8000)
mix = np.tanh(1.2 * mix / (np.percentile(np.abs(mix), 99.5) + 1e-9))
# stereo: slight width via delayed copy for pad/lead
d = int(0.012 * SR); side = np.zeros(N); side[d:] = ((padb + leadb) * 0.15)[:-d]
Lc, Rc = mix + side, mix - side
end = int(TOTAL * SR); fade = int(0.5 * SR)
for c in (Lc, Rc): c[end - fade:end] *= np.linspace(1, 0, fade); c[end:] = 0
pk = max(np.abs(Lc).max(), np.abs(Rc).max()); Lc, Rc = Lc / pk * 0.89, Rc / pk * 0.89
st = np.stack([Lc[:end], Rc[:end]], 1)
with wave.open('music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
print('ok', end / SR)
