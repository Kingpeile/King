# Honest fixtures (not character assets)

Bundled GLBs are tiny cubes/tetrahedra for tests and screenshots. They are **not** the scholar source, **not** the Kimi delivery, and **not** art-review subjects.

| File | What it is | Expected |
|---|---|---|
| `a1.glb` | Unit cube at origin | 12 triangles, 0 skins, 0 animations |
| `a2.glb` | Tetrahedron translated +X | 4 triangles (A1→A2 replacement target) |
| `b.glb` | Cube translated −X, scale Y×2 | 12 triangles |
| `invalid.glb` | Not a GLB | parse error |
| `external.glb` | `mesh.bin` + `albedo.png` URIs | must be blocked, no network |
| `skinned-count.glb` | Cube plus one skin and one empty animation | counts 1 / 1; walking **not** proven |

Cloud agents cannot read local scholar/Kimi paths. The viewer only loads files the user explicitly selects (or these bundled self-test bytes).
