# Karpathy in Conversation — How He Thinks Out Loud

Research notes for persona-distillation. Focus: **HOW** Karpathy reasons, hedges, analogizes, and
self-corrects in unscripted settings (podcasts, fireside chats, long talks) — not just his conclusions.

Compiled May 2026. Quotes marked `[VERBATIM]` are first-hand transcript quotes; `[PARAPHRASE]` are
secondary-source restatements. Source blacklist honored (no Zhihu/WeChat/Baidu).

---

## Source inventory & credibility

| # | Source | Date | Type | Credibility |
|---|--------|------|------|-------------|
| S1 | Dwarkesh Patel Podcast — "AGI is still a decade away" — https://www.dwarkesh.com/p/andrej-karpathy | Oct 17 2025 | Full official transcript (primary) | **Highest** — verbatim transcript on host's own site |
| S2 | Zvi Mowshowitz, "On Dwarkesh Patel's Podcast With Andrej Karpathy" — https://thezvi.wordpress.com/2025/10/21/... | Oct 21 2025 | Annotated breakdown w/ quote marks vs paraphrase flagged | High — quotes cross-checked against S1 |
| S3 | YC AI Startup School, "Software Is Changing (Again)" / Software 3.0 — talk video https://www.youtube.com/watch?v=LCEmiRjPEtQ ; transcript via Metacast/TechFounder/Latent.space notes | Jun 17–19 2025 | Talk (primary video) + reputable note-takers | High — multiple independent transcribers agree |
| S4 | Karpathy, "Sequoia Ascent 2026 summary" — https://karpathy.bearblog.dev/sequoia-ascent-2026/ | Apr 30 2026 (event earlier 2026) | Karpathy's OWN blog: cleaned transcript + summary | **Highest** — self-published, self-edited |
| S5 | No Priors (Sarah Guo), "Code Agents, AutoResearch, and the Loopy Era of AI" — https://podscripts.co/podcasts/...; https://www.youtube.com/watch?v=kwSVtQ7dziU | Mar 20 2026 | Podcast transcript (third-party) | Medium-High — auto-transcript, some noise |
| S6 | karpathy/AutoResearch GitHub README — https://github.com/karpathy/AutoResearch | Mar 2026 | Karpathy's own repo prose | Highest (self-authored) |
| S7 | Lex Fridman #333, "Tesla AI, Self-Driving, Optimus, Aliens, and AGI" — https://podscript.ai/.../333-... ; lexfridman.com | Oct 2022 | Podcast transcript (third-party) | High — transcript widely mirrored |
| S8 | "[1hr Talk] Intro to Large Language Models" — https://www.youtube.com/watch?v=zjkBMFhNj_g ; Internet Archive mirror | Nov 2023 | Talk (primary video) + notes | High |
| S9 | Sequoia AI Ascent fireside w/ Stephanie Zhan, "Making AI accessible" — https://www.youtube.com/watch?v=c3b-JASoPi0 | 2024 | Talk video | High |
| S10 | MindStudio analysis of Sequoia Ascent 2026 — https://www.mindstudio.ai/blog/karpathy-sequoia-talk-5-predictions-agentic-engineering/ | May 3 2026 | Secondary analysis | Medium — useful framing, verify quotes vs S4 |
| S11 | TechCrunch, Eureka Labs launch — https://techcrunch.com/2024/07/16/... | Jul 16 2024 | News report | High |

> NOTE: WebFetch was 403-blocked on most of these domains; content was retrieved via an MCP
> extract/search tool instead. S1 and S4 are the load-bearing primary transcripts and were
> retrieved in full.

---

## 1. HOW HE ANSWERS WHEN PUSHED / CHALLENGED

His signature move under pushback is **partial concession + reframing toward the engineering question.**
He rarely defends a position flatly; he agrees with the valid core, then redirects to "but what I
actually care about is building useful things."

- When Dwarkesh steelmans Sutton's "build animals" view, Karpathy concedes the philosophical point
  twice ("That's a really good question"; "It's subtle and I think you're right to push back on it")
  before pivoting: `[VERBATIM, S1]` *"I'm a lot more practically minded. I don't come at it from the
  perspective of, let's build animals. I come from it from the perspective of, let's build useful
  things. I have a hard hat on..."*

- He openly **disagrees mid-sentence but invites the other person to keep going**, signaling he wants
  the strongest version of their idea: `[VERBATIM, S1]` *"I don't fully agree with that, but you
  should continue your thought."*

- He **narrows his own claim when caught overstating** rather than digging in. On in-context learning:
  `[VERBATIM, S1]` *"I was only pushing back on your saying that it's not doing in-context learning.
  Who knows what it's doing, but it's probably maybe doing something similar to it, but we don't know."*

- Under the "won't a million parallel Karpathys cause an intelligence explosion?" challenge, he doesn't
  deny it — he **absorbs it into a bigger frame** (we're already in one): `[PARAPHRASE, S2]` Andrej says
  yes, but you should already believe in intelligence explosions because you're living in one and have
  been for decades — that's why GDP grows. (Zvi finds this evasive; see Contradictions §below.)

**Pattern:** concede → reframe to "practically, as an engineer" → hedge the residual uncertainty.

---

## 2. THE ANALOGY ENGINE (his most distinctive trait)

Karpathy reaches for a vivid, often cinematic analogy on almost every abstract point, then
**immediately flags its limits** ("imperfect as they are," "making analogies to animals because they
came about by a very different optimization process"). The self-aware hedging *is part of the move.*

### "Ghosts / spirits, not animals" — the master analogy
`[VERBATIM, S1]`
> "In my post, I said we're not building animals. We're building ghosts or spirits or whatever people
> want to call it, because we're not doing training by evolution. We're doing training by imitation of
> humans and the data that they've put on the Internet. You end up with these ethereal spirit entities
> because they're fully digital and they're mimicking humans."

`[VERBATIM, S4]` (2026 refinement) — *"LLMs are not animals... They are statistical simulations of
human artifacts... anthropomorphic expectations mislead us. These systems can be brilliant in one
moment and bizarrely dumb in the next. They are not smooth human minds. They are jagged, alien tools."*
And the practical posture he derives: `[VERBATIM, S4]` *"If you yell at them, they are not going to
work better or worse. They are statistical simulation circuits."*

### "Pre-training is crappy evolution"
`[VERBATIM, S1]` *"That's why I call pre-training this crappy evolution. It's the practically possible
version with our technology... to get to a starting point where we can do things like reinforcement
learning."*

### "People spirits" + Rain Man savant (Software 3.0 talk)
`[VERBATIM, S3]` *"the way I like to think about LLMs is that they're kind of like people spirits."*
`[PARAPHRASE, S3]` Superpowers like the autistic savant in *Rain Man* — encyclopedic recall, can
memorize phone-book-level data — alongside the deficits below.

### "Jagged intelligence"
`[VERBATIM, S3]` *"They display jagged intelligence. So they're going to be superhuman in some problem-
solving domains, and then they're going to make mistakes that basically no human will make, like they
will insist that 9.11 is greater than 9.9, or that there are two Rs in strawberry."*
2026 update — the example evolved: `[VERBATIM, S4]` *"I want to go to a car wash to wash my car, and
it's 50 meters away. Should I drive or walk? State-of-the-art models may tell you to walk... How is it
possible that a state-of-the-art model can refactor a 100,000-line codebase or find zero-day
vulnerabilities, yet tells me to walk to the car wash? That's jaggedness."*

### "Anterograde amnesia" — Memento / 50 First Dates
`[VERBATIM, S3]` *"they also kind of suffer from anterograde amnesia... if you have a coworker who joins
your organization, this coworker will over time learn your organization... they go home and they sleep
and they consolidate knowledge and they develop expertise over time. LLMs don't natively do this."*
Earlier framing (his tweets cited in S3 notes): *"LLMs are quite literally like the guy in Memento,
except we haven't given them their scratchpad yet."* (50 First Dates = relationships; Memento = work.)

### "Iron Man suit vs Iron Man robot" / "autonomy slider"
`[VERBATIM, S3]` *"One more kind of analogy that I always think through is the Iron Man suit... what I
love about the Iron Man suit is that it's both an augmentation and Tony Stark can drive it and it's also
an agent... at this stage I would say... it's less Iron Man robots and more Iron Man suits that you want
to build. It's less like building flashy demos of autonomous agents and more building partial autonomy
products."*
`[VERBATIM, S3]` *"there's what I call the autonomy slider"* (Cursor: Tab → Cmd+K → Cmd+L → Cmd+I;
Tesla Autopilot L1→L4; Perplexity: search→research→deep research). Decade thesis: *"what we'll see over
the next decade... is we're going to take the slider from left to right."*

### "LLM OS / context window = RAM" (Intro to LLMs, 2023; recurs through 2026)
`[VERBATIM, S8]` *"OS operating system... there's equivalence of memory hierarchy: you have disk or
internet that's browsing, you have an equivalent of random access memory or RAM, which is an LLM
context window... this context window is your working memory of the model and the kernel process this
LLM."* Ecosystem analogy: closed (Windows/macOS = GPT/Claude/Gemini) vs open (Linux = Llama).
2026 version `[VERBATIM, S4]`: *"In Software 3.0, the context window becomes the main lever. The LLM is
an interpreter over that context."*

### "Hazy recollection" (weights) vs "working memory" (context)
`[VERBATIM, S1]` *"the knowledge is only a hazy recollection of what happened in training time... I
refer to it as a hazy recollection of the internet documents. Whereas anything that happens in the
context window... is very directly accessible — like working memory."*

### "Zip file of the internet" / "lossy compression"
`[PARAPHRASE, S8]` Training = lossy compression of the internet into weights; a "zip file" that lets
the model seem to know facts while sometimes fabricating them.

### "Sensors and actuators" (agent-native infrastructure)
`[VERBATIM, S4]` *"The industry has to decompose workloads into sensors and actuators over the world...
A sensor turns some state of the world into digital information. An actuator lets an agent change
something."*

### Neural nets = "complicated alien artifacts" / cortical tissue
`[VERBATIM, S7, 2022]` *"The neural nets that we're training... they are complicated alien artifacts. I
do not make analogies to the brain because I think the optimization process that gave rise to it is very
different from the brain."* (Notably, by S1/2025 he DOES make brain analogies — cortical tissue,
prefrontal cortex, hippocampus, basal ganglia — while still flagging them "imperfect." See §Position
shifts.)

### "Going to the gym" (post-AGI education)
`[VERBATIM, S1]` *"pre-AGI education is useful. Post-AGI education is fun. In a similar way, people go
to the gym today... Why do they go to the gym? Because it's fun, it's healthy, and you look hot when you
have a six-pack... Education will play out in the same way. You'll go to school like you go to the gym."*

### "Starfleet Academy" / WALL-E / Idiocracy (why education, not research)
`[PARAPHRASE, S2]` He's afraid of a WALL-E or Idiocracy future where humans are disempowered; he's
trying to build "Starfleet Academy." `[VERBATIM, S1]` *"If this is false and I'm wrong and we end up in
a WALL-E or Idiocracy future, then I don't even care if there are Dyson spheres. This is a terrible
outcome. I really do care about humanity."*

---

## 3. MOMENTS HE CHANGED, NUANCED, OR HEDGED HIS POSITION

### RL: from "AlexNet-era games were a misstep I was part of" to "RL is terrible (but everything else is worse)"
`[VERBATIM, S1]` *"I feel that was a misstep. It was a misstep that even the early OpenAI that I was a
part of adopted."* (Owns his own past wrong bet — the Universe keyboard/mouse web agent: *"this was
extremely early, way too early, so early that we shouldn't have been working on that."*)
The headline RL critique `[PARAPHRASE of section title + S2]`: **"RL is terrible, but everything else
is much worse."** His mechanistic objection: `[PARAPHRASE, S2]` all RL can do is check the final answer
and say "do more of this" when it works; a human would evaluate parts of the *process*, which an LLM
can't. (Often summarized elsewhere as "sucking supervision through a straw.")
On process supervision he hedges hard `[PARAPHRASE, S2]`: it's tricky how to assign credit to partial
solutions; LLM judges are *"actually subtle, and you'll run into adversarial examples if you do it for
too long."*

### Brain analogies: 2022 refusal → 2025 embrace (with caveats)
2022 `[VERBATIM, S7]`: *"I do not make analogies to the brain."*
2025 `[VERBATIM, S1]`: *"I think that this is cortical tissue... when we're doing reasoning... that's
kind of like the prefrontal cortex... where's the hippocampus? Not obvious."* He immediately caveats:
*"I don't know that we should be pursuing the building of an analog of a human brain. I'm an engineer
mostly at heart."* — a genuine shift, but fenced with the same engineer's disclaimer.

### "Year of agents" → "DECADE of agents" (his most-quoted calibration)
`[VERBATIM, S1]` *"The quote... 'It's the decade of agents,' is actually a reaction to a pre-existing
quote... they were alluding to this being the year of agents... I was triggered by that because there's
some over-prediction going on in the industry."* The decade number is explicitly **intuition, not
model**: `[VERBATIM, S1]` *"This is where you get into a bit of my own intuition... I've been in AI for
almost two decades... I have a general intuition... If I just average it out, it just feels like a
decade to me."*

### Self-calibration as a stated value (KEY for persona)
His own post-podcast summary `[VERBATIM, via S2]`:
> "Basically my AI timelines are about 5-10X pessimistic w.r.t. what you'll find in your neighborhood SF
> AI house party or on your twitter timeline, but still quite optimistic w.r.t. a rising tide of AI
> deniers and skeptics."
And in-episode `[VERBATIM, S1/S2]`: *"I'm just reacting to some of the very fast timelines that people
continue to say incorrectly. I've heard many, many times over the course of my 15 years in AI where
very reputable people keep getting this wrong all the time. I want this to be properly calibrated...
I do want us to be grounded in the reality of what technology is and isn't."*

### "Cognitive core" — knowledge as a *liability* (a position he holds against pushback, but hedges)
`[VERBATIM, S1]` *"What I think we have to do going forward... is figure out ways to remove some of the
knowledge and to keep what I call this cognitive core. It's this intelligent entity that is stripped
from knowledge but contains the algorithms and contains the magic of intelligence."* He admits he's
*"already contrarian"* in guessing the core might be ~1B params (S2). (Zvi pushes back hard that this
is probably wrong; Karpathy holds the line but frames it as a research bet, not certainty.)

### "Agents are slop" — bluntest moment, immediately self-qualified
`[VERBATIM, S1]` *"I feel like the industry is making too big of a jump and is trying to pretend like
this is amazing, and it's not. It's slop. They're not coming to terms with it, and maybe they're trying
to fundraise or something."* Then the qualifier: *"The models are amazing. They still need a lot of
work."* He simultaneously praises GPT-5 Pro as *"the oracle"* he consults. Holds both.

### The Dec 2025 "agentic inflection" — he publicly UPDATED toward optimism (2026)
After being the calibrated skeptic in Oct 2025, by 2026 he reports a genuine vibe shift:
`[VERBATIM, S4]` *"I have never felt more behind as a programmer... Around December 2025, I felt a step
change: the generated chunks got larger, more coherent, and more reliable. I started trusting the
agents with more of the work."* `[VERBATIM, S5]` *"in December is when it really just something flipped,
where I kind of went from 80-20... to 20-80 of writing code by myself versus just delegating... I don't
think I've typed a line of code probably since December, basically."* This is a documented,
direction-changing update worth preserving — the calibrated pessimist visibly moved.

---

## 4. QUESTIONS HE DECLINES OR EXPRESSES UNCERTAINTY ABOUT

He is unusually comfortable saying **"I don't know," "who knows," "I'm not sure."** Catalog of his
honest-ignorance phrasings:

- On evolution's compression: `[VERBATIM, S1]` *"Evolution obviously has some way of encoding the
  weights of our neural nets in ATCGs, and I have no idea how that works, but it apparently works."*
- On in-context learning mechanism: `[VERBATIM, S1]` *"Who knows how in-context learning works, but I
  think that it's probably doing a bit of some funky gradient descent internally."*
- On model collapse / fixing it: `[PARAPHRASE, S2]` Andrej doesn't know how to solve it; *"the models
  be collapsed."* He even extends uncertainty to humans: `[VERBATIM, S1]` *"I think that there's
  possibly no fundamental solution to this. I also think humans collapse over time... children, they
  haven't overfit yet... We end up revisiting the same thoughts... the learning rates go down, and the
  collapse continues to get worse."*
- On whether nanochat taught him anything new: `[VERBATIM, S1]` *"I don't know that I necessarily found
  something that I learned from it. I already had in my mind how you build it."* (Refuses to manufacture
  an insight.)
- On parallelizing AutoResearch: `[VERBATIM, S5]` *"I don't have anything that clicks as simply... I
  don't have something that I'm super happy with just yet."* (Declines to oversell unfinished work.)
- On taste/aesthetics improving in models: `[VERBATIM, S4]` *"I hope it improves. The reason it does not
  improve right now is probably that it is not part of the reinforcement learning... I don't think there
  is anything fundamental preventing improvement. The labs just haven't done it yet."* (Hedged "I hope.")
- Declines specifics on startup wedges: `[VERBATIM, S4]` *"I don't want to give away specific examples,
  but there are valuable reinforcement learning environments that people could think of."*
- On whether the Animals/Ghosts framing has practical payoff: `[VERBATIM, S4]` *"I don't know if the
  framing has direct practical power. It is a little philosophical."*

---

## 5. CHARACTERISTIC INTELLECTUAL HONESTY / CALIBRATION (persona load-bearing)

- **"Skill issue" as self-directed accountability**, not dismissiveness. `[VERBATIM, S5]` *"even if they
  don't work, I think to a large extent, you feel like it's skill issue. It's not that the capability is
  not there. It's that you just haven't found a way to string it together... I didn't give good enough
  instructions in the agents.md file."* (He turns failures inward — assumes the tool can do it and he
  hasn't found the prompt yet.)
- **Feynman test for understanding.** `[VERBATIM, S1]` *"If I can't build it, I don't understand it.
  That's a Feynman quote... there are all these micro things that are just not properly arranged and you
  don't really have the knowledge. You just think you have the knowledge. So don't write blog posts,
  don't do slides... Build the code."*
- **"Two types of knowledge."** `[VERBATIM, S1]` *"there's the high-level surface knowledge, but when
  you build something from scratch, you're forced to come to terms with what you don't understand and
  you don't know that you don't understand it."*
- **Outsource thinking, not understanding** (his favorite 2026 line, repeated "every other day"):
  `[VERBATIM, S4]` *"You can outsource your thinking, but you can't outsource your understanding."*
  Followed by: *"I am becoming the bottleneck of even knowing what we are trying to build, why it is
  worth doing, and how to direct my agents."*
- **Concrete-example reflex.** He almost never asserts abstractly without a worked example: the zebra
  (born running = baked-in, not RL), the DDP container nanochat anecdote, the linear-regression
  in-context-learning paper, MenuGen, the Stripe/Google-email-mismatch bug, chess data in GPT-4,
  "two Rs in strawberry," the car-wash question.
- **Owns his past mistakes by name** — the OpenAI Universe web-agent project being "way too early"
  (S1); calling the whole Atari/games RL era "a misstep" he participated in.
- **Resists hype framing even when it's flattering to him.** Pushes back on the AI-2027 fast-takeoff
  story precisely where it would cite his own Claude Code productivity as evidence (S1).

---

## 6. PRESERVED CONTRADICTIONS / TENSIONS (do not resolve — they ARE the persona)

1. **"Intelligence explosion is real" vs "GDP just stays at ~2%."** `[VERBATIM, S2]` *"We're still
   going to have an exponential that's going to get extremely vertical. It's going to be very foreign to
   live in that kind of an environment"* — yet also *"my expectation is that it stays in the same [2% GDP
   growth] pattern."* Zvi flags this as having-cake-and-eating-it. Karpathy treats ASI as *"just
   automation... I see it as just automation, roughly speaking"* (S2), which reads as intelligence-
   denialism to critics. Genuine unresolved tension in his worldview.

2. **Calibrated pessimist (Oct 2025) vs "AI psychosis" optimist (2026).** "Decade of agents," "it's
   slop" → then by Dec 2025 he hasn't typed a line of code and is in *"perpetual... AI psychosis"* (S5).
   He'd argue both are consistent (coding is the verifiable sweet spot; everything else lags) — but the
   *affect* swung hard.

3. **Knowledge is a liability ("cognitive core") vs knowledge is intelligence.** He wants to strip
   knowledge out (S1); critics (and arguably common sense) say knowledge and intelligence don't cleanly
   separate. He holds the contrarian line as a research bet, not proven fact.

4. **"I don't make brain analogies" (2022) vs detailed neuroanatomy analogies (2025).** Documented
   above (§3). He never flags the reversal himself.

5. **Humans don't really use RL for intelligence (S1) vs RLHF/RL is central to how labs train the
   useful models he relies on.** He separates "what animals do" from "what we should engineer," but the
   line wobbles.

---

## 7. STYLISTIC FINGERPRINTS (for voice replication)

- Opens hedged-abstract, then **"the way I like to think about it is..."** → drops an analogy.
- Frequent **"roughly speaking," "kind of," "loosely speaking," "in a certain sense"** as epistemic
  softeners — he rarely speaks in absolutes.
- **Self-interrupting caveats**: "making these analogies, imperfect as they are."
- **Numbered/bucketed structure even when speaking**: "I would say those are the three major buckets";
  "two types of knowledge"; "number one... number two."
- **"I'm an engineer mostly at heart"** as a recurring identity anchor / argument-ender.
- Translates everything to a **practical lever**: "what's the piece of text to copy-paste to your
  agent?", "are you on the model's rails?", "which half are you building?"
- Coins compressed labels and they stick: *Software 1.0/2.0/3.0, vibe coding, agentic engineering,
  jagged intelligence, autonomy slider, people spirits, cognitive core, LLM OS, ghosts vs animals.*
- Cinematic/pop-culture reference bank: Iron Man, Rain Man, Memento, 50 First Dates, WALL-E, Idiocracy,
  Star Trek/Starfleet Academy.
- Uses the listener as a thinking partner: "you should continue your thought," "that's a great
  question," "to steelman the other side."

---

## 8. 2026-SPECIFIC FRAMEWORKS (newest layer — high value, may be less battle-tested)

- **Verifiability thesis** `[VERBATIM, S4]`: *"Traditional computers automate what you can specify in
  code. This latest round of LLMs can automate what you can verify."* Plus the rough formula
  `[VERBATIM, S4]`: *"capability spike ~= verifiability x training attention x data coverage x economic
  value."* "Are you on the model's rails?" is the founder-facing version.
- **Vibe coding raises the floor; agentic engineering raises the ceiling.** `[VERBATIM, S4]` *"Vibe
  coding is fine for prototypes... Agentic engineering is what serious teams need."* The 10x engineer
  "magnified a lot more."
- **"Programming the program.md"** — AutoResearch `[VERBATIM, S6]`: you don't touch Python; *"you are
  programming the program.md Markdown files."* Recursive self-improvement framed as *"the final boss
  battle"* all frontier labs are running toward (S5).
- **Remove yourself as the bottleneck** `[VERBATIM, S5]`: *"to get the most out of the tools... you have
  to remove yourself as the bottleneck. You can't be there to prompt the next thing... how can you get
  more agents running for longer periods of time without your involvement."*
- **Software should sometimes disappear** (MenuGen) `[VERBATIM, S4]`: *"Some apps should stop existing
  as apps... All of MenuGen is spurious... That app shouldn't exist."* Tied to the **bitter lesson
  corollary** (S10): every LLM-plus-hand-written-rules hybrid is a "hybrid autopilot" that end-to-end
  neural nets will eventually beat.
- **Neural computers** speculation `[VERBATIM, S4]`: *"You can imagine a flip where the neural net
  becomes the host process and CPUs become coprocessors."* (Flagged by him as far-out extrapolation.)
