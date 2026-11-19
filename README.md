# WIREFRAMECH 鋼弦機兵

第一人稱鋼索擺盪機甲射擊遊戲原型，戰場是空中浮島，掉下去就是虛空。用瀏覽器就能玩，以手機和平板橫向觸控為主。

**線上遊玩：** https://wireframech.vercel.app

## 操作（觸控）

環形戰場：兩隊基地在兩端；外圈是往內傾、一階階往上的空島（高機動、難瞄準）；中央平台最低、沒有墜落風險但會被俯射。

| 控制 | 功能 |
|---|---|
| 藍色搖桿 | 移動（推越遠越快）；輕點＝原地跳；快速往任一方向滑出並放開＝往那邊跳（滑越快跳越遠越高）；空中開釘槍＝煞車；釘在牆上時＝沿牆爬（每 6m 用一根釘子） |
| 左索／右索 | 都是小搖桿：按住＝射出鋼索；圈內拖曳＝上收索、下放索、左右擺盪；拖出外圈＝推進；放開＝甩出去 |
| 射擊 | 按住開火；按著拖曳＝邊射邊瞄；往上一甩＝快速一甩切換：上＝01 主武 57mm、左＝02 副武 14.5mm 機槍、右＝03 腿部釘槍 |
| 左上角 3P／1P | 切換第三人稱／第一人稱（鍵盤 V） |
| 畫面其他地方 | 拖曳＝瞄準；快速點兩下＝180° 迴轉；也可開啟陀螺儀 |

開始畫面可選「練習（打靶）」、「對戰 AI」（1v1，先擊破 5 次或 5 分鐘）、「線上對戰」（真人 1v1：快速配對或房間代碼，WebRTC 點對點、不需要伺服器；20 秒沒配到人改打 AI）或「新手教學」（遊戲內逐步引導，第一次練習會自動開始）。目前地圖是「大島・樹林」，環形空島戰場留到之後更新。

設定（右上齒輪）分成操作、鏡頭、新手輔助、陀螺儀、外觀五個分頁。

## 鍵盤

WASD 移動・F 鋼索（勾住時 W/S 收放、A/D 擺盪）・Q／E 左右索・Space／Shift 推進・X 切換武器・R 裝填・滑鼠瞄準、左鍵射擊

## 技術

- [Three.js](https://threejs.org/)：3D 繪圖
- [Rapier3D](https://rapier.rs/)：物理引擎（WASM，跨平台結果一致，方便之後做連線）
- 整個遊戲是單一檔案 `index.html`，從 jsDelivr CDN 載入函式庫，不需要建置步驟
- 部署：Vercel（推送到 `main` 就會自動上線）

## 文件

- [`docs/SPEC.md`](docs/SPEC.md)：設計規格與每個版本的更新紀錄（含數值、設計決策與自動測試結果）


## 素材授權 / Credits

- 機體模型："Eighty-Six XM2 Reginleif [Undertaker]" (https://skfb.ly/oL9Qx) by Z7RO is licensed under Creative Commons Attribution (http://creativecommons.org/licenses/by/4.0/).
  - 已修改：重組腳部關節並以 IK 驅動、調整站姿、移除左刀臂、加裝機槍與鋼索發射器、壓縮貼圖與網格。
  - 注意：CC BY 授權的是建模作品；機體設計屬《86 -不存在的戰區-》原作，正式發布前需換成原創設計。
- "Pine Forest" (https://sketchfab.com/3d-models/pine-forest-ece69535f7584e099488f65f2072264e) by fangzhangmnm is licensed under Creative Commons Attribution (http://creativecommons.org/licenses/by/4.0/). Modified: extracted a single tree, downscaled textures; ground texture reused.
