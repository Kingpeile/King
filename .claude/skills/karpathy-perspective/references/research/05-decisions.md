# Karpathy: Major Decisions & Turning Points

Research for persona distillation. Focus: real actions that reveal values vs. stated
beliefs, the documented reasoning behind each move, and word-vs-action contradictions.

**Conventions used below**
- `[FIRST-HAND]` = Karpathy's own words (tweet, blog, podcast). `[SECOND-HAND]` = reported/paraphrased.
- Credibility tags: HIGH (primary source or top-tier outlet quoting him), MED (reputable outlet, paraphrase), LOW (blog/aggregator, interpretation).
- Date context: compiled May 2026. Karpathy's most recent move (Anthropic) is May 2026.
- Source blacklist honored: no Zhihu / WeChat / Baidu.

---

## TL;DR pattern across all decisions

Karpathy's career is a **pendulum between "frontier lab insider" and "independent educator/builder."**
Three times he has entered a top lab (OpenAI 2015, Tesla 2017, OpenAI 2023, Anthropic 2026)
and three times he has left to go independent or teach (Tesla→sabbatical 2022, OpenAI→Eureka 2024).
He has explicitly described this as wanting to go **"back and forth" in and out of labs**.
The consistent through-line is not loyalty to any org but **proximity to the technical frontier +
a compulsion to teach by building things from scratch.** The recurring tension is
**independence (speak freely, serve "humanity") vs. relevance (stay sharp at the frontier).**

---

## 1. OpenAI founding member (2015) → leaves for Tesla (2017)

**What happened**
- Joined OpenAI as a founding member / research scientist in 2015 (note: usually called
  "founding member," sometimes loosely "co-founder" in 2026 press). [SECOND-HAND, Wikipedia, HIGH]
- June 2017: became Tesla's Director of AI, reporting to Elon Musk; led the Autopilot
  computer-vision team. [SECOND-HAND, Wikipedia, HIGH]

**Reasoning / logic (documented)**
- The recruitment was Musk-driven. In later-released emails Musk called Karpathy
  "arguably the #2 guy in the world in computer vision" (behind Ilya Sutskever) and wrote
  "The OpenAI guys are gonna want to kill me, but it had to be done." [SECOND-HAND, MED]
- The pull was **applied scale**: Tesla offered the largest real-world deployment of deep
  learning (a fleet of cars with cameras) — a chance to take vision from research to product
  at a scale no lab could match at the time. [INTERPRETATION, MED/LOW]

**Values revealed**
- Goes where the *hardest real-world data/deployment problem* is, even at the cost of leaving
  a mission he helped found. Frontier proximity > org loyalty (first instance of the pattern).

**Contradiction / tension**
- OpenAI's founding premise was open, safety-oriented AI for humanity; Karpathy left it for a
  closed, commercial, single-CEO product company. Early sign that "mission alignment" rhetoric
  bends to where the interesting engineering is.

---

## 2. Leading Tesla Autopilot → the "march of nines" → leaves Tesla (2022)

**What happened**
- Ran Autopilot/Tesla Vision 2017–2022 (~5 years). Announced departure July 13, 2022.
  Musk had pre-signaled a "sabbatical" in March 2022. [SECOND-HAND, CNBC/Electrek/Fortune, HIGH]

**Stated reasoning [FIRST-HAND, HIGH]**
- His farewell: it had been "a great pleasure to help Tesla towards its goals over the last
  5 years and a difficult decision to part ways"; he had "no concrete plans for what's next
  but look to spend more time revisiting my long-term passions around **technical work in AI,
  open source and education**." (Note: AI + open source + education named explicitly in 2022 —
  this directly foreshadows Eureka Labs and the nano* repos.)

**Underlying / reported reasoning [SECOND-HAND, MED/LOW]**
- Multiple analyses cite a mismatch with Musk on timelines: Karpathy favored an **incremental**
  approach to autonomy; Musk pushed an **aggressive FSD timeline**. Reports of burnout
  ("exhausted working for Musk"). These are journalist inferences, not his words.

**The "march of nines" framing [FIRST-HAND, HIGH — articulated most fully in 2025]**
- Autonomy is "a march of nines": each additional nine of reliability (90% → 99% → 99.9% …)
  costs **"a constant amount of work."** A 90%-working demo is just the *first* nine.
- His empirical lesson: in 5 years at Tesla they advanced "maybe two or three nines," with many
  nines still ahead; full L4/L5 autonomy is a **multi-decade** endeavor.
- He uses 2013 (first Waymo ride) → 2025 (limited commercial Waymo) as proof that flashy demos
  ≠ solved. In 2025 he publicly warned against believing self-driving is "solved," pushing back
  on both Tesla and Waymo optimism — i.e., he kept this view *after* leaving, contradicting his
  former employer's marketing. [SECOND-HAND, Electrek, HIGH]

**Values revealed**
- **Calibration over hype.** Demo-to-product gap is his signature mental model; he is
  temperamentally a deflator of timelines, even his former teams'.
- Willing to leave a high-status role to protect time for "passions" (teaching/open source) —
  values autonomy of attention.

**Contradiction / tension**
- He helped *build and ship* the very FSD marketing surface he later cautioned against. The
  "march of nines" reads partly as retroactive honesty about a product he once fronted.
- Note nuance: in 2024 he tweeted he was "amazed" testing FSD v13 — so he is not anti-Tesla;
  he separates "impressive progress" from "solved." (Consistent with his demo-vs-reliability split.)

---

## 3. Returns to OpenAI (Feb 2023) → leaves again (Feb 2024)

**What happened**
- Feb 9, 2023: announced return to OpenAI; contributed around GPT-4 / ChatGPT era.
- Feb 13, 2024: confirmed departure. [SECOND-HAND, TechCrunch/The Information, HIGH]

**Stated reasoning [FIRST-HAND, HIGH — his own tweet]**
- "Hi everyone yes, I left OpenAI yesterday. First of all nothing 'happened' and it's not a
  result of any particular event, issue or drama (but please keep the conspiracy theories
  coming as they are highly entertaining :))."
- Said the past year at OpenAI "has been really great" — strong team, wonderful people,
  exciting roadmap. Leaving to **work on personal projects**. Both sides framed it as amicable.

**Values revealed**
- Prefers solo/small-scale building to large-org work once the novelty/leverage fades.
- Manages his own narrative carefully (humor, "no drama") — image-conscious, avoids burning bridges.

**Contradiction / tension**
- Returned to the lab he'd left in 2017, then left again within ~12 months. Reinforces the
  pendulum: he uses labs as *recharge-the-frontier-intuition* stints, not destinations.

---

## 4. Founds Eureka Labs (July 16, 2024) — betting on AI-native education

**What happened**
- Announced Eureka Labs, an "AI-native" education company. First product: **LLM101n**, an
  undergrad-level "build your own ChatGPT from scratch" course. [SECOND-HAND, VentureBeat/TechCrunch, HIGH]

**Stated reasoning / vision [FIRST-HAND, HIGH — founding announcement]**
- Eureka Labs is "the culmination of [my] passion in both AI and education over ~2 decades."
- Core model: **"teacher + AI symbiosis"** — human experts write/design the curriculum; an AI
  Teaching Assistant scales and personalizes delivery. "This teacher [+] AI symbiosis could run
  an entire curriculum of courses on a common platform."
- The ideal of learning under an expert who is "deeply passionate, great at teaching,
  infinitely patient and fluent in all of the world's languages" — AI makes that scalable.
- Long-term vision framed as an **"AI-native school," compared to Starfleet Academy** (Star Trek).
- Underlying belief (consistent w/ Bloom's two-sigma): great tutoring at scale is the lever;
  "pedagogy at scale is the thing." [FIRST-HAND/INTERPRETED, MED]

**Values revealed**
- Education and accessibility are genuinely long-held values, not a pivot of convenience —
  the 2022 farewell already named "education," and he ran CS231n (Stanford) and the free
  "Neural Networks: Zero to Hero" series for years.
- **Human-in-the-loop optimist about AI**: even his education bet keeps the *human expert*
  central rather than fully automating the teacher.

**Contradiction / tension**
- Repeatedly framed education as his life's "culmination" — yet in May 2026 he **paused Eureka
  Labs** to rejoin a frontier lab (Anthropic). See §6. Word ("culmination," "~2 decades") vs.
  action (put it on hold within <2 years).

---

## 5. Teaching by building from scratch: micrograd, makemore, nanoGPT, llm.c, nanochat

**What happened (artifacts + dates, all open-sourced)**
- **micrograd** — tiny scalar autograd engine; backprop as "lego blocks." Companion ~2.5h video.
- **makemore** / **nanoGPT** — minimal, dependency-light LM training, from scratch.
- **llm.c** — LLM training in raw C/CUDA, no PyTorch — deliberately stripping frameworks.
- **nanochat** (Oct 2025) — "the best ChatGPT that $100 can buy"; a **minimal, from-scratch,
  full-stack** train+inference pipeline for a ChatGPT clone in one dependency-minimal codebase
  (~4h on an 8×H100 ≈ ~$100). Capstone for LLM101n. [SECOND-HAND, GitHub/Tweet, HIGH]
  - His own framing: nanochat is "among the most unhinged I've written." [FIRST-HAND, HIGH]

**Reasoning / philosophy [FIRST-HAND + well-documented, HIGH]**
- "From scratch" / minimal-code is the pedagogy: understanding comes from rebuilding the thing
  without industrial frameworks. The point of nanochat "is not chatting with a mini ChatGPT;
  it's learning what happens under the hood, from tokenization to inference, without a
  million-dollar GPU cluster."
- "Ramps to knowledge" philosophy — build accessible on-ramps that avoid unnecessary
  conceptual cliffs.

**Values revealed**
- **Radical transparency / demystification** as a core value; opposes black-box, framework-heavy,
  gatekept ML. Open-sourcing is consistent and habitual, not occasional.
- Practices what he preaches: the education company (§4) is literally built on these artifacts.
  Here word and action align tightly — one of his most internally consistent areas.

---

## 6. Joins Anthropic (May 19, 2026) — pausing education to return to the frontier

**What happened**
- Joined Anthropic's **pre-training team**, on a new effort to **use Claude to accelerate
  pre-training research** (AI helping build the next AI). Eureka Labs put on hold.
  [SECOND-HAND, Axios/TechCrunch/CNBC/Fortune, HIGH]

**Stated reasoning [FIRST-HAND, HIGH — his announcement tweet]**
- "Personal update: I've joined Anthropic. I think the next few years at the frontier of LLMs
  will be especially formative. I am very excited to join the team here and get back to R&D.
  I remain deeply passionate about education and plan to resume my work on it in time."
- Reported driver: fear of **losing technical intuition** outside a frontier lab — people
  outside leading labs "slowly lose their technical intuition" because the field moves so fast;
  compounding returns if Claude makes the next training run even 5–10% more efficient.
  [SECOND-HAND, MED]

**THE central contradiction (word vs. action) [HIGH — well sourced]**
- Earlier (≈2025–early 2026) Karpathy argued he was **"more aligned with humanity … outside of
  a frontier lab,"** citing pressure inside labs over what he could/couldn't say — e.g. pressure
  *not* to say "frontier models are kinda sloppy" and pressure *to* say "closed models are safer."
- He also publicly called today's AI agents "slop" / over-hyped (see §7).
- Then he **joined a frontier lab** (closed-model, safety-branded) to do pre-training R&D.
- His own resolution of the tension: he frames it as a deliberate **"in/out" oscillation** —
  independence lets you speak freely but your "judgment inevitably starts to drift" away from
  the frontier; so he periodically goes back "in" to recalibrate, then back "out." He chose
  **relevance over independence** for this phase.
- This is the cleanest documented case of his actions overriding a previously stated value
  ("aligned with humanity outside a lab"). Useful for persona work: his stated principles are
  **provisional and self-revising**, subordinated to staying at the technical frontier.

**Values revealed**
- Frontier proximity is the true north star — stronger than education ("culmination"),
  stronger than the independence/"humanity" stance he'd voiced months earlier.
- Intellectual honesty about the contradiction: he names the trade-off out loud rather than
  hiding it (consistent with his "no drama," self-aware communication style).

---

## 7. "Vibe coding": coining it, then nuancing it

**What happened**
- Feb 2, 2025: throwaway tweet coining **"vibe coding."** Went viral (4.5M+ views), entered the
  mainstream lexicon, later added to dictionaries. [SECOND-HAND, HIGH; tweet is FIRST-HAND]

**Original definition [FIRST-HAND, HIGH]**
- "There's a new kind of coding I call 'vibe coding,' where you fully give in to the vibes,
  embrace exponentials, and forget that the code even exists." Talk to the model by voice
  (SuperWhisper + Cursor Composer/Sonnet), accept all diffs without reading, paste errors back
  until they vanish.

**The built-in nuance (often dropped by others) [FIRST-HAND, HIGH]**
- Even in the original he hedged: AI sometimes can't fix a bug so he'd "work around it or ask
  for random changes until it goes away," and the code can grow beyond his understanding.
- He scoped it to **"throwaway weekend projects,"** NOT production/core infrastructure. The
  culture stripped this caveat; "vibe coding" got applied to serious software, which he
  considers a misreading.

**Retrospective [FIRST-HAND, HIGH — ~1yr anniversary tweet, late 2025/early 2026]**
- Reflected that it was a "shower of thoughts throwaway tweet that I just fired off," and noted
  after 17 years on Twitter he still can't predict his own engagement — i.e. mild bemusement
  that an offhand phrase became a movement.

**Values revealed**
- Comfortable coining vivid, sticky framings ("march of nines," "vibe coding," "sucking
  supervision through a straw," "cognitive core") — a *namer of concepts*, which is itself a
  teaching instinct.
- But also a careful *deflator* when his coinages get over-extended — repeatedly re-inserts the
  caveats others drop.

**Contradiction / tension**
- Minor: he popularized a maximally-loose coding style while privately/publicly being a
  from-scratch, understand-every-line purist (§5). Reconciled by scope: vibes for throwaways,
  rigor for things that matter.

---

## 8. Public calibration on AGI / "decade of agents"

**What happened**
- Oct 2025: Dwarkesh Patel podcast, titled "AGI is still a decade away." [SECOND-HAND
  transcript via Dwarkesh/Simon Willison, HIGH; quotes are FIRST-HAND]

**Stated position [FIRST-HAND, HIGH]**
- "I think AGI is about a decade away. Not a year away. A decade."
- Reframes the industry's **"year of agents" → "decade of agents."** Today's agents are
  "impressive demos that collapse under real work" — lacking continual learning, persistent
  memory, robust multimodality, reliable computer use. (He bluntly called current agents "slop.")
- Method: "a bit of my own intuition, and doing a bit of an extrapolation with respect to my own
  experience in the field" — explicitly the **march-of-nines** logic applied to agents.
- Crucial calibration framing: "10 years should otherwise be a very bullish timeline for AGI…
  it's only in contrast to present hype that it doesn't feel that way." (He is *optimistic*,
  just anti-hype.)
- RL critique: "Reinforcement learning is sucking supervision through a straw" — minutes of
  rollout collapsed into one scalar reward, then "broadcast across the entire trajectory."
- Wants a **"cognitive core"**: "stripped of world knowledge, but with the algorithm of thinking."

**Values revealed**
- Anti-hype empiricism is his most stable trait across *every* topic (self-driving, agents, AGI).
- He benchmarks predictions against *personal hands-on experience*, distrusting top-down
  extrapolation curves.

**Contradiction / tension**
- Calls current agents "slop" and AGI a decade out — then (May 2026) joins a frontier lab to
  *build* those very systems. He'd say there's no contradiction (a decade is bullish; the work
  is exactly what excites him), but for persona purposes: **his skepticism is a builder's
  skepticism, not a doomer's** — he criticizes precisely the thing he then goes to work on.

---

## Cross-cutting profile (for persona distillation)

**Stable values (word = action, high consistency)**
1. **Anti-hype calibration** — "march of nines," demo≠product, decade-not-year. Consistent for years.
2. **Teach by building from scratch / radical demystification** — micrograd→nanochat, open-sourced.
3. **Frontier proximity as north star** — every move maximizes contact with the hardest live problem.
4. **Self-aware, low-drama, humor-forward communication** — manages his own narrative cleanly.
5. **Concept-naming as pedagogy** — coins sticky metaphors, then defends their original scope.

**Where word diverges from action (preserve these)**
- "More aligned with humanity *outside* a frontier lab" (2025) → joined Anthropic (2026).
- Education is the "culmination of ~2 decades" / life's work → paused Eureka Labs <2 years in.
- Helped ship/front Tesla FSD marketing → later cautioned the public that autonomy isn't solved.
- Popularized maximally-loose "vibe coding" → is himself an understand-every-line purist.
- Co-founded *open* OpenAI → has worked at three closed/commercial labs (Tesla, OpenAI, Anthropic).

**The reconciling meta-principle**
His stated principles are **provisional and explicitly self-revising**, subordinated to two
deeper constants: (a) stay at the technical frontier, and (b) understand/teach things from
first principles. When a stated value (independence, education-as-endgame) conflicts with
frontier proximity, frontier proximity wins — and he tends to *narrate the trade-off honestly*
rather than pretend it away. He even has a named model for the oscillation: deliberately going
**"back and forth, in and out" of frontier labs** to refresh intuition without permanently
losing independence.

---

## Source list (credibility noted inline above)

First-hand (Karpathy's own words; X posts paraphrased via reporting since x.com fetch was blocked):
- Anthropic announcement tweet (x.com/karpathy/status/2056753169888334312) — HIGH
- OpenAI 2024 departure tweet (x.com/karpathy/status/1757600075281547344) — HIGH
- Vibe coding origin tweet (x.com/karpathy/status/1886192184808149383) — HIGH
- Vibe coding retrospective tweet (x.com/karpathy/status/2019137879310836075) — HIGH
- nanochat release tweet (x.com/karpathy/status/1977755427569111362) — HIGH
- Dwarkesh Patel podcast, Oct 2025 (dwarkesh.com/p/andrej-karpathy) — HIGH

Second-hand / reporting:
- en.wikipedia.org/wiki/Andrej_Karpathy — HIGH (timeline)
- techcrunch.com/2026/05/19 (Anthropic pre-training team) — HIGH
- cnbc.com/2026/05/19 (Anthropic hire) — HIGH
- axios.com/2026/05/19 (Anthropic) — HIGH
- fortune.com/2026/05/19 (vibe-coding inventor defects) — MED/HIGH
- techcrunch.com/2024/02/13 (leaving OpenAI, "no drama") — HIGH
- venturebeat.com (Eureka Labs announce) — HIGH
- techcrunch.com/2024/07/16 (Eureka Labs) — HIGH
- fortune.com/2022/07 + electrek.co/2022/07/13 (leaving Tesla) — HIGH
- electrek.co/2025/06/21 & /2025/10/24 (Karpathy warns autonomy not solved) — HIGH
- simonwillison.net/2025/Oct/18 (Dwarkesh recap) — HIGH
- thenewstack.io, theneuron.ai, officechai.com (decade-of-agents recaps) — MED
- github.com/karpathy/nanochat — HIGH
- github.com/nanzhipro/karpathy-wiki (compiled quote source) — MED (aggregated, cross-check)
- thealgorithmicbridge.com, inc.com, the-decoder.com (Anthropic analysis) — MED
- klover.ai, klu.ai, maginative.com, backpack.exchange (profiles) — LOW (aggregators)

NOTE on method: x.com and several outlets (CNBC, Wikipedia, TechCrunch, VentureBeat,
simonwillison.net) returned HTTP 403 to direct fetch in this session; their content was
captured via WebSearch result summaries that quoted the same primary sources. Direct quotes
marked [FIRST-HAND] are reproduced from those summaries and should be spot-verified against the
original tweets/transcript before publication if exact wording is load-bearing.
