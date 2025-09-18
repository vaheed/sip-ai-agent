#!/usr/bin/env python3
"""Build and install the pjsua2 Python bindings."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from urllib.request import urlretrieve

PJSIP_VERSION = "2.12"
PJSIP_URL = f"https://github.com/pjsip/pjproject/archive/{PJSIP_VERSION}.tar.gz"


def run_command(command: list[str], *, cwd: Path | None = None) -> None:
    """Run a subprocess command, echoing it to stdout."""
    display_cmd = " ".join(command)
    if cwd:
        print(f"[install_pjsua2] $ (cd {cwd} && {display_cmd})")
    else:
        print(f"[install_pjsua2] $ {display_cmd}")
    subprocess.run(command, check=True, cwd=cwd)


def ldconfig_available() -> bool:
    """Return True if ldconfig is available on this system."""
    return shutil.which("ldconfig") is not None


def running_as_root() -> bool:
    """Detect whether the current user is root (Unix-only)."""
    geteuid = getattr(os, "geteuid", None)
    if geteuid is None:
        return False
    return geteuid() == 0


def ensure_ld_library_path(prefix: Path | None) -> None:
    """Emit guidance when shared libraries are installed to a custom prefix."""
    if not prefix:
        return

    lib_dir = prefix / "lib"
    if not ldconfig_available():
        print(
            "[install_pjsua2] ldconfig not found; ensure your runtime linker can "
            "locate libraries under "
            f"{lib_dir} (e.g. by exporting LD_LIBRARY_PATH)."
        )
    elif not running_as_root():
        print(
            "[install_pjsua2] ldconfig requires elevated privileges. If you "
            "installed to a custom prefix, run ldconfig manually or update "
            f"LD_LIBRARY_PATH to include {lib_dir}."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and install pjsua2 bindings from pjproject")
    parser.add_argument(
        "--prefix",
        type=Path,
        default=None,
        help="Installation prefix to pass to configure. Defaults to system prefix.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Build even if pjsua2 is already importable.",
    )
    return parser.parse_args()


def pjsua2_already_installed() -> bool:
    try:
        import pjsua2  # type: ignore
    except ImportError:
        return False
    else:
        location = getattr(pjsua2, "__file__", "<unknown>")
        print(f"[install_pjsua2] Existing pjsua2 module detected at {location}.")
        return True


def build_and_install(prefix: Path | None) -> None:
    with tempfile.TemporaryDirectory(prefix="pjproject-") as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        archive_path = tmpdir / "pjproject.tar.gz"
        print(f"[install_pjsua2] Downloading pjproject {PJSIP_VERSION} from {PJSIP_URL}...")
        urlretrieve(PJSIP_URL, archive_path)

        print(f"[install_pjsua2] Extracting to {tmpdir}...")
        with tarfile.open(archive_path) as tar:
            tar.extractall(path=tmpdir)

        source_dir = tmpdir / f"pjproject-{PJSIP_VERSION}"
        if not source_dir.exists():
            raise RuntimeError(f"Extracted source directory {source_dir} not found")

        configure_cmd = ["./configure", "--enable-shared"]
        if prefix:
            configure_cmd.append(f"--prefix={prefix}")
        run_command(configure_cmd, cwd=source_dir)
        run_command(["make", "dep"], cwd=source_dir)
        run_command(["make"], cwd=source_dir)
        run_command(["make", "install"], cwd=source_dir)

        if ldconfig_available() and running_as_root():
            run_command(["ldconfig"])
        else:
            ensure_ld_library_path(prefix)

        swig_dir = source_dir / "pjsip-apps" / "src" / "swig"
        run_command(["make", "python"], cwd=swig_dir)

        python_dir = swig_dir / "python"
        run_command([sys.executable, "setup.py", "install"], cwd=python_dir)

    print("[install_pjsua2] Installation complete.")


def main() -> None:
    args = parse_args()
    if not args.force and pjsua2_already_installed():
        print("[install_pjsua2] Skipping build; rerun with --force to rebuild.")
        return

    build_and_install(args.prefix)


if __name__ == "__main__":
    main()
