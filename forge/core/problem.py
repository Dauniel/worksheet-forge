"""The single data structure every generator returns."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

DIFFICULTIES = ("easy", "medium", "hard")


def normalize(question_latex: str) -> str:
    """Collapse a question to a canonical form for hashing.

    Two problems that a student would experience as identical must normalize to
    the same string, so whitespace and math-mode delimiters are stripped.
    """
    s = question_latex.strip()
    s = s.replace("$", " ")
    s = s.replace(r"\dfrac", r"\frac")  # display vs inline fractions are the same problem
    s = re.sub(r"\\[,;:!]", " ", s)  # latex spacing macros
    s = re.sub(r"\s+", "", s)
    return s


def fingerprint_of(question_latex: str, topic: str, subskill: str) -> str:
    payload = f"{topic}|{subskill}|{normalize(question_latex)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Problem:
    question_latex: str
    answer_latex: str
    answer_expr: Any
    topic: str
    subskill: str
    difficulty: str
    fingerprint: str = ""
    # Free-form data the verifier uses to re-derive the answer independently
    # of however the generator arrived at it.
    verify: dict = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        if not self.fingerprint:
            object.__setattr__(
                self,
                "fingerprint",
                fingerprint_of(self.question_latex, self.topic, self.subskill),
            )
        if self.difficulty not in DIFFICULTIES:
            raise ValueError(f"bad difficulty {self.difficulty!r}")
