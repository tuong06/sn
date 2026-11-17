"""Tổng hợp bản "Happy Birthday to You" (public domain) phối kiểu hộp nhạc, nhịp waltz.
Xuất WAV stereo 44.1 kHz; mã hoá MP3 làm bằng ffmpeg bên ngoài."""
import sys
import wave
import numpy as np

SR = 44100
BPM = 88.0
BEAT = 60.0 / BPM          # một phách đen
BAR = 3 * BEAT             # nhịp 3/4
rng = np.random.default_rng(7)

KEY = 5  # dịch giọng: Đô trưởng -> Fa trưởng


def midi(name):
    names = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    n, acc, octv = name[0], 0, name[-1]
    if '#' in name:
        acc = 1
    if 'b' in name[1:-1]:
        acc = -1
    return 12 * (int(octv) + 1) + names[n] + acc + KEY


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# Giai điệu: (tên nốt, số phách). Có nhịp lấy đà 1 phách ở đầu.
PICKUP = [('G4', .75), ('G4', .25)]
VERSE = [
    ('A4', 1), ('G4', 1), ('C5', 1),
    ('B4', 2), ('G4', .75), ('G4', .25),
    ('A4', 1), ('G4', 1), ('D5', 1),
    ('C5', 2), ('G4', .75), ('G4', .25),
    ('G5', 1), ('E5', 1), ('C5', 1),
    ('B4', 1), ('A4', 1), ('F5', .75), ('F5', .25),
    ('E5', 1), ('C5', 1), ('D5', 1),
    ('C5', 3),
]
# Hợp âm theo ô nhịp (8 ô của một lượt), mỗi ô: list (hợp âm, số phách)
CHORDS = [
    [('C', 3)], [('G', 3)], [('G7', 3)], [('C', 3)],
    [('C7', 3)], [('F', 3)], [('C', 2), ('G7', 1)], [('C', 3)],
]
CH = {
    'C': ['C3', 'E3', 'G3'], 'G': ['G2', 'B2', 'D3'], 'G7': ['G2', 'B2', 'F3'],
    'C7': ['C3', 'E3', 'Bb3'], 'F': ['F2', 'A2', 'C3'],
}
ROOT = {'C': 'C3', 'G': 'G2', 'G7': 'G2', 'C7': 'C3', 'F': 'F2'}
FIFTH = {'C': 'G2', 'G': 'D2', 'G7': 'D2', 'C7': 'G2', 'F': 'C2'}


def env_exp(n, attack, decay):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-t / decay)


def musicbox(f, dur, vel):
    """Âm sắc hộp nhạc / celesta: hoạ âm hơi lệch, tắt nhanh ở tần số cao."""
    n = int(SR * min(dur + 2.2, 4.0))
    t = np.arange(n) / SR
    out = np.zeros(n)
    parts = [(1.0, 1.0, 1.6), (2.0, .32, .7), (3.01, .10, .35), (4.17, .16, .18), (6.8, .05, .08)]
    for ratio, amp, dec in parts:
        fr = f * ratio
        if fr > SR / 2.2:
            continue
        out += amp * np.sin(2 * np.pi * fr * t + rng.uniform(0, 6.28)) * env_exp(n, .002, dec * (440 / f) ** .25)
    # tiếng gõ nhẹ đầu nốt
    click = rng.normal(0, 1, int(SR * .004)) * np.linspace(1, 0, int(SR * .004)) * .05
    out[:click.size] += click
    return out * vel


def ep(f, dur, vel):
    """Đàn phím điện mềm cho phần đệm waltz."""
    n = int(SR * (dur + 1.2))
    t = np.arange(n) / SR
    out = (np.sin(2 * np.pi * f * t) + .25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / .3)
           + .08 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t / .15))
    e = env_exp(n, .006, .9)
    rel = int(SR * dur)
    if rel < n:
        e[rel:] *= np.exp(-np.arange(n - rel) / SR / .18)
    return out * e * vel


def bass(f, dur, vel):
    n = int(SR * (dur + .8))
    t = np.arange(n) / SR
    out = np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / .25)
    e = env_exp(n, .01, 1.4)
    rel = int(SR * dur)
    if rel < n:
        e[rel:] *= np.exp(-np.arange(n - rel) / SR / .12)
    return out * e * vel


def pad(freqs, dur, vel):
    """Nền dây êm: nhiều sine lệch nhịp, vào chậm ra chậm."""
    n = int(SR * (dur + 1.5))
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12)
            out += np.sin(2 * np.pi * ff * t + rng.uniform(0, 6.28)) + .2 * np.sin(2 * np.pi * 2 * ff * t)
    a = np.clip(t / .9, 0, 1)
    r = np.ones(n)
    k = int(SR * dur)
    r[k:] = np.exp(-np.arange(n - k) / SR / .5)
    lfo = 1 + .06 * np.sin(2 * np.pi * .35 * t)
    return out * a * r * lfo * vel / (len(freqs) * 3)


class Track:
    def __init__(self, seconds):
        self.L = np.zeros(int(SR * seconds))
        self.R = np.zeros(int(SR * seconds))

    def add(self, sig, start, pan=0.0):
        i = int(start * SR)
        if i >= self.L.size:
            return
        j = min(self.L.size, i + sig.size)
        s = sig[: j - i]
        gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.L[i:j] += s * gl
        self.R[i:j] += s * gr


def human(x=.007):
    return rng.uniform(-x, x)


INTRO_BARS = 2
VERSES = 3
TOTAL_BARS = INTRO_BARS + VERSES * 8 + 3
seconds = TOTAL_BARS * BAR + 4
dry = Track(seconds)

t0 = INTRO_BARS * BAR  # ô nhịp 1 của lượt đầu bắt đầu ở đây

# Mở đầu: rải hợp âm Fa trưởng lên cao, rồi nhịp lấy đà
intro = ['C4', 'E4', 'G4', 'C5', 'E5', 'G5', 'C6', 'G5', 'E5', 'C5', 'G4', 'E4']
for k, nm in enumerate(intro):
    dry.add(musicbox(hz(midi(nm)), .5, .26 - k * .008), k * (2 * BAR / 12) + human(), pan=-.3 + k * .05)
dry.add(pad([hz(midi(x)) for x in ['C3', 'G3', 'E4']], 2 * BAR, .5), 0)

for v in range(VERSES):
    start = t0 + v * 8 * BAR
    # nhịp lấy đà nằm ở phách 3 của ô trước
    tt = start - BEAT
    mel = PICKUP + VERSE
    vel_base = [.62, .66, .58][v]
    for nm, beats in mel:
        f = hz(midi(nm) + (12 if v == 1 else 0))
        dur = beats * BEAT
        vel = vel_base * (1.08 if beats >= 1 else .9) * rng.uniform(.92, 1.05)
        dry.add(musicbox(f, dur, vel), tt + human(), pan=.12)
        if v == 1:
            # lượt hai: giai điệu ở quãng tám cao, thêm bè thấp một quãng tám bằng đàn phím
            dry.add(ep(hz(midi(nm)), dur * .95, .16), tt + human(), pan=-.2)
        if v == 2 and beats >= 1:
            dry.add(musicbox(f / 2, dur, vel * .35), tt + human(), pan=-.15)
        tt += dur

    # phần đệm waltz: bass phách 1, hợp âm phách 2 và 3
    for b, bar in enumerate(CHORDS):
        bt = start + b * BAR
        ph = 0
        for chord, beats in bar:
            for k in range(beats):
                beat_no = ph + k
                at = bt + beat_no * BEAT + human(.005)
                if beat_no == 0:
                    dry.add(bass(hz(midi(ROOT[chord])), BEAT * .95, .30), at, pan=0)
                elif k == 0 and beat_no == 2:
                    dry.add(bass(hz(midi(ROOT[chord])), BEAT * .9, .24), at, pan=0)
                else:
                    for nm in CH[chord]:
                        dry.add(ep(hz(midi(nm) + 12), BEAT * .55, .085 + (.02 if v == 1 else 0)), at, pan=-.25)
            ph += beats
        if v >= 1:
            ch = bar[0][0]
            dry.add(pad([hz(midi(x) + 12) for x in CH[ch]], BAR * .98, .32 if v == 1 else .42), bt, pan=.0)
    if v == 2:
        # lượt cuối: chuông đối điểm nhẹ ở phách 1 mỗi ô
        for b, bar in enumerate(CHORDS):
            top = CH[bar[0][0]][-1]
            dry.add(musicbox(hz(midi(top) + 24), BEAT, .12), start + b * BAR + BEAT * 1.5 + human(), pan=-.45)

# Kết: hợp âm chủ ngân dài và một nốt chuông cuối
end = t0 + VERSES * 8 * BAR
dry.add(pad([hz(midi(x) + 12) for x in ['C3', 'E3', 'G3', 'C4']], 2.5 * BAR, .45), end)
dry.add(bass(hz(midi('C3')), 2 * BAR, .28), end)
for k, nm in enumerate(['C5', 'E5', 'G5', 'C6']):
    dry.add(musicbox(hz(midi(nm)), 2.0, .3), end + k * .09, pan=-.2 + k * .13)

# Hồi âm: đáp ứng xung là nhiễu tắt dần, khác nhau cho trái và phải
def reverb_ir(seed, secs=2.6):
    r = np.random.default_rng(seed)
    n = int(SR * secs)
    t = np.arange(n) / SR
    ir = r.normal(0, 1, n) * np.exp(-t / .55)
    # làm tối dần các tần số cao bằng lọc trung bình trượt
    k = 6
    ir = np.convolve(ir, np.ones(k) / k, mode='same')
    ir[: int(SR * .012)] = 0  # pre-delay
    return ir / np.sqrt(np.sum(ir ** 2))


def fftconv(x, h):
    n = x.size + h.size - 1
    N = 1 << (n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(h, N), N)[: x.size]
    return y


wetL = fftconv(dry.L, reverb_ir(1))
wetR = fftconv(dry.R, reverb_ir(2))
L = dry.L * .82 + wetL * .30
R = dry.R * .82 + wetR * .30

# lấy mẫu cuối cùng có âm, cắt đuôi im lặng
mix = np.stack([L, R], 1)
level = np.abs(mix).max(1)
last = np.nonzero(level > level.max() * 1e-3)[0][-1]
mix = mix[: last + int(SR * .2)]
# fade in rất ngắn, fade out 1.5 s
fi = int(SR * .01)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(SR * 1.5)
mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 2

# nén mềm rồi chuẩn hoá đỉnh về -1 dBFS
peak = np.abs(mix).max()
mix = mix / peak
mix = np.tanh(mix * 1.4) / np.tanh(1.4)
mix *= 10 ** (-1 / 20) / np.abs(mix).max()

pcm = (mix * 32767).astype('<i2')
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f'duration {mix.shape[0] / SR:.1f}s, bars {TOTAL_BARS}, tempo {BPM}')
