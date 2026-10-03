# Data-source scan — every open MOF data source (2026-10-03)

Owner request before any source-integration implementation: survey GitHub,
aggregation centers, and literally any open data relevant to the tool, and
rate each source with **two explicit numbers**. This scan feeds the D12
decision (which sources to adopt, in what order).

## The rating rubric (declared before the numbers — auditable)

**Completeness %** — weighted for THIS tool's use case (MOF electrocatalysis:
structures + synthesis + electrochemical numbers + open machine access):

| Component | Weight |
|---|---|
| MOF structure coverage (how much of the known/experimental space) | 40% |
| Synthesis / preparation data | 25% |
| Electrochemical measurement data (HER/OER overpotential, electrolyte, stability) | 25% |
| Open accessibility (license, bulk download, API, machine-readable) | 10% |

**Credibility /10** — peer-reviewed publication + institution (3), documented
curation process (3), versioning/DOI/maintenance (2), license clarity (1),
community adoption (1).

## The scan

| # | Source | What it actually contains | Completeness | Credibility | Access |
|---|---|---|---|---|---|
| 1 | **CoRE MOF 2019** (Zenodo, 78 MB) | ~14,000 computation-ready **experimental** MOF CIFs, cleaned from CSD, with source DOIs | **~50%** (structures 80%×40 + synthesis 30%×25 + electro 0 + open 100%×10) | **9/10** (peer-reviewed, multi-group curation, DOI, 51k+ downloads) | Open (CC) |
| 2 | **QMOF Database** (GitHub `rosen1/QMOF-database`, also Materials Cloud / MPContribs) | DFT properties (band gap, DOS, …) for 14k+ experimental-derived MOFs | **~55%** (structures 80%×40 + synthesis 10%×25 + electro-as-theory 40%×25 + open 100%×10) | **9/10** (Rosen et al., *Matter* 2021; versioned, DOI, maintained) | Open (MIT) |
| 3 | **CSD MOF subset** (CCDC) | ~100k+ experimental MOF structures — THE authoritative structural record | **~46%** (structures 95%×40 + synthesis 30%×25 + electro 0 + open 0) | **10/10** (the gold standard) | **CLOSED — commercial license** |
| 4 | **DigiMOF** (text-mined synthesis, Chem. Mater. 2023) | 52,680 literature-extracted synthesis properties: methods, precursors, solvents, topology | **~28%** (structures 0 + synthesis 70%×25 + electro 0 + open 100%×10) | **8/10** (peer-reviewed, 111+ citations; documented NLP error rates) | Open |
| 5 | **ODAC23** (GitHub `facebookresearch/open-dac`) | 38M DFT calcs of CO₂/H₂O adsorption over ~8,400 MOFs | **~22%** (structures 30%×40 + electro 0 — DAC, not HER/OER + open 100%×10) | **9/10** (Meta FAIR, peer-reviewed, benchmarked) | Open |
| 6 | **hMOF** (Northwestern) | ~138k **hypothetical** MOFs with simulated isotherms | **~24%** (hypothetical structures 35%×40 + open 100%×10) | **7/10** (classic 2012 paper; aging infrastructure) | Open |
| 7 | **COD** (crystallography.net) | 450k+ CIFs incl. MOFs (ungrouped, mixed quality) | **~22%** (structures 30%×40 + open 100%×10) | **8/10** (open infrastructure since 2003) | Open |
| 8 | **MOFid / MOFkey** (GitHub) | Structure-identity keys (topology + building units) — **tooling, not data**; cross-references QMOF↔CSD↔ODAC23 | n/a (enabler for #18 compound identity) | **8/10** (published method) | Open |
| 9 | **Text-mined synthesis repos** (`CederGroupHub/text-mined-synthesis_public`, `L2M3`) | Solid-state + LLM-extracted synthesis routes (MOF subset emerging) | **~12%** | **6/10** (partially peer-reviewed) | Open |
| 10 | **Experimental MOF HER/OER numbers** | ⚠️ **NO dedicated open database exists.** Numbers live in papers; ML papers use small ad-hoc literature tables; MOFEvolve emerging | **~5%** | n/a | — |
| 11 | **OpenAlex / Crossref** | Paper discovery + metadata | already integrated (D9) | — | Open |

## The scan's three load-bearing findings

1. **Structures are a solved problem (if we stay open):** CoRE MOF 2019 gives
   computation-ready experimental CIFs with source DOIs; COD is a fallback;
   CSD is authoritative but closed (any use needs a licensing decision).
2. **Synthesis conditions exist as text-mined data** (DigiMOF) — usable with
   provenance labels, consistent with our attribution model.
3. **THE GAP: no open database of experimental MOF electrocatalysis numbers.**
   This is the owner's core need ("أرقام المعمل") and it exists nowhere as
   open data — it lives in papers. Consequence: **our tool's attributed
   assertion model (record from papers, D4-reviewed) is not just a design
   choice — it is the gap-filler.** And #17's industry/reference stream must
   be built from curated review tables with provenance, not downloaded.

## Proposed adoption order (D12 decision — owner to approve)

1. **CoRE MOF 2019** — structure lookup + source-DOI→reference capture links
2. **QMOF** — theory-stream numbers for #17 (labeled `computational`) and #18 profiles
3. **DigiMOF** — synthesis-condition context (labeled `tool inference` provenance)
4. **MOFid/MOFkey** — the compound-identity key prerequisite for #18
5. **COD** — fallback structure lookup
Defer: ODAC23 (DAC-scoped), hMOF/ARC (hypothetical screening later), CSD
(closed — separate licensing decision), emerging text-mining repos (watch).

## Sources consulted

CoRE MOF on Zenodo; mofsresearch.com; QMOF via MPContribs; Northwestern MOF DB;
COD (Gražulis et al. 2011); DigiMOF (PMC10269341, MOFtextminer GitHub);
ODAC23 (facebookresearch/open-dac); MOFEvolve (ChemRxiv); Materials Cloud;
NOMAD; CederGroupHub/text-mined-synthesis_public; L2M3.
