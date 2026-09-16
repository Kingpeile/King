# CT-BASE-02 morph inventory (data files only — do not install MPFB)

Same MPFB2 commit as BASE-01 `base.obj`. Bundled targets are CC0 (LICENSE.md section C).

| pin | |
|---|---|
| repo | https://github.com/makehumancommunity/mpfb2 |
| commit | `437dd513888a92399d1d3200d2e80859fae55abc` |
| license file SHA256 | `5cefb60680cb9efd4550a2e65d719021cfbec9dad3658481d11d48ae863ce04d` |

| file | repo path | gz bytes | SHA256 |
|---|---|---|---|
| `asian-male-young.target.gz` | `src/mpfb/data/targets/macrodetails/asian-male-young.target.gz` | 130005 | `0928ed8b9f08f60afb9884cf9e9f33a939ed3a85d7f136de9ccc88a76981d6d7` |
| `universal-male-young-maxmuscle-averageweight.target.gz` | `src/mpfb/data/targets/macrodetails/universal-male-young-maxmuscle-averageweight.target.gz` | 45597 | `833caafc302bd9306de494f32ee1bc51d3a2e6641183329b031ac06ef0f4277e` |

Candidate: official MH/MPFB macro endpoints **asian + male + young** at weight 1.0 and **max muscle / average weight** at weight 1.0. Applied on all 19158 source verts, then `body` filter (same keep/drop as BASE-01). Not a uniform X-widen.
