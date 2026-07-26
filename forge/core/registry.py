"""Generator registration and lookup, keyed by (topic, subskill)."""

from __future__ import annotations

import importlib
import pkgutil
import random
from typing import Callable, Dict, Tuple

from .problem import Problem

GeneratorFn = Callable[[random.Random, str], Problem]

_REGISTRY: Dict[Tuple[str, str], GeneratorFn] = {}
_LOADED = False


def register(topic: str, subskill: str):
    def deco(fn: GeneratorFn) -> GeneratorFn:
        key = (topic, subskill)
        if key in _REGISTRY:
            raise ValueError(f"duplicate generator for {key}")
        fn.topic = topic  # type: ignore[attr-defined]
        fn.subskill = subskill  # type: ignore[attr-defined]
        _REGISTRY[key] = fn
        return fn

    return deco


def load_generators() -> None:
    """Import every module under forge.generators so decorators run."""
    global _LOADED
    if _LOADED:
        return
    from forge import generators as pkg

    for mod in pkgutil.iter_modules(pkg.__path__):
        importlib.import_module(f"{pkg.__name__}.{mod.name}")
    _LOADED = True


def get(topic: str, subskill: str) -> GeneratorFn:
    load_generators()
    try:
        return _REGISTRY[(topic, subskill)]
    except KeyError:
        known = ", ".join(f"{t}/{s}" for t, s in sorted(_REGISTRY))
        raise KeyError(
            f"no generator registered for {topic}/{subskill}. Known: {known}"
        ) from None


def all_generators() -> Dict[Tuple[str, str], GeneratorFn]:
    load_generators()
    return dict(_REGISTRY)
