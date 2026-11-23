import numpy as np, wave, json, sys
from scipy.signal import lfilter, fftconvolve
# v2 score — written from scratch. 128.57 BPM (one beat = 14 video frames = 0.4667 s), F# minor,
# progression i–iv–bII–V (F#m – Bm – G – C#), half-time intro, syncopated breakbeat drums, sub-bass,
# arpeggiated pluck lead, dark 7-voice detuned saw pads, glitch/bit-crushed static risers, FM metal hits.
SR = 44100; BEAT = 14 / 30; BAR = 4 * BEAT; TOTAL = 1008 / 30; N = int(TOTAL * SR) + SR
rng = np.random.default_rng(2045)
SY = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'sync3.json'))
def g(fr): return fr / 30.0
def T(d): return np.arange(int(d * SR)) / SR
def add(buf, x, t, gain=1.0):
    i = int(round(t * SR)); j = min(N, i + len(x))
    if 0 <= i < N: buf[i:j] += x[:j - i] * gain
def nz(n): return rng.standard_normal(n)
def lpf(x, fc):
    if np.ndim(fc):   # block-wise time-varying
        y = np.zeros_like(x); z = 0.0
        for i in range(0, len(x), 128):
            a = np.exp(-2 * np.pi * fc[min(i, len(fc) - 1)] / SR); out, zf = lfilter([1 - a], [1, -a], x[i:i + 128], zi=[a * z]); y[i:i + 128] = out; z = out[-1]
        return y
    a = np.exp(-2 * np.pi * fc / SR); return lfilter([1 - a], [1, -a], x)
def hpf(x, fc): return x - lpf(x, fc)
def svf_bp(x, f0, q=4):   # 2-pole resonant band-pass (biquad)
    w = 2 * np.pi * f0 / SR; al = np.sin(w) / (2 * q); b = [al, 0, -al]; a = [1 + al, -2 * np.cos(w), 1 - al]; return lfilter(b, a, x)
def osc_saw(f, n, ph=0.0): p = (ph + np.cumsum(np.broadcast_to(f, (n,)) / SR)) % 1; return 2 * p - 1
def osc_sq(f, n, pw=0.5): p = np.cumsum(np.broadcast_to(f, (n,)) / SR) % 1; return np.where(p < pw, 1.0, -1.0)
NOTE = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'E#': 5, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
def hz(s): return 440 * 2 ** ((NOTE[s[:-1]] + 12 * (int(s[-1]) + 1) - 69) / 12)

# ---------- instruments ----------
def kick():
    t = T(0.32); f = 38 + 140 * np.exp(-t / 0.022); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    click = svf_bp(nz(len(t)), 3500, 2) * np.exp(-t / 0.004) * 0.9; return np.tanh(3.2 * x + click)
def clap():
    t = T(0.35); x = np.zeros(len(t))
    for k, d in enumerate((0, 0.007, 0.016, 0.023)): i = int(d * SR); m = int(0.006 * SR); x[i:i + m] += nz(m) * (1 - k * 0.15)
    x += svf_bp(nz(len(t)), 1400, 1.2) * np.exp(-t / 0.09) * 0.8; return x * 0.9
def rim(): t = T(0.08); return (np.sin(2 * np.pi * 1730 * t) + 0.6 * np.sin(2 * np.pi * 2650 * t)) * np.exp(-t / 0.012) + svf_bp(nz(len(t)), 5000, 3) * np.exp(-t / 0.005)
def hat(o=False): t = T(0.35 if o else 0.04); return hpf(nz(len(t)), 8500) * np.exp(-t / (0.12 if o else 0.016))
def shaker(): t = T(0.07); return svf_bp(nz(len(t)), 6500, 1.5) * np.sin(np.pi * t / 0.07) ** 2
def sub(f, d):
    t = T(d); x = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t)
    return np.tanh(1.4 * x) * np.minimum(1, t / 0.006) * np.clip((d - t) / 0.03, 0, 1)
def growl(f, d):   # mid bass: pulse + square, band-limited, for the drop
    t = T(d); x = osc_sq(f * 2, len(t), 0.3) * 0.5 + osc_saw(f * 2.006, len(t)) * 0.5
    fc = 300 + 1400 * np.exp(-t / 0.09); return lpf(x, fc) * np.minimum(1, t / 0.004) * np.clip((d - t) / 0.02, 0, 1)
def dark_pad(fs, d, cut=850):
    t = T(d); x = np.zeros(len(t))
    for f in fs:
        for c in (-18, -11, -5, 0, 5, 11, 18): x += osc_saw(f * 2 ** (c / 1200), len(t), rng.random())
    x = lpf(lpf(x, cut), cut * 1.3) / (5 * len(fs)); env = np.minimum(1, t / 0.5) * np.clip((d - t) / 0.35, 0, 1)
    return x * env * (1 + 0.12 * np.sin(2 * np.pi * 0.35 * t))
def pluck(f, d=0.2, br=1.0):
    t = T(d + 0.15); x = osc_sq(f, len(t), 0.25) * 0.55 + osc_saw(f * 1.004, len(t)) * 0.45
    fc = 400 + 5200 * br * np.exp(-t / 0.05); return lpf(x, fc) * np.exp(-t / 0.13) * np.minimum(1, t / 0.002)
def bell(f, d=0.9):   # FM bell lead for the hook
    t = T(d); m = np.sin(2 * np.pi * f * 3.5 * t) * 2.2 * np.exp(-t / 0.25); return np.sin(2 * np.pi * f * t + m) * np.exp(-t / 0.45) * np.minimum(1, t / 0.003)
def metal_hit(p=1.0):
    t = T(1.6); x = np.zeros(len(t))
    for r, a, dc in ((1, 1, 0.9), (2.76, 0.6, 0.5), (5.40, 0.45, 0.3), (8.93, 0.3, 0.18)):
        x += a * np.sin(2 * np.pi * 410 * p * r * t + 1.5 * np.sin(2 * np.pi * 410 * p * r * 1.41 * t) * np.exp(-t / 0.05)) * np.exp(-t / dc)
    return 0.5 * x + svf_bp(nz(len(t)), 4200, 1) * np.exp(-t / 0.008) * 2
def sizzle(d=1.2):
    t = T(d); cr = (rng.random(len(t)) < 0.002) * rng.standard_normal(len(t)) * 6
    return (hpf(nz(len(t)), 3000) * 0.5 + svf_bp(cr, 2500, 1)) * np.exp(-t / (d / 2.5))
def crush(x, hold):   # sample-and-hold bit crush
    idx = (np.arange(len(x)) // hold) * hold; return np.round(x[idx] * 6) / 6
def glitch_riser(d):
    t = T(d); u = t / d; x = hpf(nz(len(t)), 600 + 4000 * u) * u ** 1.6
    gate = (np.sin(2 * np.pi * np.cumsum(4 + 28 * u ** 2) / SR) > 0).astype(float); x = x * (0.35 + 0.65 * gate)
    return crush(x, 6) * 0.9
def static_burst(d=0.25): x = crush(hpf(nz(int(d * SR)), 900), 9); return x * np.linspace(1, 0, len(x)) ** 1.5
def sub_drop(d=1.8): t = T(d); f = 30 + 55 * np.exp(-t / 0.15); return np.tanh(1.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.8))
def cannon():
    t = T(1.0); f = 46 + 120 * np.exp(-t / 0.03); x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.35)
    return np.tanh(2.6 * (x + lpf(nz(len(t)), 2400) * np.exp(-t / 0.07) * 1.6))
def boom(): t = T(1.2); return np.tanh(2.4 * (lpf(nz(len(t)), 380) * np.exp(-t / 0.35) * 2.6 + np.sin(2 * np.pi * 36 * t) * np.exp(-t / 0.5)))
def swish(d=0.4): t = T(d); u = t / d; f = 1200 + 6000 * u; return lpf(hpf(nz(len(t)), 0.6 * f), 1.5 * f) * np.sin(np.pi * u) ** 2 * 2.2
def blip(f, d=0.05): t = T(d); return osc_sq(f, len(t)) * 0.4 * np.clip((d - t) / 0.01, 0, 1)
def ui_tick(): t = T(0.06); return np.sin(2 * np.pi * (2400 + 1600 * np.exp(-t / 0.01)) * t) * np.exp(-t / 0.015)

# ---------- harmony ----------
PROG = [('F#2', ['F#3', 'A3', 'C#4']), ('B1', ['B2', 'D3', 'F#3']), ('G1', ['G2', 'B2', 'D3']), ('C#2', ['C#3', 'E#3', 'G#3'])]
def chord(t): return PROG[int(t / BAR + 1e-6) % 4]
drums = np.zeros(N); bass = np.zeros(N); pads = np.zeros(N); lead = np.zeros(N); fx = np.zeros(N); dry = np.zeros(N); kicks = []

def k_at(t, gain=1.0): add(drums, KICK, t, gain); kicks.append(t)
KICK, CLAP, RIM, HC, HO, SHK = kick(), clap(), rim(), hat(), hat(True), shaker()
S16 = BEAT / 4
def breakbeat(t0, t1, full=False):
    # one-bar pattern in 16ths: kicks 0, 6, 10 ; clap 4, 12 ; ghost rim 7, 15 ; hats every 16th with accents ; open hat on 14
    b = t0
    while b < t1 - 1e-6:
        for s in (0, 6, 10) + ((3,) if full else ()):
            if b + s * S16 < t1 - 1e-6: k_at(b + s * S16, 0.95)
        for s in (4, 12):
            if b + s * S16 < t1 - 1e-6: add(drums, CLAP, b + s * S16, 0.55)
        for s in (7, 15): add(drums, RIM, b + s * S16, 0.18)
        for s in range(16):
            if b + s * S16 < t1 - 1e-6: add(drums, HC if s != 14 else HO, b + s * S16, (0.16 if s % 4 == 2 else 0.07) * (1.2 if full else 1))
        if full:
            for s in (1, 5, 9, 13): add(drums, SHK, b + s * S16, 0.1)
        b += BAR
def halftime(t0, t1):
    b = t0
    while b < t1 - 1e-6:
        k_at(b, 0.8); add(drums, RIM, b + 2 * BEAT, 0.3); add(drums, HC, b + 3 * BEAT + S16 * 2, 0.08); b += BAR
def subline(t0, t1, drop=False):
    pat = [(0, 1.5), (1.5, 0.5), (2.5, 1.0), (3.5, 0.5)]   # beats: dotted, push, offbeat
    b = t0
    while b < t1 - 1e-6:
        r = hz(chord(b)[0])
        for st, ln in pat:
            tt = b + st * BEAT
            if tt < t1 - 1e-6:
                add(bass, sub(r, min(ln * BEAT * 0.95, t1 - tt)), tt, 0.62)
                if drop: add(bass, growl(r, ln * BEAT * 0.7), tt, 0.16)
        b += BAR
def padline(t0, t1, gain=0.5, cut=850):
    b = t0
    while b < t1 - 1e-6:
        nb = (np.floor(b / BAR + 1e-6) + 1) * BAR; d = min(nb - b, t1 - b); add(pads, dark_pad([hz(n) for n in chord(b)[1]], d + 0.2, cut), b, gain); b += d
def arp(t0, t1, gain=0.22, br=1.0, oct_up=1):
    order = [0, 2, 1, 2, 0, 3, 1, 3]   # chord tone index (3 = root an octave up)
    i = 0; t = t0
    while t < t1 - 1e-6:
        tones = chord(t)[1]; k = order[i % 8]; nm = tones[k % 3]; o = int(nm[-1]) + oct_up + (1 if k == 3 else 0)
        add(lead, pluck(hz(nm[:-1] + str(o)), S16 * 0.9, br), t, gain * (1.15 if i % 4 == 0 else 0.85)); t += S16; i += 1

# ---------- arrangement (all section times sit on the 14-frame beat grid) ----------
t_b2, t_l3, t_a4, t_sw, t_sv, t_du, t_pa, t_ha, t_sk, t_en = (g(x) for x in tuple(SY['sections']))
# intro: pad swell + glitch riser + static window-open motif + countdown blips
padline(0, t_b2, 0.45, 600); add(fx, static_burst(0.5), 0.0, 0.5); add(fx, glitch_riser(t_b2), 0, 0.28)
for i, t in enumerate(SY['count']): add(dry, blip(1480 if i < 2 else 2220, 0.08), t, 0.45)
# blade (slow motion): half-time, sub drone, swing swish, cut = metal hit + sizzle, then glitch riser into the laser
halftime(t_b2, t_l3); padline(t_b2, t_l3, 0.4, 500); add(bass, sub(hz('F#1'), t_l3 - t_b2) * 0.7, t_b2, 0.55)
add(dry, sub_drop(), t_b2, 0.7); add(fx, static_burst(0.2), t_b2, 0.35)
for t in SY['swish']: add(fx, swish(0.7), t, 0.6)
for t in SY['cut']: add(dry, metal_hit(1.0), t, 0.75); add(fx, sizzle(1.6), t, 0.45); add(dry, sub_drop(1.2), t, 0.5)
add(fx, glitch_riser(t_l3 - SY['cut'][0] - 0.3), SY['cut'][0] + 0.3, 0.35)
# laser + aim: breakbeat in, sub line, arp; lock-on blips; cannon on the beat; silence on the freeze
breakbeat(t_l3, t_sw); subline(t_l3, t_sw); padline(t_l3, t_sw, 0.32, 1100); arp(t_l3, t_sw, 0.16, 0.7)
for i, t in enumerate(SY['lock']): add(dry, blip(1975, 0.05) if i < len(SY['lock']) - 1 else blip(2637, 0.28), t, 0.4)
for t in SY['cannon']: add(dry, cannon(), t, 0.9)
for t in SY['impact']: add(dry, boom(), t, 0.8); add(dry, metal_hit(0.7), t, 0.3)
# swing + sever: filtered build, tear + metal hit, riser into the drop
padline(t_sw, t_du, 0.42, 1500); halftime(t_sw, t_sv)
for t in SY['whoosh']: add(fx, swish(0.6), t, 0.55)
b = t_sv
while b < t_du - 1e-6: k_at(b, 0.85); add(drums, CLAP, b + BEAT, 0.25 + 0.4 * (b - t_sv) / (t_du - t_sv)); b += 2 * BEAT
for i in range(12): add(drums, RIM, t_du - BEAT * 1.5 + i * BEAT * 1.5 / 12, 0.15 + 0.3 * i / 12)
for t in SY.get('clack', []): add(dry, metal_hit(1.9), t, 0.6); add(dry, rim(), t + 0.07, 0.9)
for t in SY['tear']: add(dry, metal_hit(1.3), t, 0.7); add(fx, sizzle(0.9), t, 0.5); add(dry, boom(), t, 0.4)
for t in SY['slash']: add(fx, swish(0.5), t, 0.5)
add(fx, glitch_riser(t_du - t_sv), t_sv, 0.4)
# drop: duel + parry — full breakbeat, sub + growl, arp + FM bell hook
FZ = SY['freeze']
add(dry, sub_drop(2.0), t_du, 0.9); add(fx, static_burst(0.35), t_du, 0.4)
breakbeat(t_du, FZ, full=True); subline(t_du, FZ, drop=True); padline(t_du, FZ, 0.38, 1800); arp(t_du, FZ, 0.14, 1.0)
HOOK = [('C#5', 0, 2), ('F#5', 2, 1), ('A5', 3, 1), ('G#5', 4, 2), ('E#5', 6, 2), ('D5', 8, 1), ('F#5', 9, 1), ('B5', 10, 2), ('A5', 12, 1), ('G#5', 13, 1), ('E#5', 14, 2)]
for rep in range(4):
    for nm, st, ln in HOOK:
        t = t_du + rep * 2 * BAR + st * BEAT / 2
        if t < FZ - 0.05: add(lead, bell(hz(nm), ln * BEAT / 2 + 0.4), t, 0.2)
for t in SY['cannon2']: add(dry, cannon(), t, 0.85)
for t in SY['impact2']: add(dry, boom(), t, 0.7)
for t in SY['hop']: add(fx, swish(0.35), t, 0.45)
for t in SY['block']: add(dry, metal_hit(1.6), t, 0.7)
for t in SY['parry']: add(dry, metal_hit(0.85), t, 0.95); add(dry, metal_hit(1.21), t + 0.02, 0.5); add(dry, sub_drop(0.9), t, 0.5)
for t in SY['flash']: add(fx, static_burst(0.18), t, 0.45)
for t in SY['slash2']: add(fx, swish(0.45), t, 0.5)
add(dry, metal_hit(0.6), FZ, 0.6)
# hangar: groove returns lighter, UI tick per repaint
breakbeat(t_ha, t_sk); subline(t_ha, t_sk); arp(t_ha, t_sk, 0.13, 0.6)
add(fx, static_burst(0.3), t_ha - 0.05, 0.35)
for t in SY['clicks']: add(dry, ui_tick(), t, 0.55)
# three skins: three rising stabs (F#m -> A -> C#)
for i, (t, ch) in enumerate(zip(SY['stabs'], [['F#3', 'A3', 'C#4', 'F#4'], ['A3', 'C#4', 'E4', 'A4'], ['C#4', 'E#4', 'G#4', 'C#5']])):
    add(pads, dark_pad([hz(n) for n in ch], BEAT * (1 if i < 2 else 2), 3200), t, 0.9); add(lead, bell(hz(ch[-1]) * 2, 0.6), t, 0.15); k_at(t, 0.9)
add(fx, glitch_riser(t_en - SY['stabs'][-1]), SY['stabs'][-1], 0.35)
# end: final hit, long dark pad, glitch static fade
add(dry, sub_drop(3.0), t_en, 1.0); add(dry, metal_hit(0.5), t_en, 0.6); add(fx, static_burst(0.4), t_en, 0.4)
add(pads, dark_pad([hz(n) for n in ['F#2', 'C#3', 'F#3', 'A3', 'C#4']], TOTAL - t_en, 1400), t_en, 0.75)
arp(t_en + BAR, t_en + 3 * BAR, 0.07, 0.5)
st = crush(hpf(nz(int(1.6 * SR)), 1500), 7) * np.linspace(0, 1, int(1.6 * SR)) ** 2; add(fx, st, TOTAL - 1.6, 0.3)

# ---------- automation + mix ----------
gate = np.ones(N)
for a, b2 in SY['mute']:
    i, j = int(a * SR), int(b2 * SR); gate[i:j] = 0; gate[max(0, i - 300):i] *= np.linspace(1, 0, min(300, i)); gate[j:j + 2000] *= np.linspace(0, 1, 2000)
i, j = int(FZ * SR), int(t_ha * SR); gate[i:j] = 0; gate[i - 300:i] *= np.linspace(1, 0, 300)
fc = np.full(N, 15000.0)
i, j = int(t_sw * SR), int(t_du * SR); fc[i:j] = 500 + 14500 * np.linspace(0, 1, j - i) ** 2.2   # build opens the filter
i, j = int(t_b2 * SR), int(t_l3 * SR); fc[i:j] = 700                                              # slow-mo: muffled
duck = np.ones(N)
for tk in kicks:
    i = int(tk * SR); n = int(0.22 * SR); j = min(N, i + n); duck[i:j] = np.minimum(duck[i:j], 1 - 0.55 * np.exp(-np.arange(j - i) / SR / 0.07))
music = lpf(drums * 0.9 + (bass + pads) * duck + lead * (0.55 + 0.45 * duck), fc) * gate
def verb(x, d=2.8, mix=0.5):
    tt = T(d); ir = nz(len(tt)) * np.exp(-tt / (d / 6)); ir = lpf(ir, 4500); ir /= np.sqrt((ir ** 2).sum()); return x + mix * fftconvolve(x, ir)[:len(x)]
mix = music + verb(fx + 0.55 * dry, 2.8, 0.5) * 0.85 + verb(lead * gate, 1.6, 0.25) * 0.25
mix = np.tanh(1.05 * mix / (np.percentile(np.abs(mix), 99.6) + 1e-9))
dl = int(0.014 * SR); side = np.zeros(N); side[dl:] = ((pads + lead) * 0.14 * gate)[:-dl]
L, R = mix + side, mix - side
end = int(TOTAL * SR); fd = int(1.2 * SR)
for c in (L, R): c[end - fd:end] *= np.linspace(1, 0, fd) ** 1.4; c[end:] = 0
pk = max(abs(L).max(), abs(R).max()); L, R = L / pk * 0.89, R / pk * 0.89
with wave.open('music3.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.stack([L[:end], R[:end]], 1) * 32767).astype('<i2').tobytes())
print('ok')
