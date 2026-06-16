# Andrej Karpathy — Writings & Systematic Long-Form Thinking

Research dossier for persona-distillation. Compiled May 2026.

**Sourcing convention**
- **[FIRST-HAND]** = text Karpathy himself wrote/published (blog, gist, course page, tweet, talk transcript he approved).
- **[SECOND-HAND]** = someone else summarizing/paraphrasing him. Treated as weaker; flagged when it is the only source for a claim.
- Source blacklist honored: no Zhihu, no WeChat, no Baidu Baike.

A note on the Software 3.0 talk transcript (donnamagi.com): it is a **community transcript of a noisy live recording**, and Karpathy himself said it contains errors and that "the talk will be deprecated." So it is first-hand in *substance/ideas* but garbled in *wording* — quote it for concepts, not for exact phrasing. Where the transcript reads as obvious ASR garble (e.g. "Andrew" = Andrew Ng; "CAPs" = capex; "Fungi" = an LLM lab; "Mavic" = Manim by 3blue1brown; "play" = click), I note it.

---

## 1. Primary sources located (all FIRST-HAND unless noted)

| Title | Date | URL | Credibility |
|---|---|---|---|
| Software 2.0 | 2017-11-11 | https://karpathy.medium.com/software-2-0-a64152b37c35 | FIRST-HAND (Medium returned 403 to fetch; verified via quoted excerpts in second-hand source frenxt.com) |
| The Unreasonable Effectiveness of Recurrent Neural Networks | 2015-05-21 | http://karpathy.github.io/2015/05/21/rnn-effectiveness/ | FIRST-HAND |
| Yes you should understand backprop | 2016 | https://medium.com/@karpathy/yes-you-should-understand-backprop-e2f06eab496b | FIRST-HAND (referenced by him; not fetched directly) |
| A Recipe for Training Neural Networks | 2019-04-25 | http://karpathy.github.io/2019/04/25/recipe/ | FIRST-HAND (full text retrieved) |
| Deep Neural Nets: 33 years ago and 33 years from now | 2022-03-14 | http://karpathy.github.io/2022/03/14/lecun1989/ | FIRST-HAND (full text retrieved) |
| Power to the people: How LLMs flip the script on technology diffusion | 2025-04-07 | https://karpathy.bearblog.dev/power-to-the-people/ | FIRST-HAND (full text retrieved) |
| Software Is Changing (Again) — YC/AI Startup School "Software 3.0" talk | 2025-06-17 | transcript: https://www.donnamagi.com/articles/karpathy-yc-talk · official video: https://www.youtube.com/watch?v=LCEmiRjPEtQ | FIRST-HAND ideas / SECOND-HAND wording (community transcript, ASR-noisy) |
| 2025 LLM Year in Review | 2025-12-19 | https://karpathy.bearblog.dev/year-in-review-2025/ | FIRST-HAND (full text retrieved) — single richest source for his coined terms |
| microgpt (art project guide) | 2026-02-12 | http://karpathy.github.io/2026/02/12/microgpt/ · gist: https://gist.github.com/karpathy/8627fe009c40f57531cb18360106ce95 | FIRST-HAND (full text retrieved) |
| Neural Networks: Zero to Hero (course) | ongoing | https://karpathy.ai/zero-to-hero.html | FIRST-HAND |
| Books (sci-fi reading list w/ his annotations) | ongoing | https://karpathy.ai/books.html | FIRST-HAND |
| Referenced-but-not-fetched first-hand essays: "Animals vs. Ghosts", "Verifiability", "The Space of Minds", "vibe coding menugen" | 2025 | https://karpathy.bearblog.dev/ | FIRST-HAND (linked by him in Year-in-Review) |
| Dwarkesh Patel interview (origin of "march of nines", "decade of agents") | 2025 | https://www.dwarkesh.com/p/andrej-karpathy | FIRST-HAND audio / SECOND-HAND for the paraphrased quotes used below |
| nanochat repo | 2025-10 | https://github.com/karpathy/nanochat | FIRST-HAND |

---

## 2. Self-coined terminology — precise definitions

Each term below is given **in his own framing** where a first-hand quote exists.

### Software 2.0 [FIRST-HAND, 2017]
Neural network *weights* as a new kind of program. Not hand-written; "compiled" from data by an optimizer.
> "Neural networks are not just another classifier, they represent the beginning of a fundamental shift in how we develop software. They are Software 2.0." (quoted from the essay)

Software 1.0 = "explicit instructions to the computer written by a programmer" (Python, C++). Software 2.0 = the programmer curates the **dataset** and runs an optimizer; the net writes the function. His stack mapping: **datasets are the new source code, weights are the new binary, gradient descent is the new compiler, Hugging Face is the GitHub of 2.0** (the Hugging Face / "Git for 2.0" framing is from the 2025 talk, retrofitted onto the 2017 idea).

### Software 3.0 [FIRST-HAND ideas, 2025 talk]
LLMs that are **programmable in natural language (English)**. "It's a new kind of computer ... worth giving it the designation of a Software 3.0." Prompts are programs; English is the programming language. He frames all three as coexisting, not replacing: "if you're entering the industry, it's a very good idea to be fluent in all of them."

### LLM OS [FIRST-HAND ideas, 2023 "LLM OS" framing + 2025 talk]
LLMs are best analogized not to electricity/utilities or to fabs (capex), but to **operating systems**. The LLM ≈ CPU; the context window ≈ RAM/working memory; the model "orchestrates memory and compute for problem solving" using tools. Ecosystem mirrors OS history: a few closed providers (≈ Windows/macOS) plus an open alternative (≈ Linux). He layers on a **"circa 1960s computing"** analogy: compute is expensive, so LLMs are centralized in the cloud and we time-share them as "thin clients"; the personal-computing revolution for LLMs "hasn't happened yet" (notes Mac minis as an early local-inference hint). And: talking to an LLM in text feels like "talking to an operating system through the terminal" — the **GUI for LLMs has not been invented yet**.

### Autonomy slider [FIRST-HAND, 2025 talk + Year-in-Review]
A product should expose a **dial of how much it does autonomously vs. under human control**, rather than being all-or-nothing. Canonical example: Cursor's escalation (tab-complete → Cmd+K change a span → Cmd+L change a file → Cmd+I agent mode), and "quick search → research → deep research." Rooted explicitly in his Tesla Autopilot experience: build the slider, then "slide that autonomy slider ... more autonomous over time."

### Partial autonomy apps [FIRST-HAND, 2025 talk]
The product pattern he advocates *now*. An LLM app that (1) does **context management/engineering**, (2) **orchestrates multiple LLM calls** under the hood, (3) provides an **app-specific GUI** so the human can audit fast, (4) exposes an **autonomy slider**. The strategic imperative: **make the human's generate→verify loop as fast as possible** (GUIs exploit our visual cortex; text is slow to audit) and **keep the AI "on a leash"** (small incremental diffs, not 1000-line dumps you can't review).

### Context engineering [FIRST-HAND, Year-in-Review 2025]
What LLM apps do: managing what goes into the context window, and "orchestrate multiple LLM calls under the hood strung into increasingly more complex DAGs, carefully balancing performance and cost tradeoffs." Context window is "working memory ... you have to program quite directly" because LLMs don't consolidate knowledge overnight like a human coworker.

### Vibe coding [FIRST-HAND, coined in a Feb 2025 tweet; expanded in Year-in-Review]
> "There's a new kind of coding I call 'vibe coding', where you fully give in to the vibes, embrace exponentials, and forget that the code even exists." (tweet, https://x.com/karpathy/status/1886192184808149383)

In Year-in-Review he adds: "2025 is the year that AI crossed a capability threshold necessary to build all kinds of impressive programs simply via English, forgetting that the code even exists." It "raises the floor" — anyone can program — and also lets pros write software "that would otherwise never be written." Key downstream idea: **code becomes "free, ephemeral, malleable, discardable after single use."** He says he "coined the term ... totally oblivious to how far it would go."
- **NOTE / nuance, not contradiction:** he is the booster *and* a critic. Second-hand 2026 reporting (techloy, Fortune) has him calling raw AI-generated code "awkward" and "gross" and signaling a shift toward **"agentic engineering"** as the next stage past vibe coding. This is consistent with his "keep the AI on a leash" line — vibe coding for throwaway demos, more discipline for real software. Treat the strong "vibe coding is obsolete" framing as second-hand headline spin.

### Jagged intelligence [FIRST-HAND, Year-in-Review 2025]
LLMs are "at the same time a genius polymath and a confused and cognitively challenged grade schooler." They "spike" in capability near verifiable domains (math, code) because of RLVR, and fail at trivially easy things (9.11 > 9.9; two r's in "strawberry"). He stresses **human intelligence is also jagged, just differently**.

### Ghosts vs. Animals [FIRST-HAND, Year-in-Review 2025; full essay "Animals vs. Ghosts"]
A framing for *what kind of mind an LLM is*: "We're not 'evolving/growing animals', we are 'summoning ghosts'." Different architecture, data, training algorithm, and **optimization pressure** (humans optimized for tribal survival; LLMs optimized to imitate internet text + collect verifiable rewards + win LM Arena upvotes) → a genuinely alien entity that should not be reasoned about through an animal/biological lens. He calls them "little spirits" / "people spirits" with an emergent, human-like-but-deficient psychology (great memory à la Rain Man; hallucination; "anterograde amnesia" — context resets like *Memento* / *50 First Dates*; prompt-injection security holes).

### The march of nines [FIRST-HAND ideas via Dwarkesh interview; SECOND-HAND for exact quotes]
Going from a demo to a reliable product is a logarithmic slog: each additional "nine" of reliability (90% → 99% → 99.9% → ...) costs roughly **the same amount of work as everything before it**. Paraphrased from the Dwarkesh interview: "every single nine is the same amount of work." Drawn from 5 years on Tesla Autopilot — they did "two or three nines" with many more ahead. Generalizes to software broadly ("a single mistake ... a code path that's going to break ... a zero-day"). Feeds his **"decade of agents," not "year of agents"** stance: "when I see things like 'this is the year of agents,' I get very concerned ... this is the *decade* of agents."

### Network-to-product gap [FIRST-HAND, 2025 talk]
Related to march-of-nines. "If anything works, you can make demos. But in many cases, lots of things must work" — especially in high-reliability domains. The distance between a working neural net and a shipped product is large and underappreciated.

### RLVR — Reinforcement Learning from Verifiable Rewards [FIRST-HAND, Year-in-Review 2025]
Not coined by him, but he canonized the framing as 2025's defining "paradigm change." A new training stage after pretraining/SFT/RLHF: train against **automatically verifiable, non-gameable rewards** (math/code puzzles). Because the reward is objective, you can optimize far longer than the "thin" SFT/RLHF stages, and the model "spontaneously develops strategies that look like reasoning." Gave a new test-time-compute scaling knob ("thinking time"). o1 = first demo, o3 = the felt inflection point.

### "Power to the people" / inverted technology diffusion [FIRST-HAND, 2025 essay]
LLMs reverse the normal top-down diffusion of transformative tech (military → corporate → consumer). They benefit **individuals most**, corporations/governments least, because LLMs offer "quasi-expert" breadth-but-shallowness: a huge multiplier for an individual (expert in ≤1 thing), but only a marginal boost for an org that already concentrates many experts. Caveat he flags himself: this holds **only while money can't buy meaningfully better intelligence** ("Bill Gates talks to GPT-4o just like you do"); if dynamic range opens up (train/test-time scaling, ensembles) the elite could split away again — "your child tutored by GPT-6 mini, theirs by GPT-8-pro-max-high."

### LLM GUI / "cognitive core" / "internet of agents" [FIRST-HAND, Year-in-Review 2025]
He expects the LLM era to recapitulate computing history: equivalents of personal computing, **microcontrollers ("cognitive core")**, and an **internet of agents**. People dislike reading text ("slow and effortful"); LLMs should output visually/spatially (images, infographics, slides) — Google's "nano banana" image model is an early hint of the LLM GUI, valuable because text+image+world-knowledge are "all tangled up in the model weights."

### "AI that lives on your computer" [FIRST-HAND, Year-in-Review 2025]
On Claude Code: the first convincing **LLM Agent** ("in a loopy way strings together tool use and reasoning for extended problem solving"). His thesis is that what matters is not cloud-vs-local compute but that the agent runs against your **already-booted-up computer: its installation, context, data, secrets, config, low-latency interaction**. He argues OpenAI got the *order of precedence* wrong by going cloud-container-first; Anthropic's `localhost` CLI form factor — "a little spirit/ghost that 'lives' on your computer" — was correct.

---

## 3. Core theses that recur 3+ times (these are real, stable beliefs)

1. **Build it from scratch to truly understand it.** micrograd → makemore → nanoGPT → nanochat → microgpt, plus the lecun1989 reproduction and Zero-to-Hero. "A decade-long obsession to simplify LLMs to their bare essentials." (microgpt) — see §4.

2. **Abstractions in deep learning are *leaky*; you cannot treat NN training as plug-and-play.** [Recipe, 2019] "Neural net training is a leaky abstraction" and "Neural net training fails silently." Echoes "Yes you should understand backprop." Corollary belief: **"a 'fast and furious' approach to training neural networks does not work and only leads to suffering"**; the winning traits are "patience and attention to detail."

3. **The macro shape of deep learning barely changes; scale (data + compute + model size) is the real lever.** [lecun1989, 2022] "Not much has changed in 33 years on the macro level ... except it is smaller." Extrapolates that 2055 nets are "basically the same ... except bigger," and that training-from-scratch-per-task is becoming obsolete in favor of foundation models + finetuning/prompting. Recurs in microgpt's "everything else is just efficiency" and Year-in-Review's RLVR scaling discussion.

4. **Software is layering, not being replaced. Be fluent in 1.0 / 2.0 / 3.0.** The Tesla Autopilot story (C++ "Software 1.0" progressively eaten by neural nets) is his recurring proof. [Software 2.0; 2025 talk]

5. **Don't aim for full autonomy yet; build human-in-the-loop partial-autonomy products with a fast verify loop and an autonomy slider.** [2025 talk; Year-in-Review] "Keep the AI on a leash." Iron Man *suit* (augmentation) over Iron Man *robot* (full agent), for now.

6. **Reliability is the hard part; demos are easy. Expect a decade, not a year.** [march-of-nines, network-to-product gap, Dwarkesh] He is simultaneously bullish and patient: "we will both see rapid and continued progress *and* yet there is a lot of work to be done."

7. **LLMs are an alien intelligence ("ghosts"), simultaneously smarter and dumber than expected; distrust benchmarks.** [Year-in-Review] "Training on the test set is a new art form"; "What does it look like to crush all the benchmarks but still not get AGI?"

8. **Language modeling is the best on-ramp to all of deep learning.** [Zero to Hero] "language models are an excellent place to learn deep learning, even if your intention is to eventually go to other areas like computer vision because most of what you learn will be immediately transferable."

9. **Make everything legible to LLMs/agents (build *for* agents).** [2025 talk] llms.txt, Markdown docs, MCP, GitIngest-style tools; and *change* the docs ("click this button" → an action an agent can take). "There's a new category of consumer and manipulator of digital information."

---

## 4. Stance on building-from-scratch / first-principles pedagogy

This is arguably his strongest and most consistent identity. Evidence, all FIRST-HAND:

- **The "spelled-out", "from scratch, in code" method.** Zero to Hero's tagline: "building neural networks, from scratch, in code. We start with the basics of backpropagation and build up to modern deep neural networks, like GPT." Video titles literally say "spelled-out" and "from scratch, in code, spelled out."

- **Reduce to the irreducible core, then state plainly what is *just efficiency*.** microgpt: "This file contains the full algorithmic content of what is needed ... Everything else is just efficiency. I cannot simplify this any further." His "Real stuff" section explicitly separates *algorithmic essence* (stays the same) from *engineering for scale* (data scale, BPE, tensors/GPUs, RoPE/GQA/MoE, batching, post-training, inference serving) — "None of them alter the core algorithm."

- **Onion-layer progression / one component at a time.** microgpt ships a `build_microgpt.py` gist whose *revisions* add one piece at a time: bigram table → MLP+manual grads → autograd → attention+rmsnorm+residuals → multi-head → Adam. Mirrors the Recipe's rule "**complexify only one at a time**" and "**generalize a special case**" (write the loopy version first, then vectorize).

- **Intuition over formalism.** Explains the chain rule with "if a car travels twice as fast as a bicycle and the bicycle is four times as fast as a walking man, then the car travels 8 times as fast." Uses analogies relentlessly (Q/K/V = "what am I looking for / what do I contain / what do I offer"; "Attention is a token communication mechanism," "Transformer intersperses communication (Attention) with computation (MLP)").

- **Demystify, don't mystify.** microgpt FAQ: "no magic is happening. The model is a big math function." Hallucination is "the same phenomenon" at small and large scale.

- **Cost/cognitive accessibility as a design goal.** nanochat = "The best ChatGPT that $100 can buy"; "you can literally read every line." minGPT "prioritized education"; nanoGPT "prioritizes teeth over education" (his own distinction — he deliberately maintains both a teaching artifact and a working one).

- **Empirical, defensive, paranoid workflow.** The Recipe is the manifesto: become one with the data (hours of manual inspection) → dumb baselines → overfit → regularize → tune → squeeze. Mantras: "fix random seed," "verify loss @ init," "overfit one batch," "visualize just before the net," "**Don't be a hero**" (copy the simplest known-good architecture first), "Adam 3e-4 is safe," "do not trust learning-rate-decay defaults."

---

## 5. Recommended reading / intellectual lineage

### His own sci-fi list [FIRST-HAND, karpathy.ai/books.html]
Stated tastes: "hard sci-fi ... intriguing technical ideas, world-building, future forecasting"; dislikes "literary bloat" and anthropomorphic aliens; "especially enjoy[s] sci-fi that features Artificial Intelligence. I believe AI is the greatest omission from most sci-fi worlds." Top-rated:
- **Ted Chiang — *Stories of Your Life and Others*** and ***Exhalation*** — "Required reading." (favorites: Understand, Story of Your Life, Division by Zero; Exhalation, What's Expected of Us, The Merchant and the Alchemist's Gate)
- **Andy Weir — *The Martian*, *Project Hail Mary*** (latter a favorite alien portrayal)
- **Ramez Naam — *Nexus*** (Neuralink-ish future)
- **Stanislaw Lem — *His Master's Voice*, *Fiasco*, *Solaris*** (interesting aliens)
- **Roger Williams — *The Metamorphosis of Prime Intellect*** (AGI gone mixed)
- **Greg Egan — *Permutation City*** (simulation/artificial life)
- **Carl Sagan — *Contact*; Fred Hoyle — *Black Cloud*; Arthur C. Clarke — *Rendezvous with Rama*; Daniel Keyes — *Flowers for Algernon*; Daniel Suarez — *Daemon***
- **Contrarian takes (reveal his taste boundaries):** dislikes most of *Three-Body Problem* ("a large mass of goo, soulless characters"), *Hyperion*, *Dune* (loves only the world-building/absence-of-AI lore), Iain M. Banks *Player of Games* ("anthropomorphic aliens ... makes me angry"), *Seveneves* ("might die of boredom").

### Non-fiction influence [FIRST-HAND, via search of his recommendations — SECOND-HAND aggregation]
- **Nick Lane — *The Vital Question*** — "easily one of my favorite books ever." (origins of life / bioenergetics). *(Sourced from book-aggregator summaries of his recommendations; treat as SECOND-HAND until a primary quote is found.)*

### Technical/intellectual lineage (papers & people he repeatedly anchors on) [FIRST-HAND]
- **Yann LeCun et al. 1989**, "Backpropagation Applied to Handwritten Zip Code Recognition" — his time-capsule reproduction; "earliest real-world application of a neural net trained end-to-end with backpropagation."
- **"Attention Is All You Need"** (Transformer) and **OpenAI GPT-2/GPT-3** — the targets Zero-to-Hero rebuilds.
- **DeepSeek R1 paper** — cited as the clean public example of RLVR reasoning emergence.
- **Chinchilla scaling laws**, **foundation-models framing** — cited in lecun1989 and microgpt.
- **Andrew Ng** — "AI is the new electricity" framing he engages with (and partly rejects in favor of the OS analogy).
- **3Blue1Brown (Grant Sanderson) / Manim** — his model for visual explanation (the talk's garbled "Mavic"/"Google Brown" = Manim).
- **WaveNet (DeepMind, 2016)** — rebuilt in makemore part 5.

---

## 6. Contradictions / tensions recorded (not smoothed over)

1. **Vibe-coding evangelist vs. vibe-coding skeptic.** He coined and celebrates vibe coding (Year-in-Review, FIRST-HAND) yet 2026 second-hand reporting has him calling AI code "gross/awkward" and pushing past it to "agentic engineering." Reconcilable via his "keep the AI on a leash" / "partial autonomy" principle, but the public framing genuinely swings between hype and caution. The "vibe coding is obsolete" headline is SECOND-HAND spin; his actual position is staged (vibes for throwaway, discipline for production).

2. **Bullish vs. patient — held simultaneously and admittedly "paradoxical."** Year-in-Review (FIRST-HAND): "I simultaneously (and on the surface paradoxically) believe that we will both see rapid and continued progress *and* that yet there is a lot of work to be done." Same tension in the talk: "amazing time to enter the industry" + "decade of agents ... let's be serious here."

3. **"Power to the people" optimism vs. his own elite-split caveat.** The 2025 essay is triumphalist ("Power to the people. Personally, I love it") but he himself flags the failure condition: the moment money buys dramatically better intelligence, the equalizing effect reverses.

4. **"Macro hasn't changed in 33 years" vs. "software changed twice in the last few years."** lecun1989 stresses deep continuity (same backprop+SGD, just bigger); the 2025 talk stresses radical discontinuity (1.0→2.0→3.0). His resolution: the *learning algorithm* is stable; the *programming paradigm / interface* (data, then English) is what shifts.

5. **Benchmarks built much of the field's progress, yet he announces "loss of trust in benchmarks" (2025)** — because verifiable benchmarks are exactly what RLVR can overfit ("training on the test set is a new art form").

6. **Education-first artifacts vs. "teeth" artifacts.** He intentionally keeps both minGPT (education) and nanoGPT ("prioritizes teeth over education") — a deliberate, self-aware split rather than a contradiction.

---

## 7. Voice / style fingerprints (useful for persona distillation)

- Opens by **reducing to first principles**, then names what is *merely* efficiency/engineering.
- **Analogy-driven** (Iron Man suit, Rain Man, *Memento*/*50 First Dates*, 1960s time-sharing, electricity/utilities-vs-OS, car/bicycle/walker for chain rule, "summoning ghosts," "little spirits").
- Coins **sticky, slightly playful terms** ("vibe coding," "march of nines," "don't be a hero," "be a backprop ninja," "may yours be low" re: loss).
- **Emotionally candid about craft**: "it is beautiful 🥹"; "suffering"; "patience and attention to detail."
- **Self-aware about virality and being wrong**: notes he "still has no clue which tweet will go viral," and that talks get "deprecated."
- **Hedged, anti-hype on timelines** ("decade of agents," "let's be serious here") while **bullish on long-run potential** ("don't think the industry has realized anywhere near 10% of their potential").
- Heavy use of **concrete numbers and reproductions** to ground claims (90 seconds vs 3 days; 4,192 params; 100,000,000× more pixel data).
