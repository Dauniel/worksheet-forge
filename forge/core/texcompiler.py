"""Locate a LaTeX compiler, fetching one if the machine has none.

Priority, cheapest and least surprising first:

1. A tectonic binary already cached from a previous run of this tool.
2. ``pdflatex`` on PATH -- if the user already has a TeX distribution
   (MacTeX/TeX Live/MiKTeX) installed, use it and never touch the network.
3. ``tectonic`` on PATH -- likewise, respect an existing install.
4. Download tectonic (a small, self-contained, single-binary LaTeX engine)
   from its GitHub releases into a local cache and use that. This is what
   makes a fresh clone + ``pip install -e .`` produce a PDF on a machine
   with no TeX distribution at all.

Set ``WORKSHEET_FORGE_NO_DOWNLOAD=1`` (or pass ``allow_download=False``) to
disable step 4, e.g. in offline CI.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import stat
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

RELEASES_API = "https://api.github.com/repos/tectonic-typesetting/tectonic/releases/latest"
_BIN_NAME = "tectonic.exe" if platform.system() == "Windows" else "tectonic"


class DownloadError(RuntimeError):
    pass


def cache_dir() -> Path:
    override = os.environ.get("WORKSHEET_FORGE_CACHE")
    if override:
        return Path(override)
    if platform.system() == "Windows":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "worksheet-forge" / "bin"
    return Path.home() / ".cache" / "worksheet-forge" / "bin"


def _cached_tectonic() -> Optional[Path]:
    candidate = cache_dir() / _BIN_NAME
    return candidate if candidate.exists() else None


def _platform_asset_markers() -> list[str]:
    system = platform.system()
    machine = platform.machine().lower()
    arm = machine in ("arm64", "aarch64")
    if system == "Windows":
        return ["pc-windows-msvc"]
    if system == "Darwin":
        return ["aarch64-apple-darwin"] if arm else ["x86_64-apple-darwin"]
    if system == "Linux":
        return ["aarch64-unknown-linux-musl"] if arm else ["x86_64-unknown-linux-musl"]
    raise DownloadError(f"no tectonic build known for platform {system!r}/{machine!r}")


def _pick_asset(assets: list[dict]) -> dict:
    markers = _platform_asset_markers()
    for asset in assets:
        name = asset.get("name", "")
        if all(m in name for m in markers) and (name.endswith(".zip") or name.endswith(".tar.gz")):
            return asset
    raise DownloadError(
        f"could not find a tectonic release asset matching {markers}; "
        "install a TeX distribution manually or set PATH."
    )


def _extract_binary(archive_path: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as zf:
            name = next(n for n in zf.namelist() if n.endswith(_BIN_NAME))
            with zf.open(name) as src, open(dest_dir / _BIN_NAME, "wb") as dst:
                shutil.copyfileobj(src, dst)
    else:
        with tarfile.open(archive_path) as tf:
            name = next(n for n in tf.getnames() if n.endswith("tectonic"))
            member = tf.getmember(name)
            with tf.extractfile(member) as src, open(dest_dir / _BIN_NAME, "wb") as dst:
                shutil.copyfileobj(src, dst)
    out = dest_dir / _BIN_NAME
    if platform.system() != "Windows":
        out.chmod(out.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return out


def download_tectonic() -> Path:
    """Fetch the latest tectonic release for this platform into the cache dir."""
    try:
        with urllib.request.urlopen(RELEASES_API, timeout=30) as resp:
            release = json.loads(resp.read())
    except Exception as e:  # network down, rate-limited, DNS, etc.
        raise DownloadError(f"could not reach GitHub to fetch tectonic: {e}") from e

    asset = _pick_asset(release.get("assets", []))
    with tempfile.TemporaryDirectory() as td:
        archive_path = Path(td) / asset["name"]
        try:
            urllib.request.urlretrieve(asset["browser_download_url"], archive_path)
        except Exception as e:
            raise DownloadError(f"could not download tectonic: {e}") from e
        return _extract_binary(archive_path, cache_dir())


def resolve_compiler(allow_download: bool = True) -> tuple[str, str]:
    """Return (kind, executable_path) where kind is 'tectonic' or 'pdflatex'.

    Raises DownloadError if nothing is available and downloading is
    disabled or fails.
    """
    cached = _cached_tectonic()
    if cached is not None:
        return "tectonic", str(cached)

    pdflatex = shutil.which("pdflatex")
    if pdflatex is not None:
        return "pdflatex", pdflatex

    tectonic_on_path = shutil.which("tectonic")
    if tectonic_on_path is not None:
        return "tectonic", tectonic_on_path

    no_download_env = os.environ.get("WORKSHEET_FORGE_NO_DOWNLOAD") == "1"
    if not allow_download or no_download_env:
        raise DownloadError(
            "no LaTeX compiler found (pdflatex/tectonic) and downloading is disabled."
        )

    print("No LaTeX compiler found -- fetching tectonic (one-time, ~30MB)...")
    path = download_tectonic()
    print(f"tectonic installed at {path}")
    return "tectonic", str(path)
