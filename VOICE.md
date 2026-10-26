# Technical Voice — darpan-docs

This is the documentation-specific calibration of the Darpan brand voice. It **extends** `VOICE_GUIDE.md` (the brand soul: seven pillars + seriousness dial) — read that first. This file says how those pillars land in a technical doc, and it is the standard every page here is measured against. It is internal: it is **not** in `docs.json` and never publishes.

## The one idea

The voice lives in the **framing**, never the mechanics (VOICE_GUIDE rule #4). A lead, a transition, or a "why this matters" aside carries the tone. The step, the table cell, the code block, the service contract stay literal and clinical. Warmth in a how-to *is* the procedure working.

## Register map

| Section | Register | Voice budget |
|---|---|---|
| `getting-started`, `guides`, `troubleshooting` | Plain+ | Warm, disarming lead + transitions + "why this matters" asides; steps/tables/code clinical. |
| `reference`, `api-reference` | Plain | Directness + clarity + next-step; near-zero warmth. A reference must not sound like a landing page. |
| `backend`, `engineering` | Plain/Grave | Precision first; voice only in section intros. |

**Troubleshooting is Plain+ on purpose** — it is the strongest disarm-the-dread moment on the site. The lead names the failure plainly and shrinks it, then the checks stay literal. Carve-out: disarm the dread of the *task*, never minimize a real failure. A page about data loss or a Darpan-caused failure drops to **Grave** — ownership and specifics, no reassurance.

## Do

- Open every page with a lead that frames the work. For Plain+, disarm the dread (name the tedious/scary thing, then shrink it). For Plain, one crisp orienting sentence. For Plain/Grave, state what this is and why it matters in one line.
- Write to one person. "You," active voice, sentence-case headings.
- Lead with the true thing, then the path. Name the hard part before the payoff.
- Keep workflow pages task-shaped: lead → prerequisites → steps → expected result → next step.
- Bold UI elements; code-format paths, commands, and identifiers.

## Don't

- Never use: leverage, robust, seamless/seamlessly, best-in-class, mission-critical, effortless, cutting-edge. (Hard fail.)
- Review and usually cut: simply, just, powerful, easy, quick, and throat-clearing ("It is important to note that…").
- Don't sprinkle personality on a procedure. Don't warm a reference page. Don't oversell or fake-cheer.
- Don't list Ask Darpan search synonyms. Don't assume a permanent sidebar.

## Per-page checklists

**Plain+ (getting-started, guides, troubleshooting)**
- [ ] Lead frames + disarms; not a restated title.
- [ ] Key transitions / "why this matters" moments carry the voice.
- [ ] Steps, tables, code unchanged in register — literal.
- [ ] Workflow pages: lead → prerequisites → steps → expected result → next step.
- [ ] Troubleshooting: lead names + shrinks the failure; Grave if data-loss / Darpan-caused.
- [ ] No buzzwords; soft words reviewed; no factual change.

**Plain (reference, api-reference)**
- [ ] Lead is one crisp orienting sentence — no disarming framing added.
- [ ] Contracts, field tables, service shapes accurate and literal.
- [ ] Ends with a reliable next-step link where one exists.
- [ ] No buzzwords; terminology consistent; no factual change.

**Plain/Grave (backend, engineering)**
- [ ] Precision first; voice only in section intros (≤ one "why this matters" line per major section).
- [ ] Architecture/contracts/entity names literal, grounded in the real Moqui `darpan` component; no aspirational architecture; no dev-local checkout names as official.
- [ ] No buzzwords; no factual change.

## Before / after

**Plain+ — guide lead (`guides/run-reconciliation.mdx`)**
- Before: "Run reconciliation executes the saved setup: source data, schemas, matching keys, and optional RuleSets. The output points to the next decision."
- After: "Running a reconciliation is the easy part — the work happened back in setup. This step takes your saved sources, schemas, matching keys, and rules, compares everything, and hands back what doesn't line up. That output is where the real decisions start."

**Plain+ — framing vs. mechanics (`getting-started/core-concepts.mdx`)**
- Page lead (new, warm): "These are the six words you'll see on every screen. Learn them once here and the rest of the docs stop being a vocabulary test."
- Term body (unchanged, clinical): "A schema describes the structure Darpan expects from source data. It gives a reconciliation run stable field names and types to use during parsing, mapping, and comparison."

**Plain+ — troubleshooting lead (`troubleshooting/login-and-session.mdx`)**
- After: "Getting locked out of your own tool is the worst kind of broken — you can't even get in to fix it. Most login failures come down to three things, and you can rule them out in a couple of minutes. Start at the top." (The checks below stay literal.)

**Plain — reference (do not warm it)**
- Reference and API pages keep today's clinical tone. The fix here is clarity, accurate contracts, and a reliable next-step link — not personality.

**Plain/Grave — backend section intro (`backend/reconciliation-engine.mdx`)**
- Section intro may carry one line: "This is where a run actually spends its time, so the two passes are worth understanding." Body — service contracts, Spark/Drools processing, entity names — stays exactly as precise as today.
