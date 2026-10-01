# Discovery ideas scan — implemented tools that help researchers find suitable compounds

**Status:** research note (2026-10-01). Documents actually-deployed tools and the ideas they
demonstrate. This note proposes nothing on the owner's behalf; each idea carries a proposed
timing (`now` / `later` / `foundation-only`) subject to Mohammed's approval, per the
learning-to-project mapping rule in plan §8.

## 1. What is actually deployed (checked 2026-10-01)

| Tool / dataset | What it really does | Relevant link |
|---|---|---|
| **Materials Project MOF Explorer** | Browsable explorer over 20k+ MOFs with QMOF DFT properties; filters by metal/linker/topology; uses MOFid/MOFkey identifiers | [MP docs](https://docs.materialsproject.org/apps/explorer-apps/mof-explorer/property-definitions/smiles-mofid-and-mofkey) |
| **CoRE MOF DB (2025 update) + `coremof-tools`** | Curated *experimental* MOF structures, computation-ready, with a Python query package and integrated material–process screening | [QMOF repo](https://github.com/Andrew-S-Rosen/QMOF) (companion landscape), CoRE MOF 2025 update in *Matter* |
| **DigiMOF / synthesis databases** | Structured synthesis information: topology, linkers, metal precursors, methods, solvents — enables synthesizability-aware screening | ACS (DigiMOF) |
| **Catalysis-Hub.org (CatApp)** | Open DFT reaction/adsorption data with per-publication provenance and interactive activity maps | [publications](https://www.catalysis-hub.org/publications), [Sci Data 2019](https://www.nature.com/articles/s41597-019-0081-y) |
| **CatHubExp (experimental Catalysis-Hub)** | Structured catalyst **synthesis + characterization + electrochemical testing** records for reproducible catalyst research | [about](https://experimental.catalysis-hub.org/about) |
| **Open Catalyst Project (OC20/OC22)** | Large-scale DFT datasets + ML baselines for oxide electrocatalysis (OER scaling relations) | [project](https://opencatalystproject.org), [OC22](https://arxiv.org/abs/2206.08917) |
| **Rayyan** | Free AI-assisted title/abstract screening with deduplication and decision logging, used by 1M+ researchers | [rayyan.ai](https://www.rayyan.ai) |
| **Covidence** | End-to-end systematic-review workbench: import → dedup → screening with reasons → **extraction forms** → bias assessment → PRISMA export | [comparison](https://www.scribelabwriter.com/blog/rayyan-vs-covidence-choosing-the-right-tool-for-your-systematic-review), [PMC6148615](https://pmc.ncbi.nlm.nih.gov/articles/PMC6148615) |
| **MOFid / MOFkey + web-MOFid** | Systematic unique identifiers from building-block deconstruction (metal node + linker SMILES + topology); online generator from CIF | [paper](https://pubs.acs.org/cgdefu/article/19/11/6682/584912/Identification-Schemes-for-Metal-Organic), [web tool](https://snurr-group.github.io/web-mofid) |
| **ChemDataExtractor** | Classic rule-based NLP extraction of chemical/materials properties from literature | [docs](https://cambridgemolecularengineering-chemdataextractor-development.readthedocs-hosted.com/en/latest/getting_started.html) |
| **MaterialBrain & LLM extraction pipelines (2025)** | LLM-based synthesis-recipe extraction with **human-in-the-loop verification**; field trend from rules → LLM + human check | [paper](https://pubs.acs.org/jcisd8/article/66/1/228/5080242/MaterialBrain-High-Performance-Material-Synthesis), [review](https://www.nature.com/articles/s43246-025-01043-3), [method](https://pubs.rsc.org/dd/article/3/6/1221/846018/Flexible-model-agnostic-method-for-materials-data) |

## 2. The six most helpful ideas, mapped to this project

| # | Idea (borrowed from) | Why it helps "find the suitable compound" | Proposed timing |
|---|---|---|---|
| 1 | **Screening funnel with decision logs** (Rayyan/Covidence) | Every candidate record gets include/exclude/maybe **with a reason**, dedup, and an exportable audit trail — turns ad-hoc reading into a defensible funnel; maps directly to issues #10–#11 candidate card + review queue | `now` — adopt the pattern in the review UI |
| 2 | **Building-block identity keys: MOFid/MOFkey** (Bucior et al.) | A machine-checkable identifier for the **framework level** (node + linker + topology). Strengthens the identity contract: never merges samples, but makes "same parent framework" comparisons citable and reproducible. Fits as an optional `framework.mofid` field | `now` — one optional column + validation; no new dependency in slice 1 |
| 3 | **Structured synthesis+testing records** (CatHubExp) | The closest existing analog of our tested-sample contract: synthesis, characterization, and electrochemical testing kept as linked, reproducible records. Also a potential future **source** for evidence | `now` as design confirmation; `later` as an integration source (owner decision) |
| 4 | **Explorer-style filtering over curated experimental sets** (MP MOF Explorer, CoRE 2025, `coremof-tools`) | Filters (metal, linker, topology) over a *curated experimental* base, then drill into per-material evidence — the discovery half of our workflow once evidence records exist | `later` — after #8–#11 provide the data |
| 5 | **Human-in-the-loop AI extraction** (MaterialBrain; Digital Discovery method) | AI proposes an extraction with a location pointer; a human confirms/corrects with full provenance — exactly our `tool inference` → `user judgment` epistemic typing. Would accelerate #7's manual extraction later | `later` — owner decision required (plan B.2 excludes LLM transformations from MVP) |
| 6 | **Reproducible dataset provenance** (OCP/OC22; Catalysis-Hub per-paper data) | Every data row carries publication, version, and calculation context — validates the provenance invariants we already encode; a benchmark for our export format | `foundation-only` — no dependency to add |

## 3. Honest boundaries

- None of these tools implements our differentiator: **per-assertion review states + tested-sample
  identity + documented search scope ("no result found ≠ novel")**. That remains our niche; the
  ideas above are adoption candidates, not competitors to replicate wholesale.
- ML screening (QMOF-style property prediction, OCP models) is deliberately outside the first
  slice; any use would be `later` with its own owner decision, validation set, and labeling.
- DigiMOF/CatHubExp coverage of MOF HER/OER electrochemistry is unverified until inspected
  case by case (same rule as the task 002 source options).
