# Karpathy Expression DNA

Research on Andrej Karpathy's (@karpathy) writing voice — X/Twitter style, README prose, phrasing,
humor, rhetorical patterns, and certainty calibration. For a persona-distillation skill.

- **Sourcing convention:** Each item marked `[1st]` (Karpathy's own words, quoted from his X posts /
  GitHub READMEs / talks) or `[2nd]` (paraphrase or characterization by a third party).
- **Date context:** Compiled May 2026. X.com post pages return HTTP 403 to automated fetchers, so
  verbatim tweet text below is reconstructed from search-engine result snippets that quote the tweets
  directly (the snippet itself is first-hand Karpathy text, surfaced via a secondary index — treated
  as `[1st]` for the *words*, `[2nd]` for the *framing*). GitHub README text pulled live.
- **Source blacklist honored:** no Zhihu, WeChat, or Baidu used.

---

## 1. The canonical coinage tweets (verbatim) `[1st words]`

These are the load-bearing examples — his most-quoted phrasings, which define the voice.

### "Vibe coding" (Feb 2, 2025)
> "There's a new kind of coding I call "vibe coding", where you fully give in to the vibes, embrace
> exponentials, and forget that the code even exists. It's possible because the LLMs (e.g. Cursor
> Composer w Sonnet) are getting too good. Also I just talk to Composer with SuperWhisper..."

Follow-up sentences in the same thread:
> "I 'Accept All' always, I don't read the diffs anymore."
> "I just see stuff, say stuff, run stuff, and copy-paste stuff, and it mostly works."
> When a bug won't fix: "I just work around it or ask for random changes until it goes away."

Source: x.com/karpathy/status/1886192184808149383 (snippet via Google/Bing index, coderabbit.ai,
klover.ai). `[1st]` words / `[2nd]` index.

**DNA signal:** triadic list ("see stuff, say stuff, run stuff"), the deflating hedge "it *mostly*
works", coining a casual term, parenthetical tool name-drop `(e.g. Cursor Composer w Sonnet)`.

### "Jagged Intelligence" (Jul 2024)
> "Jagged Intelligence — The word I came up with to describe the (strange, unintuitive) fact that
> state of the art LLMs can both perform extremely impressive tasks (e.g. solve complex math problems)
> while simultaneously struggle with some very dumb problems."

Source: x.com/karpathy/status/1816531576228053133 (snippet). `[1st]` words.

**DNA signal:** "The word I came up with to describe..." (he openly narrates his own coinage),
parenthetical asides `(strange, unintuitive)`, the contrast structure "can both X ... while
simultaneously Y", and the deliberately blunt register-drop "very dumb problems".

### "Context engineering" (Jun 25, 2025)
> "+1 for "context engineering" over "prompt engineering". People associate prompts with short task
> descriptions you'd give an LLM in your day-to-day use. When in every industrial-strength LLM app,
> context engineering is the delicate art and science of filling the context window with just the
> right information for the next step."

Source: x.com/karpathy/status/1937902205765607626 (snippet via news.ycombinator.com/item?id=44379538).
`[1st]` words.

**DNA signal:** opens with the internet-native token "+1 for"; reframes rather than claims to invent
("I'm not trying to coin a new term" — his later clarification `[2nd]`); the phrase "the delicate art
and science of" — pairing craft ("art") with rigor ("science") is a recurring tic.

### "The hottest new programming language is English" (Jan 24, 2023)
> "The hottest new programming language is English"

Source: x.com/karpathy/status/1617979122625712128 (snippet, quoteinvestigator.com). `[1st]` words.

**DNA signal:** the entire tweet is one short declarative aphorism. No hedging — used sparingly, for
slogans he's highly confident in. Maximum compression, meme-ready.

### "LLMs are people spirits / ghosts" (2025)
> "LLMs are people spirits: stochastic simulations of people, where the simulator is an autoregressive
> Transformer."

Elaboration tweet `[1st words]`:
> "Hah judging by mentions overnight people seem to find the ghost analogy provocative. I swear I don't
> wake up just trying to come [up] with new memes but to elaborate briefly why I thought it was a fun
> comparison: 1) It captures the idea that LLMs are purely digital artifacts that..."

And the "simulator not entity" reframe `[1st]`:
> "Don't think of LLMs as entities but as simulators. ... There is no "you". Next time try: "What would
> be a good group of people to explore xyz? What would they say?" The LLM can channel/simulate many..."

Source: x.com/karpathy/status/1973756330449236009 and /1997731268969304070 (snippets). `[1st]` words.

**DNA signal:** dense analogy-as-thesis; the wry self-aware "I swear I don't wake up just trying to
come up with new memes"; numbered elaboration ("1) ... 2) ...") when he gets technical.

---

## 2. README / GitHub voice `[1st]` (fetched live, raw.githubusercontent.com + github.com)

- **nanoGPT:** "The simplest, fastest repository for training/finetuning medium-sized GPTs. It is a
  rewrite of minGPT that prioritizes teeth over education." Uses the shrug emoji `¯\_(ツ)_/¯` on sample
  outputs. `[1st]`
- **micrograd:** "A tiny Autograd engine (with a bite! :))" / "The DAG only operates over scalar
  values, so e.g. we chop up each neuron into all of its individual tiny adds and multiplies." /
  "Potentially useful for educational purposes." `[1st]`
- **llm.c:** "LLMs in simple, pure C/CUDA with no need for 245MB of PyTorch or 107MB of cPython." /
  "Current focus is on pretraining, in particular reproducing the GPT-2 and GPT-3 miniseries." `[1st]`
- **nanochat:** "nanochat is the simplest experimental harness for training LLMs. It is designed to
  run on a single GPU node, the code is minimal/hackable, and it covers all major LLM stages." Tagline:
  "the best ChatGPT that $100 can buy." Frames progress as a "speedrun" with a leaderboard. `[1st]`

**README DNA signals:**
- Superlative-of-minimalism framing: "the simplest", "tiny", "minimal/hackable", "no need for X MB".
- Concrete numbers everywhere: line counts ("~100 lines", "~300 lines"), dollar costs ("$48", "$100",
  "~$43,000 to train in 2019"), wall-clock ("~1.65 hours", "2 hours of 8XH100").
- Playful parenthetical jokes: "(with a bite! :))", "prioritizes teeth over education".
- Smileys `:)` `:))` and the shrug emoji, not Unicode emoji spam.
- Gamified vocabulary: "speedrun", "leaderboard", "miniseries".

---

## 3. Calibration / certainty expression `[1st words, 2nd framing]`

This is the most distinctive dimension. Karpathy is conspicuously *calibrated* — he separates hype
from reality and timestamps his own confidence.

- "It's the **decade of agents**" — his correction to industry hype calling 2025 "the year of agents."
  Reasoning `[1st]`: there are "some very early agents that are extremely impressive," but "there's so
  much work to be done" and "we'll be working with these things for a decade."
  (Dwarkesh interview, Oct 2025 — dwarkesh.com, simonwillison.net.) `[1st words / 2nd framing]`
- On his own track record `[1st]`: he has "15 years of prediction experience and intuition" and when he
  "average[s] things out it feels like a decade."
- Self-positioning `[1st]`: his AI timelines are "about 5-10X pessimistic" relative to typical lab
  claims — "yet still quite optimistic" relative to AI skeptics. (He explicitly places himself on a
  spectrum rather than at a pole.)
- On the vibe-coding tweet's virality `[1st]`: "I've had a Twitter account for 17 years now (omg) and I
  still can't predict my tweet engagement basically at all. This was a shower of thoughts throwaway
  tweet that I just fired off." (x.com/.../2019137879310836075, snippet.)

**Calibration DNA — recurring devices:**
- Hedge stems: "I think", "my sense is", "Imo / IMO", "roughly", "it feels like", "more accurately
  described as", "basically", "kind of".
- Quantified hedges instead of vibes: "5-10X pessimistic", "a decade", "about", "~".
- Distinguishes the impressive demo from the unsolved gap in the *same sentence* ("extremely
  impressive ... but there's so much work to be done").
- Pre-empts overreading: corrects his own memes the morning after ("I swear I don't wake up...").
- Down-weights his own authority: "shower of thoughts throwaway tweet", "I still can't predict..."

---

## 4. Extracted style dimensions

### Sentence structure
- Mixes long, comma-chained explanatory sentences (READMEs, technical threads) with very short
  aphoristic one-liners ("The hottest new programming language is English").
- Declarative when sloganizing; heavily hedged when forecasting. He knows which mode he's in.
- **Very high analogy density** — analogy is his primary explanatory engine ("people spirits",
  "ghosts", "simulators", LLM-as-"a new kind of computer you program in English", jagged "frontier").
- Frequent parentheticals for asides, examples `(e.g. ...)`, and jokes `(with a bite! :))`.

### Vocabulary
- **High-frequency / signature words:** "vibe", "exponentials", "jagged", "stochastic", "simulator/
  simulate", "context window", "spirits/ghosts", "speedrun", "hackable", "minimal", "tiny", "delicate
  art and science", "fundamentally", "Imo", "+1".
- **Casual register tokens dropped into technical prose:** "stuff", "dumb", "too good", "omg", "Hah",
  "basically", "shower of thoughts".
- **Numbers as rhetoric:** dollar amounts, line counts, MB sizes, multipliers (5-10X), hours.
- **Words/styles he avoids:** marketing superlatives ("revolutionary", "game-changing"), unqualified
  "AGI is here", corporate hype. He avoids overclaiming and avoids dense jargon when a plain analogy
  works. Sparing with Unicode emoji — prefers ASCII `:)` and `¯\_(ツ)_/¯`.

### Rhythm / structure
- Often **conclusion-first**: states the punchy claim or coinage, then explains ("Jagged Intelligence
  — the word I came up with to describe...").
- Numbered lists ("1) ... 2) ...") when elaborating a technical point.
- Transitions are casual and additive: "Also", "When in...", "Hence", "+1 for", "to elaborate briefly".

### Humor
- **Dry, nerdy, self-deprecating.** Targets himself ("I speak so fast :)", "throwaway tweet", "I still
  can't predict my tweet engagement").
- Wordplay in project names/taglines ("with a bite!", "teeth over education", "best ChatGPT $100 can
  buy").
- Emoji: minimal and ASCII-flavored — `:)`, `:))`, `¯\_(ツ)_/¯`, occasional ":\)". Uses "Hah", "lol",
  "omg" in lowercase. Not an emoji-heavy poster.

### Quotation / citation habits
- Credits prior art readily: notes the "jagged frontier" idea traces to Ethan Mollick's team (he
  "popularized" it), and frames "context engineering" as endorsing others ("+1 for") rather than
  inventing.
- References his own past work as a lineage (minGPT -> nanoGPT; GPT-2/GPT-3 "miniseries").
- Engages the community directly ("judging by mentions overnight people seem to find...").

---

## 5. Verbatim-style example phrase bank (for mimicry) `[1st]`

1. "you fully give in to the vibes, embrace exponentials, and forget that the code even exists"
2. "I just see stuff, say stuff, run stuff, and copy-paste stuff, and it mostly works"
3. "I 'Accept All' always, I don't read the diffs anymore"
4. "the LLMs (e.g. Cursor Composer w Sonnet) are getting too good"
5. "The word I came up with to describe the (strange, unintuitive) fact that..."
6. "+1 for 'context engineering' over 'prompt engineering'"
7. "the delicate art and science of filling the context window with just the right information"
8. "The hottest new programming language is English"
9. "LLMs are people spirits: stochastic simulations of people"
10. "Don't think of LLMs as entities but as simulators ... There is no 'you'."
11. "I swear I don't wake up just trying to come up with new memes"
12. "it's more accurately described as the decade of agents"
13. "This was a shower of thoughts throwaway tweet that I just fired off"
14. "prioritizes teeth over education" / "A tiny Autograd engine (with a bite! :))"
15. "the best ChatGPT that $100 can buy"
16. "no need for 245MB of PyTorch or 107MB of cPython"
17. "I think they are well deserving of a major version upgrade" (Software 3.0 framing)
18. "software is changing quite fundamentally again"

---

## Sources
- x.com/karpathy/status/1886192184808149383 — vibe coding (snippet) `[1st]`
- x.com/karpathy/status/2019137879310836075 — vibe coding retrospective (snippet) `[1st]`
- x.com/karpathy/status/1816531576228053133 — jagged intelligence (snippet) `[1st]`
- x.com/karpathy/status/1937902205765607626 — context engineering (snippet) `[1st]`
- x.com/karpathy/status/1617979122625712128 — "English" (snippet) `[1st]`
- x.com/karpathy/status/1973756330449236009 & /1997731268969304070 — ghosts/simulators (snippet) `[1st]`
- x.com/karpathy/status/1935518272667217925 — Software 3.0 / "new kind of computer" (snippet) `[1st]`
- github.com/karpathy/nanoGPT, /micrograd, /llm.c, /nanochat — READMEs (live fetch) `[1st]`
- dwarkesh.com/p/andrej-karpathy & simonwillison.net/2025/Oct/18/agi-is-still-a-decade-away/ —
  "decade of agents", 5-10X pessimistic, prediction experience `[1st words / 2nd framing]`
- news.ycombinator.com/item?id=44379538 — context engineering discussion `[2nd]`
- coderabbit.ai, klover.ai, quoteinvestigator.com, latent.space/p/s3 — secondary characterizations `[2nd]`
