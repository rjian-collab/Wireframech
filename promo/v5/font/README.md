# Wireframech Line 字型（鋼弦機兵 宣傳影片用）

原創的細線 HUD 風格英數字型：等粗單線、只用直線、圓角全部改成 45° 切角、字寬略寬，
適合放在深色背景加發光效果。

## 檔案說明

| 檔案 | 用途 |
|---|---|
| `WireframechLine-Thin.ttf / .otf` | 細體（線寬 40）— 副標、小字、網址 |
| `WireframechLine-Regular.ttf / .otf` | 標準體（線寬 70）— 標題、手機上的小字 |
| `WireframechLine-*.woff2` | 網頁用（CSS `@font-face`） |
| `generate_font.py` | 字型產生器（改字形就改這個） |
| `make_preview.py` | 重新產生預覽圖 |
| `preview/` | 預覽圖 |

收錄：A–Z（小寫 a–z 自動顯示成同樣的大寫字形）、0–9、
`. , : ; ! ? ' " ` - _ / \ | ( ) [ ] { } + = & # @ % * < > ~ ^ $`、`× · • ● – — → ← ↑ ↓ ▶ °`。
**沒有中文字**，中文請搭配其他字型。

容易混淆的字已特別區分：`0` 有斜線、`O` 較寬；`1` 有底座橫線、`I` 是單一直線；
`5` 左上是直角、`S` 全是切角；`8` 左側有切角、`B` 左側是直線。

## 在 Windows 11 安裝

1. 在檔案總管找到 `WireframechLine-Regular.otf`（或 `.ttf`，擇一即可，兩種都裝會重複）。
2. 按右鍵 → **安裝**（想給所有使用者用就選「為所有使用者安裝」）。
3. `WireframechLine-Thin.otf` 也照做。
4. 重開剪輯軟體，字型清單裡找 **Wireframech Line**，粗細選 Thin 或 Regular。

## 在影片剪輯軟體中使用

- Premiere Pro / After Effects / DaVinci Resolve / CapCut 電腦版：安裝後直接在文字工具選字型即可。
- 發光效果建議：白色或青色（例如 `#5AEBFF`）文字 + 外光暈/Glow（半徑小、中各一層）。
- 手機直式影片上的小字建議用 **Regular**，Thin 留給大字或較大的副標。
- 字距本身已經偏寬，通常不用再加；想更有科技感可加 +2～+5% 字距（tracking）。

## 在網頁或宣傳腳本中使用（CSS）

把 `.woff2` 檔放到網頁資料夾（例如 `fonts/`），然後：

```css
@font-face {
  font-family: "Wireframech Line";
  src: url("fonts/WireframechLine-Regular.woff2") format("woff2");
  font-weight: 400;
}
@font-face {
  font-family: "Wireframech Line";
  src: url("fonts/WireframechLine-Thin.woff2") format("woff2");
  font-weight: 200;
}
.title {
  font-family: "Wireframech Line", sans-serif;
  color: #7ff;
  text-shadow: 0 0 6px #2cf, 0 0 18px #09f, 0 0 40px #07f; /* 發光 */
}
```

用 Playwright / Puppeteer 錄宣傳畫面時，記得等字型載入完再截圖：
`await page.evaluate(() => document.fonts.ready)`。

Python（Pillow）畫圖：`ImageFont.truetype("WireframechLine-Regular.ttf", 64)`。

## 修改字形並重新產生

1. 安裝工具（只需一次）：`pip install fonttools shapely brotli pillow`
2. 用文字編輯器打開 `generate_font.py`，找到 `G["A"] = ...` 這類的行。
   - 座標系統：大寫高度 700，基線 y=0，中間 y=350，x 從 0 往右。
   - `w=` 是字寬；`p=[...]` 是一條條「中心線」，每條線是一串 (x, y) 點，依序連起來。
   - 線的第一點與最後一點相同 = 封閉形狀（例如 `O`）。
   - `d=[(x, y)]` 是方形點（句點、冒號）；`f=[...]` 是實心形狀（●）。
   - 例：想讓 `A` 的橫槓高一點，把 `[(0, 290), (560, 290)]` 改成 `[(0, 330), (560, 330)]`。
3. 想改線條粗細：修改檔案上方 `WEIGHTS` 的數字（例如加一行 `"Bold": (100, 700),` 就會多一個粗體）。
4. 執行：`python generate_font.py`（會覆蓋同資料夾的字型檔），再執行 `python make_preview.py` 看預覽圖。
5. 若 Windows 已安裝舊版：先到「設定 → 個人化 → 字型」解除安裝舊版，再安裝新版，並重開剪輯軟體。

## 授權

此字型為本專案原創設計（程式產生，未描摹任何既有字型），著作權歸使用者所有，可自由用於遊戲與宣傳。
若之後想公開分享字型檔，建議採用 **SIL Open Font License 1.1 (OFL)**。
