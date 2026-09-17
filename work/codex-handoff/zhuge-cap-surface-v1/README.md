# CT-CAP-FIT-01-FIX — 头网格纶巾定向返工

独立帽壳。**不是完整人物。不是衣袍。不是须/扇。不是 G1–G5。不是美术 PASS。** 无骨架，**不会走路**。

首包 `3620dc70f6894c18cb99f6955766b9a1878d582d` 本机 ART_FAIL 已保留（`out/cap_surface_report_3620dc7.json`）：贴合路径成立，但耳/颞被整面贴进帽、顶是泳帽、前沿悬挑压眉、参照颈切锯齿。

只读人体：PR17 `624e008349a447859ed58417394c68f382e9b887`。官方 MPFB `base.obj` `437dd513888a92399d1d3200d2e80859fae55abc`，SHA256 `8e761e6624b8f54536409135d1636da63b32486a90d4897f84e121d144f6fb4c`。不复用 PR19 `build_guan` / `ring_at` / loft。

此次唯一返工：对真实头皮三角做隐式发际剪裁（新顶点记 source-face + barycentric），完整排除耳；内层仍是该曲面约束；外层是布网格折面（前额连续折边、顶/侧少量折面体积）；前额 Y 钳制去掉悬挑；`ref_head` 用水平面平整裁切，整头+双耳，不改解剖。光照只加正面补光取证，不关阴影。

## 白名单（仅此包）

- `build_cap_surface.py`
- `README.md`
- `.gitignore`
- `out/cap_surface_report.json`
- `out/cap_surface_report_3620dc7.json`

不提交人体树、不提交 PNG/GLB/blend。

## 一次本机运行（Blender 5.2.1）

```bash
cd work/codex-handoff/zhuge-cap-surface-v1

blender --factory-startup --background --disable-autoexec -P build_cap_surface.py -- \
  --anatomy-dir "$(pwd)/../zhuge-anatomy-base" \
  --source-obj "$(pwd)/../zhuge-anatomy-base/source/base.obj" \
  --output-dir "$(pwd)/out"
```

Mac 写出：`zhuge_cap_surface_v1.glb` / `.blend`，同尺度头颈裁切 `view_front/45/side/back/top.png` + `clay_*.png`（共 10 图），新报告。首包报告不被覆盖。

## 云 / 无 bpy

```bash
python3 build_cap_surface.py \
  --anatomy-dir /path/to/zhuge-anatomy-base \
  --source-obj /path/to/zhuge-anatomy-base/source/base.obj \
  --output-dir "$(pwd)/out"
```

几何门可跑。physics / render = **UNRUN**。数值≠美术合格。根实看前不得报通过。

## 本机怎么看（未验项）

1. 耳露出、沿口连续，不再齿状贴脸。
2. 前沿无悬挑，温和正面光下眉眼清楚（阴影仍开）。
3. 灰模能读出纶巾折边/折面，不是再厚一号泳帽。
4. 参照头颈是平截面，双耳在，头皮未删未缩。
5. 未实看 10 图不得报 03 美术通过，不得宣称完整诸葛亮。
