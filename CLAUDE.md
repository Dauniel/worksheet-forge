# worksheet-forge — working agreements

Seeded, symbolically-verified math worksheet generator. Two invariants drive
the whole design; violating either is a regression regardless of how good the
output looks.

## Invariant 1: problems are never hardcoded lists

No generator may return a problem drawn from a literal list, tuple, or dict of
problems. Every number a student sees must come from the passed-in
`rng: random.Random` within difficulty-scaled ranges. If a topic feels like it
needs a fixed pool, widen the sampling ranges or add a structural parameter
instead.

This is the mechanism that stops `-8 + 5` from being question 1 of every
worksheet. `tests/test_variance.py` asserts it; do not weaken that test.

Word problems are the one permitted use of authored text: sentence *frames*
may be templated, but all names, quantities, and rates are sampled and the
answer is solved by sympy. Frames are scaffolding, never problems.

## Invariant 2: no PDF is emitted with an unverified key

`forge/core/verify.py` re-derives every answer *independently of how the
generator computed it* — parsing `question_latex` back into sympy and
re-solving. `generate()` calls `verify_all()` before any rendering happens.
Any mismatch raises `VerificationError` and fails the build loudly.

Never "fix" a verification failure by loosening the comparison. A failure means
either the generator or the LaTeX rendering is wrong.

## Backwards construction

For anything solvable, **pick the answer first, then build the problem around
it**. This guarantees clean answers and structurally prevents degenerate cases
— no accidental no-solution equations, no undefined slopes, no surprise
fractions.

- *Linear equations:* choose `x_sol`, then `m1, m2, b1` with `m1 != m2`, and
  compute `b2 = (m1 - m2) * x_sol + b1`.
- *Slope from two points:* choose `m` and `b` first, then two distinct lattice
  `x` values; compute their `y`.
- *Integer division:* choose divisor and quotient, multiply to get the dividend.
- *Fractions:* choose denominators from a difficulty-scaled small set so the
  LCD stays reasonable.

## LaTeX output conventions

- **No title block.** No `\title` / `\author` / `\date` / `\maketitle`. The
  document opens directly with the first `\section*{Part A: ...}`.
  Identification lives in the `fancyhdr` header: worksheet name left,
  `Name: \underline{\hspace{1.8in}}` right, page number in the footer. The
  header is length-budgeted in `render_tex` so it never wraps into the Name
  rule; a spec may set a short `header:` key to override the long `title:`.
- **Directions once per section, never per item.** Items are bare problems:
  `\item $3x + 5 = 2x - 9$`, never `\item Solve for $x$: $3x+5=2x-9$`.
- **Work space under every computation item** via `\vspace{...}`, scaled per
  section from the spec's `workspace` key. Blank white space only — no boxes or
  visible outlines (these get completed on an iPad).
- **Sections flow continuously.** No `\newpage` between sections.
- **Fractions:** improper fractions with magnitude > 1 display as mixed numbers
  (`$1\frac{7}{12}$`); `\dfrac` in question bodies, `\frac` in the answer key.
- **Answer key:** the teacher copy is all problems, then `\newpage`, then one
  consolidated `\section*{Answer Key}` with a `\subsection*` per part. The
  student copy is a **separate `.tex` file** with no answer content at all.
- Both PDFs go to `out/`.
- **Never concatenate the two PDFs.** The teacher copy already contains every
  problem, so joining it to the student copy prints the whole worksheet twice
  before the key — this shipped once. A single-file hand-out is the teacher
  copy, unmodified: problems once, then the key. `tests/test_build.py`'s
  `test_teacher_copy_states_each_problem_exactly_once` holds the line.

## Filing a delivered worksheet

Worksheets given to a student live in `tutor/worksheets/<Student>/` as
`<YYYY-MM-DD>_<Name>_spec.yaml`, `..._student.tex`, `..._key.tex`, and a
single `<YYYY-MM-DD>_<Name>.pdf` — that PDF is the teacher copy (see above),
not a merge. `out/` is gitignored; worksheets are reproducible from the spec
plus the seed, so build delivered copies with `--no-history`, which makes the
output depend on the seed alone. Without it the anti-repeat ledger silently
shifts the draws between runs and the same seed stops reproducing the sheet.

### Coefficient rendering

Never build linear or polynomial text with f-strings. Use
`forge/core/latexfmt.py` (`coeff`, `linear`, `poly`, `terms`, `num`, `mixed`).
The bugs it exists to prevent, all covered by `tests/test_latexfmt.py`:

- `3x + 1y = 9` must render as `3x + y = 9`
- `y = -1x - 3` must render as `y = -x - 3`
- zero slope must give `y = 5`, not `y = 0x + 5`
- never `+ -3`; always `- 3`

Spec prose (title, section names, directions) passes through `tex_escape`,
which escapes only `&`, `%`, `#` — inline math in directions must survive.
Problem and answer bodies are never escaped.

## Anti-repetition ledger

`history/used.json` is a **global** history across all specs. Fingerprints used
in the last N runs (default 5) are rejected at draw time. After
`MAX_ATTEMPTS` the constraint is relaxed with a warning rather than hanging —
never make this loop unbounded.

Subskill quotas are **enforced, not sampled**: a section asking for 5 of a
subskill gets exactly 5, or the build raises.

## Versions

`--versions 3` produces fully independent draws (distinct seeds), labelled
A/B/C. Same seed always produces byte-identical `.tex` output.

## The topic catalog

`forge/catalog.py` turns a bare list of topics into a full spec, so the common
case needs no YAML at all. It holds the editorial defaults only — section
grouping, directions, work-space, and the default subskill progression. It
selects *which generators run*, never *which problems*.

A topic emits **one section per group**, because directions are stated once per
section and items are bare. Two subskills may share a section only when one set
of directions honestly covers both. "Evaluate each expression" covers all four
`negatives` subskills; "solve the proportion" and "find the percent change" do
not, so they are separate parts. When adding a subskill, ask what the directions
would have to say — if that sentence does not fit the section it is joining,
give it its own `group`.

`forge quick` writes the generated spec to disk alongside the PDFs so a good
worksheet can be reproduced, hand-edited, or committed.

## Commands

```bash
# no spec file needed -- topics, optionally topic:count or topic:count:difficulty
python -m forge quick negatives fractions linear_equations:12:hard --seed 42
# /subskill (joined with +) narrows a topic to part of its progression
python -m forge quick exponents/product_rule+quotient_rule:12:hard
python -m forge topics                      # list topics and subskills

python -m forge build specs/placement_algebra1.yaml --seed 42
python -m forge build specs/placement_algebra1.yaml --versions 3
python -m forge build specs/placement_algebra1.yaml --seed 1 --no-pdf --no-history
pytest
FORGE_FULL_FUZZ=1 pytest tests/test_generators.py   # full 1000-seed sweep (~8 min); default SEEDS=250 for local iteration
# PowerShell: $env:FORGE_FULL_FUZZ=1; pytest tests/test_generators.py
```
