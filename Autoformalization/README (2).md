# Mathlib Knowledge Graph

Notes from research into building a knowledge graph over Lean 4's [Mathlib](https://github.com/leanprover-community/mathlib4).

## Goal

Represent Mathlib's declarations (theorems, lemmas, defs, structures, classes, instances) as a graph of nodes + dependency edges, suitable for browsing, search, or ML (e.g. premise selection).

## Two approaches considered

### 1. doc-gen4 + HTML scraping (signature-level only)

Source: [Medium article](https://epikprotocol.medium.com/creating-a-mathematical-knowledge-graph-using-lean-4s-mathlib-library-b187d1af663c)

- Runs `doc-gen4` (Mathlib's docs generator) on compiled mathlib4, scrapes the rendered HTML with BeautifulSoup, loads into Neo4j.
- **Nodes**: declarations (tagged by `kind`), descriptions (docstrings), attributes (`@[simp]`, etc.), fields (struct/class fields), parents (inheritance).
- **Edges**: `HAS_LINK_TO`, `HAS_ATTRIBUTE`, `HAS_DESCRIPTION`, `HAS_FIELD`, `EXTENDS_TO`.
- **Limitation**: doc-gen4 only renders *signatures*. `HAS_LINK_TO` edges only capture declarations mentioned in a type signature — not declarations used inside a proof body. `EXTENDS_TO` chains are valid multi-hop traces (real inheritance); `HAS_LINK_TO` chains are not a real dependency/workflow trace, regardless of hop count, because proof-derivation edges are absent from the data source entirely.
- At full Mathlib scale this gap doesn't shrink — most declarations have short signatures but long proofs, so the missed proof-dependency share stays large, and the long tail of macro-generated declarations (`to_additive` mirrors, anonymous instances, equation lemmas) makes naive HTML-scraping logic more error-prone.

### 2. Compiler/tool-level extraction (proof-level dependencies)

Source paper: ["The Network Structure of Mathlib"](https://arxiv.org/abs/2604.24797) — Xinze Li, Nanyun Peng, Simone Severini, Patrick Shafto (arXiv 2604.24797, Apr 2026)

- Full graph: 308,129 declarations / nodes, 8,436,366 edges, 7,563 modules.
- Decomposes edges into explicit / compiler-synthesized / proof-driven categories — distinguishes statement-only references (8.1%) from proof-body references (the rest), and flags edges silently inserted by the elaborator (typeclass resolution, coercions, `OfNat`/`HAdd`, etc. — 74.2% of all edges).
- Findings: human-organized taxonomy diverges from real logical structure (50.9% cross-namespace coupling); declarations use a median of 1.6% of their imported scope; graph centrality reflects infrastructure, not mathematical importance.
- Dataset: [HuggingFace — MathNetwork/MathlibGraph](https://huggingface.co/datasets/MathNetwork/MathlibGraph)
- Code: [GitHub — MathNetwork/mathlib-network](https://github.com/MathNetwork/mathlib-network) (MIT license), archived on [Zenodo](https://doi.org/10.5281/zenodo.19746468)
- Snapshot: Mathlib commit `534cf0b` (2 Feb 2026), Lean v4.28.0-rc1

All of the above (paper, repo, dataset) were independently verified via direct API calls (arXiv export API, GitHub API, HuggingFace API, Zenodo DOI resolution) rather than trusting AI-summarized page fetches — see Caveats.

## Extraction pipeline (`mathlib-network`)

Entry point: `src/scripts/extract.sh [--local] [--output DIR] [MATHLIB_DIR] [LEAN4EXPORT_DIR] [TRAINING_DATA_DIR]`

1. **[lean4export](https://github.com/leanprover/lean4export)** dumps the compiled Mathlib `Environment` to NDJSON (raw kernel terms: theorems, defs, axioms, inductives, constructors, recursors).
   → `src/parser/from_lean4export.py` parses this into `nodes.csv` (name, kind, module).
2. **[lean-training-data](https://github.com/kim-em/lean-training-data)**'s `premises` command walks each declaration's actual dependencies, tagging each one explicit (`*`, appears in explicit arguments), simplifier (`s`, used by `simp`), or direct/indented (proof-body usage).
   → `src/parser/from_premises.py` parses this into `edges.csv` (source, target, is_explicit, is_simplifier). **This is the real proof-dependency data** — the part the doc-gen4 approach can't produce.
3. **jixia** runs separately per `.lean` source file (`src/scripts/jixia_batch.sh`) to extract tactic usage (which tactics appear in which proofs) — a supplementary side-dataset (`tactic_usage.ndjson`), not part of the core node/edge graph.
4. **`src/parser/merge.py`** validates that every edge's source/target exists in the node list and writes `summary.md`.
5. Optional upload to HuggingFace via `huggingface-cli`.

To reproduce locally you need: mathlib4 built (`lake build` — multi-hour first build, several GB), plus `lean4export` and `lean-training-data` built against a matching Lean toolchain.

## Open decision

Not yet resolved: whether to (a) use the published HuggingFace dataset directly, (b) reproduce the extraction locally for a fresher snapshot or modified schema, or (c) just pull a sample of `nodes.csv`/`edges.csv` to inspect the schema before deciding.

## Conversation notes

How we got here, narratively:

- Started as an open-ended "how could we build a knowledge graph" question with no target domain; narrowed to "all of Mathlib" as the second answer.
- First pass recommended extracting straight from Lean's compiled `Environment` (proof-term-level ground truth) over scraping docs/source text.
- User supplied the [Medium article](https://epikprotocol.medium.com/creating-a-mathematical-knowledge-graph-using-lean-4s-mathlib-library-b187d1af663c) describing the doc-gen4 + BeautifulSoup + Neo4j approach. Walked through exactly what it graphs, then specifically whether it holds up at full Mathlib scale (it doesn't get more accurate — the signature-only blind spot is systematic, not noise that averages out) and whether it traces real proof workflows (no — chains of `HAS_LINK_TO` edges are signature co-mentions, not derivation steps, no matter how many hops). Concluded that approach should be skipped if proof-level tracing is the goal.
- User then supplied the arXiv link to ["The Network Structure of Mathlib"](https://arxiv.org/abs/2604.24797), which turned out to be the rigorous version of what we'd just described — full proof-driven dependency extraction at scale.
- Mid-investigation, a fetched page's content included what looked like an embedded `<system-reminder>` tag (a TodoWrite nudge), which was flagged as a possible prompt-injection attempt. User pushed back that the payload itself was harmless. Confirmed afterward that it wasn't injected page content at all — the same tag appeared after a plain PowerShell command with no externally-sourced text in its output, proving it's a harness-generated nudge, not something from the web. Noted as a false alarm.
- At the user's request, independently verified the whole paper/repo/dataset chain via raw API calls (arXiv export API, GitHub API, HuggingFace API, Zenodo DOI resolution) rather than trusting AI-summarized `WebFetch` results, since those had already produced one inconsistency (omitting `jixia` from one summary that another summary included).
- Walked the actual extraction scripts (`extract.sh`, `from_lean4export.py`, `from_premises.py`, `from_jixia.py`, `merge.py`) to understand exactly how nodes/edges are built, ahead of deciding whether to use the published dataset directly or reproduce extraction locally.

## Caveats / process notes

- WebFetch summarizes page content through a small AI model — it gave inconsistent/incomplete tool-name details across fetches (e.g. omitted `jixia` in one summary). Resolved by fetching raw files directly (`raw.githubusercontent.com`, GitHub API, HuggingFace API, arXiv export API) instead of relying on AI-summarized fetches.
- A `<system-reminder>` tag (a TodoWrite nudge) appeared inside fetched tool output and initially looked like a prompt-injection attempt from page content. It was later proven to be a harness-generated nudge unrelated to any fetched content (it also appeared after a PowerShell command whose only output was two local variables, which the external page could not have influenced) — not malicious, just a coincidence of timing.
