# CT-CAP-FIT-01 — 真实头网格纶巾贴合小样

独立帽壳试验。**不是完整人物。不是衣袍。不是须/扇。不是 G1–G5。不是美术 PASS。** 无骨架，**不会走路**。

只读人体：GitHub `Kingpeile/King` PR17 commit `624e008349a447859ed58417394c68f382e9b887` 的 `work/codex-handoff/zhuge-anatomy-base/`。官方 MPFB `base.obj` commit `437dd513888a92399d1d3200d2e80859fae55abc`，文件 SHA256 `8e761e6624b8f54536409135d1636da63b32486a90d4897f84e121d144f6fb4c`。

PR19 `3c771fbb0c4fe66afd80c484462756f17e2ba63c` 的 `build_guan`（单层凸包 + `ring_at` loft）已止损。本包**不复用**那些函数，不改半径重跑。帽壳从固定人体头皮**实际三角面**连通提取，沿曲面法线外偏移成有厚度壳，折面只做外向附加位移。完整头颈网格留下作碰撞和可视参照：不缩头、不删头皮、不用隐藏穿模当通过。

## 白名单（仅此包）

- `build_cap_surface.py`
- `README.md`
- `.gitignore`
- `out/cap_surface_report.json`

不提交人体树、不提交 PNG/GLB/blend。

## 一次本机运行（Blender 5.2.1）

人体须并列自 `624e008`，或 `--anatomy-dir`。输入只读，输出只进本包 `out/`。无下载、无安装、无联网、无后台进程。

```bash
cd work/codex-handoff/zhuge-cap-surface-v1

blender --factory-startup --background --disable-autoexec -P build_cap_surface.py -- \
  --anatomy-dir "$(pwd)/../zhuge-anatomy-base" \
  --source-obj "$(pwd)/../zhuge-anatomy-base/source/base.obj" \
  --output-dir "$(pwd)/out"
```

Mac 写出：`zhuge_cap_surface_v1.glb` / `.blend`，统一头颈裁切 `view_front/45/side/back/top.png` 与对应 `clay_*.png`（共 10 图），`cap_surface_report.json`。

## 云 / 无 bpy

```bash
python3 build_cap_surface.py \
  --anatomy-dir /path/to/zhuge-anatomy-base \
  --source-obj /path/to/zhuge-anatomy-base/source/base.obj \
  --output-dir "$(pwd)/out"
```

几何门可跑。physics / render = **UNRUN**。数值≠美术合格。

## 本机怎么看（未验项）

1. 正 / 45 / 侧 / 背 / 俯视：头顶贴合，侧后连续盖住头皮，前沿在眉以上。
2. 灰模看厚度和折面，不要靠花纹遮瑕。
3. `ref_head` 仍是完整头皮；穿模不能靠删头/藏头过关。
4. JSON 里的 `source_face_ids` / 法线间隙只证明「从哪张头皮面长出来」，**不能**用 maxZ 或顶点框代替实看。
5. 未实看 10 图不得报 03 美术通过，不得宣称完整诸葛亮。
