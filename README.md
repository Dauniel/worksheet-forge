# worksheet-forge

Randomized, answer-verified math worksheets as LaTeX PDFs.

Built for tutoring. Two guarantees drive the whole design:

1. **Problems are never hardcoded.** Every number is sampled from a seeded
   `random.Random` inside a registered generator. There is no list of problems
   anywhere in the codebase, which is what stops the same archetypes (`-8 + 5`
   as question 1, forever) from recurring.
2. **No PDF is emitted with an unverified key.** Every answer is re-derived
   independently of how the generator produced it — the printed question is
   parsed back into sympy and re-solved. Any mismatch fails the build loudly.

Each build produces two PDFs: a teacher copy with a consolidated answer key,
and a clean student copy containing no answer content at all.

## Install

```bash
pip install -e .
```

No separate LaTeX install required. If you already have a TeX distribution
(MacTeX, TeX Live, MiKTeX) on PATH, `pdflatex` is used automatically. If not,
the first PDF build downloads [Tectonic](https://tectonic-typesetting.github.io/)
— a small, self-contained LaTeX engine — into a local cache (`~/.cache/worksheet-forge/bin`,
or `%LOCALAPPDATA%\worksheet-forge\bin` on Windows) and uses that from then on.

Pass `--no-download` (or set `WORKSHEET_FORGE_NO_DOWNLOAD=1`) to disable the
auto-download, e.g. in offline CI — the build then fails if no compiler is
found on PATH, rather than reaching out to the network.

## Use

No spec file needed — just list topics:

```bash
python -m forge topics                                   # what's available
python -m forge quick negatives fractions slope          # 8 problems per topic
python -m forge quick negatives:6 linear_equations:12:hard --seed 42
python -m forge quick negatives fractions --versions 3   # A/B/C variants
```

Each token is `topic`, `topic:count`, or `topic:count:difficulty`. The
generated spec is written alongside the PDFs so a good worksheet can be
reproduced, hand-edited, or committed.

For a hand-written worksheet, use a YAML spec:

```yaml
title: "Negatives, Fractions, Equations & Slope"
sections:
  - name: "Part A: Negative Number Operations"
    directions: "Evaluate each expression completely."
    workspace: 1.1cm
    problems:
      - {topic: negatives, subskill: add_sub_integers, count: 5, difficulty: easy}
```

```bash
python -m forge build specs/placement_algebra1.yaml --seed 42
```

Subskill quotas are enforced, not sampled: a section asking for 5 gets exactly
5, or the build raises.

### Flags

| Flag | Effect |
|---|---|
| `--seed N` | Reproducible. Omit for random (the seed is printed). |
| `--versions N` | A/B/C variants — fully independent draws |
| `--difficulty` | Override every section at once |
| `--title` / `--header` | Worksheet title and short header text |
| `--save PATH` | Write the generated spec somewhere permanent |
| `--out DIR` | Output directory (default `out/`) |
| `--lookback N` | Reject problems used in the last N runs (default 5) |
| `--no-history` | Ignore and don't update the anti-repeat ledger |
| `--no-pdf` | Emit `.tex` only |
| `--no-download` | Never auto-download a LaTeX compiler; fail if none is found on PATH |

Exit codes: `1` bad request, `2` an answer failed verification (a generator
bug), `3` LaTeX failed.

## Topics

`negatives`, `fractions`, `like_terms`, `linear_equations`, `slope`,
`ratios_percents`, `exponents`, `inequalities`, `word_problems`,
`number_sense`, `roots`, `geometry`, `percent_apps`, `absolute_value`,
`unit_rates`, `systems`, `quadratics`, `rational_expressions`,
`polynomials`, `variation`, `radical_equations`, `graphing` — 86
generators in total. Run `python -m forge topics` for the current list with
subskills.

`graphing` is scoped to point-testing (`is $(x, y)$ a solution?`), not shaded
regions -- a printed worksheet is graphed by hand, so there is no pixel
output to verify against. Point-testing is checkable and covers the same
"which side of the line" reasoning a student needs.

## Design

**Backwards construction.** For anything solvable, the answer is chosen first
and the problem built around it. Linear equations pick `x_sol`, then `m1, m2,
b1` with `m1 != m2`, and derive `b2 = (m1 - m2) * x_sol + b1` — so
no-solution and infinite-solution cases are structurally impossible. Slope
problems pick `m` and `b` first, then lattice points. Integer division picks
the divisor and quotient and multiplies.

**Anti-repetition ledger.** `history/used.json` records fingerprints globally
across specs; problems used in the last N runs are rejected at draw time, with
a bounded retry that relaxes and warns rather than hanging.

**Verification.** `forge/core/verify.py` holds one strategy per answer shape.
The strong ones re-read the printed question (`slope_from_points` recomputes
the slope from the points as rendered) rather than trusting generator
metadata. Word problems are the weakest case — prose can't be parsed back — so
they re-solve the model *and* assert every sampled quantity appears in the
text, catching model/prose drift.

## Tests

```bash
pytest
```

169 tests. Every generator is fuzzed across 1000 seeds for exceptions,
populated fingerprints, and answer verification. Also covered: determinism
(same seed, byte-identical output), variance (no problem is first more than 3
times in 50 runs), in-worksheet uniqueness, quota enforcement, and a sweep for
LaTeX coefficient bugs — `1x`, `-1x`, `0x`, `+ -`, float answers, unbalanced
math mode.

See `CLAUDE.md` for the conventions any future change must preserve.

## License

MIT — see [LICENSE](LICENSE).
