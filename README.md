# Timeline v6 Color — 音軌時間軸視覺化工具

> 🌐 語言：**繁體中文** | [English](README_en.md) | [日本語](README_ja.md)

> [!NOTE]
> 本說明文件由 AI 輔助撰寫（Claude Sonnet 4.6），內容以腳本原始碼為依據，僅供參考。使用前請自行核對程式碼中的實際參數與邏輯。

將 DAW 匯出的 marker 檔與分軌 WAV 結合，自動產生彩色振幅時間軸圖像，適合用於樂曲分析、演出譜面製作或縮混參考。

---

## 功能概覽

- 解析 DAW（如 Reaper、Logic Pro、Cubase）匯出的 `marker.txt`
- 對每個聲部（Part）讀取對應的分軌 WAV 檔
- 計算 **RMS 振幅**（音量輪廓）與 **Spectral Centroid**（頻譜重心，代表音色亮暗）
- 以 **HSL 色相**將頻譜重心映射為顏色（低頻 = 暖橙紅、高頻 = 冷藍紫）
- 自動將全曲分成多行（每行最多 N 個 marker），輸出 A4 橫向排版的 PNG / SVG / PDF

---

## 檔案結構

```
v6_color/
├── timeline_v6_color.py   # 主程式
├── marker.txt             # DAW 匯出的 marker 清單
├── key.wav                # 聲部 WAV（需自行準備）
├── pad.wav
├── rhythm.wav
├── texture.wav
└── README.md
```

---

## 環境需求

| 套件 | 用途 |
|------|------|
| Python 3.9+ | 直譯器 |
| `matplotlib` | 繪圖輸出 |
| `numpy` | 數值計算 |
| `librosa` | 音訊特徵分析（RMS、Spectral Centroid） |
| `scipy` | 高斯平滑濾波 |

### 一鍵安裝

```bash
pip install matplotlib numpy librosa scipy
```

---

## 快速入門（5 分鐘）

### 步驟 1 — 準備 `marker.txt`

格式為每行一個 marker，編號與時間碼以 ` - ` 分隔，時間碼格式為 `HH:MM:SS.FF`（FF = 幀號）：

```
1 - 00:00:00.00
2 - 00:00:33.07
3 - 00:00:48.12
...
```

> **注意**：時間碼最後的數字是**幀數**，不是毫秒。預設 FPS = 30，可在腳本頂部的 `FPS` 變數修改。

### 步驟 2 — 準備分軌 WAV

將各聲部的 WAV 檔放在與腳本相同的目錄下（或填入完整路徑）。

### 步驟 3 — 設定腳本參數

打開 `timeline_v6_color.py`，修改 `PARTS` 清單：

```python
PARTS = [
    {
        'label': 'K',           # 聲部名稱（用於輸出檔名）
        'audio_file': 'key.wav',
        'show_markers': None    # None = 顯示所有 marker；或填 [1, 3, 5] 只顯示指定編號
    },
    {
        'label': 'P',
        'audio_file': 'pad.wav',
        'show_markers': None
    },
    # 繼續新增更多聲部...
]
```

### 步驟 4 — 執行

```bash
python timeline_v6_color.py
```

執行後會在同一目錄下產生類似以下的檔案：

```
timeline_v6_K_row_1.png
timeline_v6_K_row_2.png
timeline_v6_P_row_1.png
...
```

---

## 主要參數說明

### 全域參數

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `FPS` | `30` | marker 時間碼的幀率（須與 DAW 設定一致） |
| `MARKERS_PER_ROW` | `6` | 每行最多顯示幾個 marker |
| `INPUT_MARKERS` | `'marker.txt'` | marker 檔路徑 |
| `OUTPUT_PREFIX` | `'timeline_v6'` | 輸出檔名前綴 |

### 匯出格式

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `EXPORT_PNG` | `True` | 匯出 PNG |
| `EXPORT_SVG` | `False` | 匯出 SVG（向量圖） |
| `EXPORT_PDF` | `False` | 匯出 PDF |
| `PNG_DPI` | `300` | PNG 解析度（dpi） |

### 版面尺寸

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `PAGE_W` | `11.69` 英吋 | 頁面寬度（A4 橫向） |
| `ROW_H` | `2.0` 英吋 | 每行高度 |
| `PAD_LEFT / PAD_RIGHT` | `0.6` 英吋 | 左右留白 |
| `PAD_TOP / PAD_BOTTOM` | `0.5` 英吋 | 上下留白 |

### 振幅曲線

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `RMS_FRAME_LENGTH` | `2048` | RMS 分析視窗大小（samples） |
| `RMS_HOP_LENGTH` | `512` | RMS 分析跳躍步長（samples） |
| `SMOOTH_SIGMA` | `5` | 高斯平滑強度（越大越圓滑） |
| `AMP_HEIGHT` | `0.5` | 振幅曲線最大高度（英吋） |
| `AMP_ALPHA` | `0.85` | 色帶不透明度（0=透明，1=實心） |

### 顏色映射（HSL）

| 參數 | 預設值 | 說明 |
|------|--------|------|
| `HUE_LOW` | `0.04`（≈ 14°，橙紅） | 低頻色相 |
| `HUE_HIGH` | `0.67`（≈ 240°，藍紫） | 高頻色相 |
| `HSL_SATURATION` | `0.65` | 彩度（0=灰階，1=全彩） |
| `HSL_LIGHTNESS` | `0.50` | 明度 |
| `RMS_SILENCE_THRESHOLD` | `0.02` | 靜音門檻，低於此值的區段顯示為透明 |
| `CENTROID_HZ_MIN` | `None` | 顏色映射下界（Hz），`None` = 自動偵測 |
| `CENTROID_HZ_MAX` | `None` | 顏色映射上界（Hz），`None` = 自動偵測 |

---

## 進階用法

### 只對特定聲部顯示部分 marker

```python
{
    'label': 'R',
    'audio_file': 'rhythm.wav',
    'show_markers': [1, 2, 5]   # 只在 marker 1、2、5 位置畫刻度線
}
```

### 固定顏色映射範圍（多聲部統一基準）

若各聲部頻率範圍差異大，可手動設定固定範圍，讓顏色在不同聲部間具有可比性：

```python
CENTROID_HZ_MIN = 200   # 所有聲部的顏色下界固定為 200 Hz
CENTROID_HZ_MAX = 8000  # 所有聲部的顏色上界固定為 8000 Hz
```

### 調整色彩配置

色相範圍可以任意修改（0.0–1.0 對應 HSL 色輪 0°–360°）：

```python
HUE_LOW  = 0.33  # 綠色（低頻）
HUE_HIGH = 0.83  # 粉紫色（高頻）
```

---

## 輸出命名規則

```
{OUTPUT_PREFIX}_{label}_row_{row_idx}.png
```

例如：`timeline_v6_K_row_1.png` = 聲部 K 的第 1 行時間軸。

每行的時間範圍由 marker 自動切分：
- 第 N 行的起點 = 第 `(N-1) × MARKERS_PER_ROW + 1` 個 marker 的時間
- 第 N 行的終點 = 下一行第一個 marker 的時間（最後一行延伸至音訊結尾）

---

## 常見問題

**Q：執行時出現 `FileNotFoundError: marker.txt`**
→ 確認 `marker.txt` 在執行目錄下，或修改 `INPUT_MARKERS` 為完整路徑。

**Q：出現 `FileNotFoundError: key.wav`**
→ 確認各 `audio_file` 路徑正確，WAV 須為單聲道或立體聲皆可（librosa 自動轉單聲道）。

**Q：時間碼對不上**
→ 確認 `FPS` 設定與 DAW 專案幀率相同（常見值：24、25、30）。

**Q：顏色全部一樣或偏灰**
→ 嘗試降低 `HSL_SATURATION`（彩度）或調整 `RMS_SILENCE_THRESHOLD`；也可固定 `CENTROID_HZ_MIN / MAX` 範圍來增加顏色對比。

**Q：想要更粗/更細的振幅曲線**
→ 調整 `AMP_HEIGHT`（曲線高度）和 `SMOOTH_SIGMA`（平滑程度）。

---

## marker.txt 格式（DAW 匯出參考）

以下為支援的格式範例（可直接由 Reaper 的 Region/Marker Manager 匯出後整理）：

```
1 - 00:00:00.00
2 - 00:00:33.07
3 - 00:00:48.12
4 - 00:00:52.01
```

- 編號與時間碼之間以 ` - ` 分隔（空格-連字號-空格）
- 時間碼格式：`HH:MM:SS.FF`（FF 為幀數，非毫秒）
- 空白行會自動忽略

---

## 授權

本工具為個人製作工具，無正式授權條款，請自由使用與修改。
