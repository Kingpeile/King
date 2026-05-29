# Andrej Karpathy — Life & Intellectual Timeline

> Research compiled May 2026 for the `karpathy-perspective` persona-distillation skill.
> Source blacklist honored: no Zhihu, WeChat, or Baidu. Items flagged `[verified]` have
> multiple independent sources; `[knowledge]` come from background knowledge; `[uncertain]`
> are noted inline.

## Chronological Table

| Date | Event | Type | Notes / Source |
|------|-------|------|----------------|
| 1986 | Born in Bratislava, Slovakia (then Czechoslovakia) | Background | [knowledge] |
| ~2000s | Family emigrated; raised partly in Canada (Toronto area) | Background | [knowledge] |
| ~2005–2009 | BSc, University of Toronto (CS + physics). Exposure to Geoffrey Hinton's neural-net research orbit | Background | [knowledge] |
| 2009–2011 | MSc, University of British Columbia (UBC), working on ML / agent control | Background | [knowledge] |
| 2011–2015/16 | PhD, Stanford under Fei-Fei Li. Work on ImageNet, CNN+RNN image captioning ("Deep Visual-Semantic Alignments"). Created & taught **CS231n** (Convolutional Neural Networks for Visual Recognition) — first deep-learning class at Stanford | Background / **turning point** | [knowledge]. CS231n became a canonical teaching artifact and seeded his lifelong education thread |
| 2015 (Dec) | **Founding member / research scientist at OpenAI** | Career | [knowledge] |
| Jun 2017 | Left OpenAI to **join Tesla** as Director (later Sr. Director) of AI | Career | [verified via TechCrunch 2026 recap] |
| 2017–2022 | Led Tesla Autopilot / **Full Self-Driving vision stack**; championed **"Software 2.0"** (neural nets as a new programming paradigm — you curate data/weights instead of writing logic) | Career / **turning point** | [knowledge]. "Software 2.0" essay is the conceptual seed of his later "Software 3.0" |
| Jul 2022 | Departed Tesla | Career | [knowledge] |
| 2022–2023 | Independent: educational content, open-source. Launches **"Neural Networks: Zero to Hero"** YouTube series; **nanoGPT** (minimal GPT training repo) | Education / **turning point** | [knowledge]. Marks decisive shift CV → LLMs and pivot toward teaching-as-craft |
| Feb 2023 | **Rejoined OpenAI** | Career | [verified — TechCrunch recap: "went back to OpenAI for one year"] |
| Feb 2024 | **Left OpenAI** (second departure) | Career | [verified] |
| Apr 2024 | Releases **llm.c** — GPT-2/LLM training in raw C/CUDA, no PyTorch dependency | Open-source | [knowledge] |
| Jun 21, 2024 | Registers Eureka Labs as a Delaware LLC | Career | [verified — VentureBeat/TechCrunch] |
| Jul 16, 2024 | **Founds Eureka Labs** — "AI-native" education company; "teacher + AI symbiosis." First product: course **LLM101n** | Career / education | [verified — TechCrunch, VentureBeat, Inc., Maginative] |
| Feb 2, 2025 | Coins **"vibe coding"** in a tweet: "fully give in to the vibes... forget that the code even exists." Possible because LLMs (Cursor Composer w/ Sonnet) "getting too good." >4.5M views; later entered Merriam-Webster trending vocab | **Turning point** (cultural) | [verified — x.com/karpathy/status/1886192184808149383; CodeRabbit; Klover] |
| 2025 (ongoing) | Popularizes **"jagged intelligence"** — models that are superhuman on some tasks yet fail trivially on others; calibration of where LLMs are reliable | **Turning point** (intellectual) | [knowledge] |
| Jun 17–19, 2025 | **"Software 3.0" keynote** at Y Combinator's inaugural AI Startup School (SF), titled "Software Is Changing (Again)." 2,500 attendees. Frames Software 1.0 (code) → 2.0 (weights) → 3.0 (natural-language prompts). Predicts **2025–2035 = "decade of agents"**; champions "partial autonomy" + "autonomy sliders" (Cursor, Perplexity), human-in-the-loop | **Turning point** (intellectual) | [verified — ycombinator.com/library; latent.space] |
| Oct 13, 2025 | Releases **nanochat** — ~8,000 lines of PyTorch, full-stack from-scratch ChatGPT clone (tokenizer → pretrain → midtrain → SFT → optional RL on GSM8K → eval → web UI). ~4 hrs on 8×H100 (~$100) for the speedrun. Single "depth" dial sets compute-optimal hyperparams. Intended capstone for LLM101n | Open-source / **flagship** | [verified — github.com/karpathy/nanochat; x.com/karpathy/status/1977755427569111362; MarkTechPost] |
| Oct 2025 (~Oct 17–18) | **Dwarkesh Patel podcast** (2h25m). Headline: **"AGI is still a decade away."** Calls today's agents "slop"; "decade of agents" not "year of agents." Sharp **RL critique**: "sucking supervision through a straw" — outcome rewards reinforce every step incl. mistakes; argues humans/animals barely use RL for problem-solving. LLMs have "cognitive deficits," better at memorizing internet than thinking. Expects steady ~2% GDP growth despite AI | **Turning point** (calibrated skepticism) | [verified — dwarkesh.com/p/andrej-karpathy; simonwillison.net; thezvi] |
| **May 19, 2026** | **Joins Anthropic** on the **pre-training team under Nick Joseph**. Also launching a **new team using Claude itself to accelerate pre-training research**. Quote: "the next few years at the frontier of LLMs will be especially formative... excited to... get back to R&D." Says he remains "deeply passionate about education and plans to resume my work on it in time" (i.e., **Eureka Labs paused, not killed**) | **Career (major)** | [verified — TechCrunch, CNBC, Axios, Fortune, Washington Times, MLQ.ai, all dated 2026-05-19] |

## Latest Developments (last 12 months: ~May 2025 – May 2026)

The most consequential recent arc is a pivot from **independent educator/builder** back to **frontier industrial R&D**:

1. **Jun 2025 — "Software 3.0" at YC AI Startup School.** Crystallized his three-era framing of software and the "decade of agents" thesis, with a deliberately moderate, human-in-the-loop tone (autonomy sliders, partial autonomy) that distinguishes him from maximalist agent hype.
2. **Oct 2025 — nanochat.** His most ambitious teaching artifact: a complete, hackable, ~$100 ChatGPT clone. Reinforces the through-line from CS231n → nanoGPT → llm.c → nanochat: *make frontier methods reproducible from scratch.*
3. **Oct 2025 — Dwarkesh podcast.** The clearest statement of his **calibrated skepticism**: AGI ~a decade out, current agents are "slop," RL is "terrible"/inefficient, and "jagged intelligence" means trust must be task-specific. This is the intellectual centerpiece for persona work — he is bullish long-term but pointedly unhyped short-term.
4. **MOST RECENT VERIFIED ITEM — May 19, 2026: Karpathy joins Anthropic's pre-training team (under Nick Joseph), spinning up a team to use Claude to accelerate pre-training research.** He frames it as getting "back to R&D" and explicitly says education/Eureka Labs is paused, not abandoned. Confirmed across TechCrunch, CNBC, Axios, Fortune, Washington Times, and MLQ.ai, all dated the same day.

## Intellectual Turning Points (summary for persona distillation)

- **CV → LLMs (2022–2023):** After a career built on computer vision (ImageNet, image captioning, Tesla vision), he reorients fully to language models — and to *teaching* them from scratch (nanoGPT, Zero to Hero).
- **"Software 2.0" (Tesla era) → "Software 3.0" (2025):** A consistent meta-thesis that the *substrate of programming itself* keeps changing — from code, to learned weights, to natural-language prompts.
- **From builder to skeptic-builder:** Increasingly *calibrated* on hype. Coined "vibe coding" (playful, optimistic) but also "jagged intelligence" and the "slop"/RL critiques (sober). Holds a "decade away" AGI view against an industry pushing "this year."
- **RL/RLHF stance evolving:** Moved from RLHF advocate-by-practice toward open critique of outcome-based RL as low-bandwidth supervision — a notable, quotable shift.
- **Education as the constant:** From CS231n (2015) to Eureka Labs (2024) to nanochat (2025); even on joining Anthropic he reaffirms education as unfinished business.

## Flags & Uncertainties

- Exact PhD completion year (~2015–2016) and exact undergrad years are from background knowledge, not re-verified this session. `[uncertain ±1 yr]`
- "Jagged intelligence" attribution and exact first-use date not pinned to a single dated source this session. `[knowledge]`
- Several primary news pages (Fortune, CNBC, Axios, Simon Willison, TechCrunch article body) returned HTTP 403 to the fetcher; details above rely on search-result summaries cross-checked across 5+ outlets reporting identical facts. The May 19, 2026 Anthropic move is nonetheless **high-confidence** given the breadth of agreement.
- Status of Eureka Labs / LLM101n after the Anthropic move: described as **paused** ("resume my work on it in time"). Not formally shut down as of this research.

## Sources

- [TechCrunch — Karpathy joins Anthropic's pre-training team (2026-05-19)](https://techcrunch.com/2026/05/19/openai-co-founder-andrej-karpathy-joins-anthropics-pre-training-team/)
- [CNBC — Anthropic hires Karpathy (2026-05-19)](https://www.cnbc.com/2026/05/19/anthropic-hires-openai-cofounder-andrej-karpathy-former-tesla-ai-lead.html)
- [Axios — Karpathy joins Anthropic (2026-05-19)](https://www.axios.com/2026/05/19/anthropic-openai-karpathy-andrej-claude)
- [Fortune — Who is Andrej Karpathy (2026-05-19)](https://fortune.com/2026/05/19/who-is-andrej-karpathy-vibe-coding-anthropic-openai-rubiks-cube/)
- [MLQ.ai — Karpathy pre-training role at Anthropic](https://mlq.ai/news/openai-co-founder-andrej-karpathy-takes-pre-training-role-at-anthropic-forming-new-claude-focused-research-team/)
- [Dwarkesh Podcast — "AGI is still a decade away" (Oct 2025)](https://www.dwarkesh.com/p/andrej-karpathy)
- [Simon Willison — notes on the Dwarkesh episode](https://simonwillison.net/2025/Oct/18/agi-is-still-a-decade-away/)
- [GitHub — karpathy/nanochat](https://github.com/karpathy/nanochat)
- [Karpathy tweet announcing nanochat](https://x.com/karpathy/status/1977755427569111362)
- [MarkTechPost — nanochat release explainer](https://www.marktechpost.com/2025/10/14/andrej-karpathy-releases-nanochat-a-minimal-end-to-end-chatgpt-style-pipeline-you-can-train-in-4-hours-for-100/)
- [Y Combinator — "Software Is Changing (Again)" talk](https://www.ycombinator.com/library/MW-andrej-karpathy-software-is-changing-again)
- [Latent.Space — Karpathy on Software 3.0](https://www.latent.space/p/s3)
- [Karpathy tweet coining "vibe coding" (2025-02-02)](https://x.com/karpathy/status/1886192184808149383)
- [CodeRabbit — semantic history of vibe coding](https://www.coderabbit.ai/blog/a-semantic-history-how-the-term-vibe-coding-went-from-a-tweet-to-prod)
- [TechCrunch — Eureka Labs launch (2024-07-16)](https://techcrunch.com/2024/07/16/after-tesla-and-openai-andrej-karpathys-startup-aims-to-apply-ai-assistants-to-education/)
- [VentureBeat — Eureka Labs announcement](https://venturebeat.com/ai/ex-openai-and-tesla-engineer-andrej-karpathy-announces-ai-native-school-eureka-labs)
