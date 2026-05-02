import re
import numpy as np
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from scipy.ndimage import gaussian_filter1d
import librosa

# ── 依賴套件 ──────────────────────────────────────────
# pip install matplotlib numpy librosa scipy

# ── 參數（可調） ──────────────────────────────────────
FPS = 30
MARKERS_PER_ROW = 6

# marker.txt 全域共用（來自 DAW 匯出）
INPUT_MARKERS = 'marker.txt'

# ── 聲部設定 ──────────────────────────────────────────
# 每個聲部指定：
#   'label'       : 聲部名稱（用於輸出檔名）
#   'audio_file'  : 該聲部的分軌 wav 路徑
#   'show_markers': 要顯示豎線的 marker 編號清單（None = 全部顯示）
#
# 範例：R 和 T 在 marker 2 有事件，K 和 P 不顯示 marker 2
#   {'label': 'K', 'audio_file': 'key.wav',     'show_markers': None},
#   {'label': 'P', 'audio_file': 'pad.wav',      'show_markers': None},
#   {'label': 'R', 'audio_file': 'rhythm.wav',   'show_markers': [1, 2, 5]},
#   {'label': 'T', 'audio_file': 'texture.wav',  'show_markers': [2, 3]},

PARTS = [
    {
        'label': 'K',
        'audio_file': 'key.wav',
        'show_markers': None
    },
    {
        'label': 'P',
        'audio_file': 'pad.wav',
        'show_markers': None
    },
    {
        'label': 'R',
        'audio_file': 'rhythm.wav',
        'show_markers': None
    },
    {
        'label': 'T',
        'audio_file': 'texture.wav',
        'show_markers': None
    },
]

OUTPUT_PREFIX = 'timeline_v6'
EXPORT_PNG = True
EXPORT_SVG = False
EXPORT_PDF = False
PNG_DPI = 300

# A4 橫向（英吋）
PAGE_W = 11.69
ROW_H = 2.0
PAD_LEFT = 0.6
PAD_RIGHT = 0.6
PAD_TOP = 0.5
PAD_BOTTOM = 0.5

# Amplitude 曲線參數
RMS_FRAME_LENGTH = 2048
RMS_HOP_LENGTH = 512
SMOOTH_SIGMA = 5
AMP_HEIGHT = 0.5
AMP_ALPHA = 0.85

# Spectral Centroid 顏色映射（方向 C：HSL 色相）
# 低頻（centroid_norm=0）→ HUE_LOW、高頻（centroid_norm=1）→ HUE_HIGH
# 色相單位 0.0–1.0（對應 0°–360°）
# 預設：低頻=暖橙紅（0.04 ≈ 14°）、高頻=冷藍紫（0.67 ≈ 240°）
HUE_LOW = 0.04  # 低頻色相
HUE_HIGH = 0.67  # 高頻色相
HSL_SATURATION = 0.65  # 彩度（0=灰階，1=全彩）
HSL_LIGHTNESS = 0.50  # 明度（固定，不隨振幅變化）

# RMS 靜音門檻：低於此值的區段顏色設為透明，避免靜音段顏色跳動
RMS_SILENCE_THRESHOLD = 0.02  # 相對正規化 RMS（0–1）

CENTROID_HZ_MIN = None  # 顏色下界（Hz）；None = 自動用該聲部全曲 min
CENTROID_HZ_MAX = None  # 顏色上界（Hz）；None = 自動用該聲部全曲 max

# Monochrome fallback（保留備用，目前不啟用）
# USE_MONOCHROME = True
# CENTROID_CMAP = 'gray_r'
# ─────────────────────────────────────────────────────


def hsl_color_array(centroid_norm, rms_norm):
    """
    centroid_norm（0-1）-> HSL 色相插值 -> RGBA
    色相：HUE_LOW（低頻）到 HUE_HIGH（高頻）
    靜音區段（rms_norm < RMS_SILENCE_THRESHOLD）alpha=0
    """
    import colorsys
    n = len(centroid_norm)
    colors = np.zeros((n, 4))
    for i in range(n):
        hue = HUE_LOW + centroid_norm[i] * (HUE_HIGH - HUE_LOW)
        r, g, b = colorsys.hls_to_rgb(hue, HSL_LIGHTNESS, HSL_SATURATION)
        alpha = AMP_ALPHA if rms_norm[i] >= RMS_SILENCE_THRESHOLD else 0.0
        colors[i] = (r, g, b, alpha)
    return colors


def parse_time(time_str):
    match = re.match(r'(\d+):(\d+):(\d+)\.(\d+)', time_str)
    h, m, s, frames = (int(match.group(1)), int(match.group(2)),
                       int(match.group(3)), int(match.group(4)))
    return h * 3600 + m * 60 + s + frames / FPS


def parse_markers(filepath):
    markers = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = re.match(r'(\d+)\s*-\s*(\d+:\d+:\d+\.\d+)', line)
            if match:
                num = int(match.group(1))
                secs = parse_time(match.group(2))
                markers.append((num, secs, match.group(2)))
    return markers


def load_audio_features(audio_file):
    """
    載入分軌 wav，回傳音訊特徵。
    回傳：(rms_times, rms_norm, centroid_norm, audio_duration, c_min, c_max, hz_min, hz_max)
    """
    y, sr = librosa.load(audio_file, sr=None, mono=True)
    audio_duration = librosa.get_duration(y=y, sr=sr)

    rms = librosa.feature.rms(y=y,
                              frame_length=RMS_FRAME_LENGTH,
                              hop_length=RMS_HOP_LENGTH)[0]
    rms_times = librosa.frames_to_time(np.arange(len(rms)),
                                       sr=sr,
                                       hop_length=RMS_HOP_LENGTH)
    rms_smooth = gaussian_filter1d(rms, sigma=SMOOTH_SIGMA)
    rms_norm = rms_smooth / (rms_smooth.max() + 1e-9)

    centroid = librosa.feature.spectral_centroid(y=y,
                                                 sr=sr,
                                                 hop_length=RMS_HOP_LENGTH)[0]
    centroid_smooth = gaussian_filter1d(centroid, sigma=SMOOTH_SIGMA)
    c_min = centroid_smooth.min()
    c_max = centroid_smooth.max()
    hz_min = CENTROID_HZ_MIN if CENTROID_HZ_MIN is not None else c_min
    hz_max = CENTROID_HZ_MAX if CENTROID_HZ_MAX is not None else c_max
    centroid_norm = np.clip(
        (centroid_smooth - hz_min) / (hz_max - hz_min + 1e-9), 0, 1)

    n = min(len(rms_times), len(centroid_norm))
    return (rms_times[:n], rms_norm[:n], centroid_norm[:n], audio_duration,
            c_min, c_max, hz_min, hz_max)


def draw_row(ax, t_start, t_end, row_markers, show_markers_set, rms_times,
             rms_norm, centroid_norm):
    """
    在給定的 ax 上繪製單行時間軸。

    t_start, t_end     : 該行的時間範圍（秒）
    row_markers        : [(num, secs, time_str), ...]
    show_markers_set   : set of int or None；None = 全部顯示
    rms_times / rms_norm / centroid_norm : 該聲部的音訊特徵
    """
    draw_w = PAGE_W - PAD_LEFT - PAD_RIGHT
    duration = t_end - t_start
    timeline_y = ROW_H / 2
    x_start = PAD_LEFT
    x_end = x_start + draw_w

    ax.set_xlim(0, PAGE_W)
    ax.set_ylim(0, ROW_H)
    ax.set_aspect('equal')
    ax.axis('off')

    # ── Amplitude + Spectral Centroid 曲線 ────────────
    if duration > 0:
        mask = (rms_times >= t_start) & (rms_times <= t_end)
        seg_times = rms_times[mask]
        seg_rms = rms_norm[mask]
        seg_centroid = centroid_norm[mask]

        if len(seg_times) > 1:
            seg_x = x_start + (seg_times - t_start) / duration * draw_w
            seg_y = timeline_y + seg_rms * AMP_HEIGHT

            # 振幅輪廓多邊形作為 clip path
            poly_x = np.concatenate([[seg_x[0]], seg_x, [seg_x[-1]]])
            poly_y = np.concatenate([[timeline_y], seg_y, [timeline_y]])
            verts = list(zip(poly_x, poly_y)) + [(poly_x[0], poly_y[0])]
            codes = ([Path.MOVETO] + [Path.LINETO] * (len(verts) - 2) +
                     [Path.CLOSEPOLY])
            clip_patch = PathPatch(Path(verts, codes),
                                   transform=ax.transData,
                                   visible=False)
            ax.add_patch(clip_patch)

            # imshow 色帶（HSL 色相方案），用 clip path 裁切
            # alpha 已內嵌於 color_array（靜音區段 alpha=0），imshow alpha 設 1.0
            color_array = hsl_color_array(seg_centroid, seg_rms)
            color_strip = color_array[np.newaxis, :, :]
            im = ax.imshow(color_strip,
                           extent=[
                               seg_x[0], seg_x[-1], timeline_y,
                               timeline_y + AMP_HEIGHT
                           ],
                           aspect='auto',
                           alpha=1.0,
                           zorder=1,
                           interpolation='bilinear')
            im.set_clip_path(clip_patch)

            # 輪廓線
            points = np.array([seg_x, seg_y]).T.reshape(-1, 1, 2)
            segments_lc = np.concatenate([points[:-1], points[1:]], axis=1)
            lc = LineCollection(segments_lc,
                                colors='grey',
                                linewidth=0.8,
                                alpha=min(AMP_ALPHA + 0.1, 1.0),
                                zorder=2)
            ax.add_collection(lc)

    # ── 主軸線 ────────────────────────────────────────
    ax.plot([x_start, x_end], [timeline_y, timeline_y],
            color='black',
            linewidth=1.2,
            zorder=4)

    # ── Markers ───────────────────────────────────────
    # 估算 label 水平佔用寬度（data 單位 ≈ 英吋）
    # "00:00:00.00" = 11 字元，5.5pt monospace ≈ 0.55 英吋
    LABEL_W = 0.55
    tick_h = 0.12
    Y_NEAR = timeline_y - tick_h - 0.04   # 第一層（緊靠軸線下）
    Y_FAR  = timeline_y - tick_h - 0.18   # 第二層（往下錯開）

    # ① 篩選 & 計算 x 位置
    visible = []
    for num, secs, time_str in row_markers:
        if show_markers_set is not None and num not in show_markers_set:
            continue
        x = (x_start + (secs - t_start) / duration * draw_w
             if duration > 0 else x_start)
        visible.append((num, x, time_str))

    # ② 按 x 排序後，貪婪分配 y 層（只在碰到才錯開）
    visible_sorted = sorted(visible, key=lambda m: m[1])
    level_last_x = [None, None]   # 兩層各自最後一個 label 的右緣 x
    y_level = {}
    for num, x, time_str in visible_sorted:
        near_ok = (level_last_x[0] is None or
                   (x - level_last_x[0]) >= LABEL_W)
        far_ok  = (level_last_x[1] is None or
                   (x - level_last_x[1]) >= LABEL_W)
        if near_ok:
            lv = 0
        elif far_ok:
            lv = 1
        else:
            lv = 0   # 極度擁擠時退回第一層（至少不比現況更差）
        y_level[num] = lv
        level_last_x[lv] = x

    # ③ 繪製刻度線與 label
    for num, x, time_str in visible:
        ax.plot([x, x], [timeline_y - tick_h, timeline_y + tick_h],
                color='black',
                linewidth=0.8,
                zorder=5)
        label_y = Y_FAR if y_level[num] == 1 else Y_NEAR
        ax.text(x,
                label_y,
                time_str,
                ha='center',
                va='top',
                fontsize=5.5,
                fontfamily='monospace',
                color='#555555')


# ── 共用 marker 資料 & 分行 ───────────────────────────
markers = parse_markers(INPUT_MARKERS)
total_markers = len(markers)

rows = [
    markers[i:i + MARKERS_PER_ROW]
    for i in range(0, total_markers, MARKERS_PER_ROW)
]
num_rows = len(rows)

# ── 各聲部輸出 ────────────────────────────────────────
for part in PARTS:
    label = part['label']
    audio_file = part['audio_file']
    show_markers = part.get('show_markers', None)
    show_markers_set = set(show_markers) if show_markers is not None else None

    print(f"\n載入聲部：{label}  ({audio_file})")
    (rms_times, rms_norm, centroid_norm, audio_duration, c_min, c_max, hz_min,
     hz_max) = load_audio_features(audio_file)

    # 每行的 t_start / t_end（行與行之間無縫銜接）
    row_ranges = []
    for i, row in enumerate(rows):
        t_start = row[0][1]
        t_end = rows[i + 1][0][1] if i + 1 < num_rows else audio_duration
        row_ranges.append((t_start, t_end))

    print(f"  {total_markers} markers, {num_rows} rows")
    print(f"  Spectral centroid (全曲): {c_min:.1f} – {c_max:.1f} Hz")
    print(f"  Spectral centroid (上色): {hz_min:.1f} – {hz_max:.1f} Hz")

    for row_idx, (row, (t_start, t_end)) in enumerate(zip(rows, row_ranges)):
        fig, ax = plt.subplots(figsize=(PAGE_W, ROW_H))
        draw_row(ax, t_start, t_end, row, show_markers_set, rms_times,
                 rms_norm, centroid_norm)

        base = f'{OUTPUT_PREFIX}_{label}_row_{row_idx + 1}'

        if EXPORT_PNG:
            path = f'{base}.png'
            plt.savefig(path,
                        format='png',
                        dpi=PNG_DPI,
                        bbox_inches='tight',
                        pad_inches=0)
            print(f"  Saved: {path}")

        if EXPORT_SVG:
            path = f'{base}.svg'
            plt.savefig(path, format='svg', bbox_inches='tight', pad_inches=0)
            print(f"  Saved: {path}")

        if EXPORT_PDF:
            path = f'{base}.pdf'
            plt.savefig(path, format='pdf', bbox_inches='tight', pad_inches=0)
            print(f"  Saved: {path}")

        plt.close(fig)

print(f"\nDone. {len(PARTS)} parts x {num_rows} rows.")
