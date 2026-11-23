import numpy as np, wave, json, sys
from scipy.signal import lfilter
# Original synth score for the v4.5 promo. 120 BPM (0.5 s/beat), 30.0 s, A minor. Sync points come from sync.json (seconds).
SR = 44100; BPM = 120; BEAT = 0.5; TOTAL = 30.0; N = int(TOTAL * SR) + SR
rng = np.random.default_rng(45)
SY = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'sync.json'))

def add(buf, x, t, g=1.0):
    i = int(round(t * SR)); j = min(N, i + len(x))
    if 0 <= i < N: buf[i:j] += x[:j - i] * g
def noise(n): return rng.standard_normal(n)
def lp(x, fc):
    if np.ndim(fc) > 0: return lp_var(x, np.asarray(fc, float))
    a = np.exp(-2 * np.pi * fc / SR); return lfilter([1 - a], [1, -a], x)
def hp(x, fc): return x - lp(x, fc)
def bp(x, lo, hi): return lp(hp(x, lo), hi)
def lp_var(x, fc):  # time-varying one-pole (fc array), block-wise
    y = np.zeros_like(x); s = 0.0; B = 256
    for i in range(0, len(x), B):
        a = np.exp(-2 * np.pi * fc[min(i, len(fc) - 1)] / SR); seg = x[i:i + B]
        out, zf = lfilter([1 - a], [1, -a], seg, zi=[a * s]); y[i:i + B] = out; s = out[-1] if len(out) else s
    return y
def saw(freq, n, ph0=0.0): ph = (ph0 + np.cumsum(np.broadcast_to(freq, (n,)) / SR)) % 1.0; return 2 * ph - 1
def hz(nm):
    k = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}
    return 440 * 2 ** ((k[nm[:-1]] + 12 * (int(nm[-1]) + 1) - 69) / 12)
def T(n): return np.arange(int(n * SR)) / SR

# ---------- instruments ----------
def kick():
    t = T(0.45); f = 42 + 110 * np.exp(-t / 0.035); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.28)
    x[:50] += noise(50) * np.linspace(0.5, 0, 50); return np.tanh(2.4 * x)
def snare():
    t = T(0.3); x = bp(noise(len(t)), 1000, 5000) * np.exp(-t / 0.13) * 1.5 + np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.07) * 0.8
    return np.tanh(1.5 * x)
def hat(o=False): t = T(0.28 if o else 0.05); return hp(noise(len(t)), 7500) * np.exp(-t / (0.2 if o else 0.03))
def bass(f, d):
    t = T(d); x = 0.55 * saw(f * 1.003, len(t)) + 0.45 * saw(f * 0.997, len(t), 0.4) + 0.7 * np.sin(2 * np.pi * f * t)
    x = lp(x, 900); env = np.minimum(1, t / 0.004) * np.clip((d - t) / 0.04, 0, 1); return np.tanh(2.6 * x) * env
def lead(f, d, br=3200):
    t = T(d + 0.25); vib = 1 + 0.008 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.2)
    x = sum(saw(f * vib * 2 ** (c / 1200), len(t), k * 0.21) for k, c in enumerate([-10, 0, 10])) / 2.4 + 0.3 * saw(f * 2 * vib, len(t))
    x = lp(lp(x, br), br * 1.5); a = np.minimum(1, t / 0.01) * np.where(t < d, 1, np.exp(-(t - d) / 0.08)); return x * a
def pad(fs, d, cut=1600):
    t = T(d); x = np.zeros(len(t))
    for f in fs:
        for c in (-8, 0, 8): x += saw(f * 2 ** (c / 1200), len(t), rng.random())
    return lp(x, cut) / (3 * len(fs)) * np.minimum(1, t / 0.25) * np.clip((d - t) / 0.25, 0, 1)
def riser(d, top=9000):
    t = T(d); u = t / d; nz = bp(noise(len(t)), 300, 1200 + top * u ** 2)
    sw = np.sin(2 * np.pi * np.cumsum(90 * 12 ** u) / SR); return (nz * 1.1 + sw * 0.35) * u ** 2.2
def sub_hit(d=1.6):
    t = T(d); f = 32 + 70 * np.exp(-t / 0.06); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.7)
    x += lp(noise(len(t)), 250) * np.exp(-t / 0.18) * 1.6; return np.tanh(2 * x)
def slash():   # metal blade swish + ring
    t = T(0.6); u = t / 0.6; x = bp(noise(len(t)), 2500 + 5000 * u, 6000 + 5000 * u) * np.sin(np.pi * np.minimum(1, u * 2.2)) ** 1.5 * 2.2
    ring = sum(np.sin(2 * np.pi * f * t) for f in (1870, 2950, 4410)) * np.exp(-t / 0.18) * 0.18; return x + ring
def whoosh(d=0.5):
    t = T(d); u = t / d; return bp(noise(len(t)), 900 + 2500 * u, 2500 + 4500 * u) * np.sin(np.pi * u) ** 1.6 * 2.4
def cannon():
    t = T(1.2); f = 38 + 90 * np.exp(-t / 0.05); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45)
    x += lp(noise(len(t)), 1800) * np.exp(-t / 0.12) * 2.2; x[:int(0.004 * SR)] += noise(int(0.004 * SR)) * 2; return np.tanh(3 * x) * 0.9
def boom():
    t = T(1.2); f = 32 + 50 * np.exp(-t / 0.12); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.6)
    x += lp(noise(len(t)), 500) * np.exp(-t / 0.3) * 2.4; return np.tanh(3.5 * x) * 0.8
def clang(pitch=1.0):
    t = T(1.4); fr = np.array([523, 1187, 1951, 2733, 3720]) * pitch
    x = sum(np.sin(2 * np.pi * f * t + k) * np.exp(-t / (0.5 / (1 + k * 0.5))) for k, f in enumerate(fr)) / 3
    return x + bp(noise(len(t)), 2000, 8000) * np.exp(-t / 0.02) * 1.5
def clack():   # spring "clack-klang"
    t = T(0.9); c1 = bp(noise(len(t)), 1500, 5000) * np.exp(-t / 0.012) * 2.5
    k = np.zeros(len(t)); i = int(0.07 * SR); tt = t[:len(t) - i]
    k[i:] = (np.sin(2 * np.pi * 740 * tt) + 0.7 * np.sin(2 * np.pi * 1663 * tt) + 0.4 * np.sin(2 * np.pi * 2411 * tt)) * np.exp(-tt / 0.35) * 0.45
    spring = np.sin(2 * np.pi * (300 + 900 * np.exp(-t / 0.05)) * t) * np.exp(-t / 0.08) * 0.25
    return c1 + k + spring
def tear():   # metal tear
    t = T(0.9); x = bp(noise(len(t)), 300, 3000) * (0.6 + 0.4 * np.sin(2 * np.pi * 37 * t)) * np.exp(-t / 0.35) * 2
    x += np.sin(2 * np.pi * np.cumsum(220 - 120 * t) / SR) * np.exp(-t / 0.4) * 0.5; return np.tanh(1.8 * x)
def beep(f=1760, d=0.07): t = T(d); return np.sin(2 * np.pi * f * t) * np.minimum(1, t / 0.003) * np.clip((d - t) / 0.01, 0, 1)
def click(): t = T(0.05); return bp(noise(len(t)), 2000, 9000) * np.exp(-t / 0.006) * 1.6 + np.sin(2 * np.pi * 3200 * t) * np.exp(-t / 0.01) * 0.4
def static(d):
    t = T(d); x = hp(noise(len(t)), 1200) * (0.6 + 0.4 * (rng.random(len(t) // 400 + 1).repeat(400)[:len(t)] > 0.5)); return x
def crash(): t = T(2.0); return hp(noise(len(t)), 5200) * np.exp(-t / 1.0)
def reverb(x, d=2.2, mix=0.5):
    ir_t = T(d); ir = noise(len(ir_t)) * np.exp(-ir_t / (d / 5)); ir = lp(ir, 5000); ir /= np.sqrt(np.sum(ir ** 2))
    from scipy.signal import fftconvolve
    return x + mix * fftconvolve(x, ir)[:len(x)]

# ---------- buses ----------
drums = np.zeros(N); bassb = np.zeros(N); leadb = np.zeros(N); padb = np.zeros(N); fx = np.zeros(N); fxdry = np.zeros(N)
K, SN, HC, HO = kick(), snare(), hat(), hat(True)
CH = ['Am', 'F', 'C', 'G']
PADN = {'Am': ['A3', 'C4', 'E4'], 'F': ['F3', 'A3', 'C4'], 'C': ['C4', 'E4', 'G4'], 'G': ['G3', 'B3', 'D4'], 'Dm': ['D4', 'F4', 'A4'], 'E': ['E3', 'G#3', 'B3']}
ROOT = {'Am': 55.0, 'F': 43.65, 'C': 65.41, 'G': 49.0, 'Dm': 73.42, 'E': 41.2}
def chord_at(t): return CH[int(t // 2) % 4]
kicks = []

def groove(t0, t1, full=False, hats=True, snares=True):
    b = t0
    while b < t1 - 1e-6:
        add(drums, K, b, 1.0); kicks.append(b)
        k = round((b) / BEAT)
        if snares and k % 2 == 1: add(drums, SN, b, 0.55)
        if hats:
            add(drums, HC, b + BEAT / 2, 0.22)
            if full: add(drums, HC, b + BEAT / 4, 0.1); add(drums, HC, b + 3 * BEAT / 4, 0.1); add(drums, HO, b + BEAT / 2, 0.08)
        b += BEAT
def bassline(t0, t1, gate=0.8):
    b = t0
    while b < t1 - 1e-6:
        r = ROOT[chord_at(b)]
        for j, m in enumerate((1, 1, 2, 1)):
            tt = b + j * BEAT / 4
            if tt < t1 - 1e-6: add(bassb, bass(r * m, BEAT / 4 * gate), tt, 0.5)
        b += BEAT
def pads(t0, t1, g=0.5, cut=1600):
    b = t0
    while b < t1 - 1e-6:
        d = min(2.0 - (b % 2.0), t1 - b); add(padb, pad([hz(n) for n in PADN[chord_at(b)]], d, cut), b, g); b += d

# --- intro 0-3: pad swell, riser, static, countdown blips
pads(0, 3.0, 0.45, 900)
add(fx, static(0.6) * np.linspace(1, 0, int(0.6 * SR)), 0.0, 0.25)
add(fx, riser(3.0, 6000), 0.0, 0.35)
for i, t in enumerate(SY['count']): add(fxdry, beep(880 if i < 2 else 1320, 0.09), t, 0.35)
# --- 3.0 downbeat: sub hit + metal slash; S2 static burst
add(fxdry, sub_hit(), 3.0, 1.0); add(fx, static(0.12), 3.0, 0.35)
for t in SY['slash']: add(fx, slash(), t, 0.7)
pads(3.0, 4.0, 0.35, 1100)
# --- 4.0-7.5 swing: drums in, rope whoosh, filter dip at apex
groove(4.0, 7.5); bassline(4.0, 7.5); pads(4.0, 7.5, 0.4)
for t in SY['rope']: add(fx, whoosh(0.6), t, 0.55)
# --- 7.5-10 cannon: groove continues, cannon on the beat, drop out during the freeze
groove(7.5, 10.0, snares=True); bassline(7.5, 10.0); pads(7.5, 10.0, 0.4)
for t in SY['cannon']: add(fxdry, cannon(), t, 0.9)
for t in SY['boom']: add(fxdry, boom(), t, 0.75)
# --- 10-15 blade: half-time, long riser into the drop
pads(10.0, 15.0, 0.42, 1300)
b = 10.0
while b < 15.0 - 1e-6:
    add(drums, K, b, 0.8 if b < 12.5 else 0.9); kicks.append(b); b += 1.0
for i in range(16): add(drums, SN, 14.0 + i * 0.0625, 0.15 + 0.45 * i / 16)
add(fx, riser(5.0, 10000), 10.0, 0.5)
for t in SY['clack']: add(fxdry, clack(), t, 0.95)
for t in SY['tear']: add(fxdry, tear(), t, 0.9); add(fxdry, boom(), t, 0.5)
for t in SY['slash2']: add(fx, slash(), t, 0.6)
# --- 15-19 main theme (drop)
add(fxdry, sub_hit(1.2), 15.0, 0.8); add(fx, crash(), 15.0, 0.35)
groove(15.0, 19.0, full=True); bassline(15.0, 19.0, 0.9); pads(15.0, 19.0, 0.5, 2200)
MEL = [('E5', 0, 1), ('A5', 1, 1), ('G5', 2, 1), ('E5', 3, 1), ('C5', 4, 2), ('D5', 6, 1), ('E5', 7, 1),
       ('E5', 8, 1), ('A5', 9, 1), ('B5', 10, 1), ('C6', 11, 1), ('B5', 12, 2), ('G5', 14, 1), ('A5', 15, 1)]
for nm, st, ln in MEL: add(leadb, lead(hz(nm), ln * BEAT / 2 * 0.9, 4200), 15.0 + st * BEAT / 2, 0.24)
for i, t in enumerate(SY['lock']): add(fxdry, beep(1760 if i < len(SY['lock']) - 1 else 2350, 0.06 if i < len(SY['lock']) - 1 else 0.3), t, 0.3)
for t in SY['cannon2']: add(fxdry, cannon(), t, 0.85)
for t in SY['boom2']: add(fxdry, boom(), t, 0.7)
for t in SY['hop']: add(fx, whoosh(0.45), t, 0.45)
# --- 19-22.5 parry: groove, clangs, cut to tail on freeze
FZ = SY['freeze8']
groove(19.0, FZ, full=True); bassline(19.0, FZ, 0.9); pads(19.0, FZ, 0.5, 2200)
for nm, st, ln in MEL[:10]:
    if 19.0 + st * BEAT / 2 < FZ - 0.1: add(leadb, lead(hz(nm), ln * BEAT / 2 * 0.9, 4200), 19.0 + st * BEAT / 2, 0.22)
for t in SY['cannon3']: add(fxdry, cannon(), t, 0.7)
for t in SY['clang']: add(fxdry, clang(1.0), t, 0.75)
for t in SY['parry']: add(fxdry, clang(0.8), t, 0.9); add(fxdry, sub_hit(0.8), t, 0.5)
for t in SY['flash']: add(fx, whoosh(0.3), t - 0.1, 0.4)
for t in SY['slash3']: add(fx, slash(), t, 0.6)
add(fxdry, clang(0.6), FZ, 0.5)
# --- 22.5-25.5 hangar: music returns, UI click per paint change
groove(22.5, 25.5); bassline(22.5, 25.5); pads(22.5, 25.5, 0.45)
for t in SY['clicks']: add(fxdry, click(), t, 0.6)
add(fx, whoosh(0.4), 22.4, 0.35)
# --- 25.5-27.5 three rising chords
for i, (t, ch) in enumerate(zip(SY['chords'], [['A3', 'C4', 'E4', 'A4'], ['C4', 'E4', 'G4', 'C5'], ['D4', 'F#4', 'A4', 'D5']])):
    add(padb, pad([hz(n) for n in ch], 0.5 if i < 2 else 1.0, 3500), t, 0.75)
    add(drums, K, t, 0.9); add(fx, crash()[:int(0.5 * SR)], t, 0.15 + 0.05 * i); kicks.append(t)
add(fx, riser(1.0, 8000), 26.5, 0.4)
# --- 27.5 final hit, reverb tail + static fade
add(fxdry, sub_hit(2.5), 27.5, 1.0); add(fx, crash(), 27.5, 0.45)
add(padb, pad([hz(n) for n in ['A2', 'E3', 'A3', 'C4', 'E4']], 2.4, 2500), 27.5, 0.6)
add(fx, static(1.2) * np.linspace(0, 1, int(1.2 * SR)) ** 2, 28.6, 0.22)

# ---------- automation ----------
music_gain = np.ones(N)
def mute(t0, t1, fade=0.02):
    i, j = int(t0 * SR), int(t1 * SR); f = int(fade * SR); music_gain[i:j] = 0
    music_gain[max(0, i - f):i] *= np.linspace(1, 0, min(f, i)); music_gain[j:j + f] *= np.linspace(0, 1, f)
for a, b in SY['mute']: mute(a, b)
# cut to tail on the S8 freeze: music bus silent from FZ to 22.5 (tail comes from reverb on fx/clang)
i = int(FZ * SR); j = int(22.5 * SR); music_gain[i:j] = 0; music_gain[i - 400:i] *= np.linspace(1, 0, 400)
fc = np.full(N, 16000.0)
for a, b in SY['dip']:   # filter dip at the swing apex
    i, j = int(a * SR), int(b * SR); n = j - i; u = np.linspace(0, 1, n); fc[i:j] = 16000 * (1 - np.sin(np.pi * u) ** 0.6 * 0.96) + 300
# 10-15 opening filter on pads as the riser builds
i, j = int(10 * SR), int(15 * SR); fc[i:j] = np.minimum(fc[i:j], 600 + 15000 * np.linspace(0, 1, j - i) ** 2)
duck = np.ones(N)
for tk in kicks:
    i = int(tk * SR); n = int(0.28 * SR); j = min(N, i + n); duck[i:j] = np.minimum(duck[i:j], 1 - 0.45 * np.exp(-np.arange(j - i) / SR / 0.1))
music = drums * 0.85 + (bassb + padb) * duck + leadb * (0.6 + 0.4 * duck)
music = lp_var(music, fc) * music_gain
wet = reverb(fx + 0.6 * fxdry, 2.4, 0.45)
mix = music + wet * 0.9
mix = mix + 0.2 * hp(mix, 8000)
mix = np.tanh(1.15 * mix / (np.percentile(np.abs(mix), 99.7) + 1e-9))
d = int(0.011 * SR); side = np.zeros(N); side[d:] = ((padb + leadb) * 0.12 * music_gain)[:-d]
Lc, Rc = mix + side, mix - side
end = int(TOTAL * SR); fd = int(0.9 * SR)
for c in (Lc, Rc): c[end - fd:end] *= np.linspace(1, 0, fd) ** 1.5; c[end:] = 0
pk = max(np.abs(Lc).max(), np.abs(Rc).max()); Lc, Rc = Lc / pk * 0.89, Rc / pk * 0.89
st = np.stack([Lc[:end], Rc[:end]], 1)
with wave.open('music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
print('ok', end / SR)
