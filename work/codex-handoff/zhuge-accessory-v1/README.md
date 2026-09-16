# CT-ACCESSORY-01 — 巾冠 / 胡须 / 羽扇

独立附件小样。**不是完整人物。不是衣袍。不是 G1–G5。不是美术 PASS。** 无骨架，**不会走路**。

只读复用：人体 `624e008349a447859ed58417394c68f382e9b887`（头/手定位、相机拟合、宫苑暖主光/冷补、Principled 材质）。只读对照着装入口 `72f854997468595b7492d709d8235db6cd74cf0c` 的 `build_clothed_v1.py`。**不复用** `3d4a40c5350ec46b9ff54547df9af1818f2dea08` 衣袍。不改旧生成器。

本目录只写三件。首包 `45fa1f5` 本机 ART_FAIL 后只做这一次定向修复：巾前下沿按真实眼眉坐标抬到发际并收回悬挑（三角跨越/前视遮挡验收，不再用顶点脸带代理）；须改为下巴分束扁平锁，去掉侧管支架；羽片收尖、羽轴收进片内、短柄不横穿双手。头/手完整表面作参照。头图框巾+整须、不含扇；扇图框扇+整手、不含断颈/须尖。肩以下不是服装展示。**未实看修后图不得报美术通过。**

## 依赖（只读，不提交人体树）

把 pinned `work/codex-handoff/zhuge-anatomy-base/` 放在本目录的**上一级**（与本包并列），或传 `--anatomy-dir`。缺文件会报明确错误，不重建人体。

## 入口

`--source-obj` / `--output-dir` / `--anatomy-dir` 在 Blender 里写在 `--` 后面。

```bash
cd work/codex-handoff/zhuge-accessory-v1

# Mac Blender 5.2.1
blender --factory-startup --background --disable-autoexec -P build_accessory_v1.py -- \
  --source-obj "$(pwd)/../zhuge-anatomy-base/source/base.obj" \
  --output-dir "$(pwd)/out"

# 人体不在并列目录时
blender --factory-startup --background --disable-autoexec -P build_accessory_v1.py -- \
  --anatomy-dir /path/to/zhuge-anatomy-base \
  --source-obj /path/to/zhuge-anatomy-base/source/base.obj \
  --output-dir "$(pwd)/out"

# 云 / 无 bpy：纯几何检查，physics/render = UNRUN
python3 build_accessory_v1.py \
  --anatomy-dir "$(pwd)/../zhuge-anatomy-base" \
  --source-obj "$(pwd)/../zhuge-anatomy-base/source/base.obj" \
  --output-dir "$(pwd)/out"
```

写出：`zhuge_accessory_v1.glb` / `.blend`，头肩裁切 `view_front/front_l45/front_r45/side/back.png`，扇局部 `view_fan.png`，对应 `clay_*.png`，`accessory_report.json`。

census 的 mesh/面/包围盒/连通性/开边 **不等于** 美术 PASS。
