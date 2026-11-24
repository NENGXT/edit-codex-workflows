"""Prepare pinned official GPT-SoVITS v5 Turbo. No reference files are uploaded."""
import os
os.environ["ORT_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

import argparse
import hashlib
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile

COMMIT = "04a44eb977586645f33594b72af13a035a2056c6"
REPO = "https://github.com/RVC-Boss/GPT-SoVITS.git"
HERE = pathlib.Path(__file__).resolve().parent


def sha256(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verified_download(url, path, expected, size=None):
    path = pathlib.Path(path)
    if path.exists():
        if sha256(path) == expected and (size is None or path.stat().st_size == size):
            print("CACHED", path.name, flush=True)
            return
        raise RuntimeError(f"Existing file fails checksum; inspect manually: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".partial")
    with urllib.request.urlopen(url, timeout=180) as response, part.open("wb") as out:
        shutil.copyfileobj(response, out, length=1024 * 1024)
    if size is not None and part.stat().st_size != size:
        raise RuntimeError(f"Wrong size: {path.name}")
    if sha256(part) != expected:
        raise RuntimeError(f"Wrong SHA-256: {path.name}; not loading it")
    part.replace(path)
    print("VERIFIED", path.name, flush=True)


def command(args, **kwargs):
    print("RUN", " ".join(map(str, args)), flush=True)
    return subprocess.run(list(map(str, args)), check=True, timeout=2400, **kwargs)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=pathlib.Path, default=pathlib.Path("/kaggle/working/gsv-v5"))
    p.add_argument("--allow-downloads-and-install", action="store_true")
    args = p.parse_args()
    if not args.allow_downloads_and_install:
        p.error("Setup is opt-in. Pass --allow-downloads-and-install only when authorized.")
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("CPU baseline used Python 3.12; stop and review this runtime rather than silently change it.")
    if not pathlib.Path("/kaggle").exists():
        raise RuntimeError("This setup is intended for Kaggle, not the current cloud computer or a Mac.")
    for executable in ("git", "gcc", "g++", "ffmpeg", "nvidia-smi"):
        if not shutil.which(executable):
            raise RuntimeError(f"Missing {executable}; review before changing system packages.")
    gpu_probe = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"],
        capture_output=True, text=True, timeout=30)
    if gpu_probe.returncode or "T4" not in gpu_probe.stdout:
        raise RuntimeError(f"Kaggle T4 preflight failed before installation: exit={gpu_probe.returncode}; "
                           f"stdout={gpu_probe.stdout.strip()}; stderr={gpu_probe.stderr.strip()}")
    print("GPU_PREFLIGHT", gpu_probe.stdout.strip(), flush=True)
    args.root = args.root.resolve()
    args.root.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(args.root).free < 14 * 1024**3:
        raise RuntimeError("Require at least 14 GiB free for isolated environment, weights and temporary downloads.")
    started = time.perf_counter()
    source = args.root / "source"
    if not source.exists():
        command(["git", "init", source])
        command(["git", "-C", source, "remote", "add", "origin", REPO])
        command(["git", "-C", source, "fetch", "--depth", "1", "origin", COMMIT])
        command(["git", "-C", source, "checkout", "--detach", "FETCH_HEAD"])
    actual = subprocess.check_output(["git", "-C", source, "rev-parse", "HEAD"], text=True).strip()
    if actual != COMMIT:
        raise RuntimeError(f"Unexpected source commit: {actual}")
    status = subprocess.check_output(["git", "-C", source, "status", "--porcelain=v1", "--untracked-files=all"], text=True).splitlines()
    dirty = [line[3:] for line in status]
    allowed = {"GPT_SoVITS/configs/tts_infer.yaml", "GPT_SoVITS/text/g2pw/polyphonic.md5"}
    if set(dirty) - allowed:
        raise RuntimeError(f"Unexpected source edits: {dirty}")

    venv = args.root / ".venv"
    if not venv.exists():
        # Kaggle may provide Python 3.12 without its optional ensurepip package.
        venv_args = [sys.executable, "-m", "venv"]
        if importlib.util.find_spec("ensurepip") is None:
            venv_args.append("--without-pip")
        command(venv_args + [venv])
    python = venv / "bin/python"
    env = os.environ.copy()
    env.update({"CC": "gcc", "CXX": "g++", "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PIP_NO_CACHE_DIR": "1"})
    if not python.exists() or not (venv / "pyvenv.cfg").is_file():
        raise RuntimeError("Existing .venv is incomplete. Inspect it manually; no files were deleted.")
    interpreter = json.loads(subprocess.check_output([python, "-c",
        "import sys,json; print(json.dumps({'version':list(sys.version_info[:2]),"
        "'prefix':sys.prefix,'base_prefix':sys.base_prefix}))"], text=True))
    if (interpreter["version"] != [3, 12] or
            pathlib.Path(interpreter["prefix"]).resolve() != venv.resolve() or
            interpreter["prefix"] == interpreter["base_prefix"]):
        raise RuntimeError("Existing environment is not the expected isolated Python 3.12 venv.")
    # Also recovers a valid partial venv left by an earlier ensurepip failure.
    pip_present = subprocess.check_output([python, "-c",
        "import importlib.util; print(int(importlib.util.find_spec('pip') is not None))"], text=True).strip()
    if pip_present == "0":
        uv = shutil.which("uv")
        if uv is None:
            raise RuntimeError("Venv pip is missing and preinstalled uv is unavailable; no system packages were changed.")
        command([uv, "pip", "install", "--python", python, "--no-cache", "pip==25.1.1"], env=env)
    command([python, "-m", "pip", "--version"], env=env)
    # Pin the same PyTorch release, changing only CPU build to CUDA 12.6 build.
    command([python, "-m", "pip", "install", "--index-url", "https://download.pytorch.org/whl/cu126",
             "torch==2.7.1+cu126", "torchaudio==2.7.1+cu126"], env=env)
    # CPU ONNX Runtime is intentional: preserve baseline Chinese G2PW frontend.
    command([python, "-m", "pip", "install", "--no-binary=opencc", "-r", HERE / "requirements-lock.txt",
             "-c", HERE / "cuda-constraints.txt"], env=env)
    command([python, "-m", "pip", "check"], env=env)
    with (args.root / "installed-packages.txt").open("w") as out:
        command([python, "-m", "pip", "freeze"], stdout=out, env=env)

    manifest = json.loads((HERE / "models-manifest.json").read_text())
    dest = source / "GPT_SoVITS/pretrained_models"
    for item in manifest["files"]:
        url = f'https://huggingface.co/{manifest["repo"]}/resolve/{manifest["revision"]}/{item["path"]}'
        verified_download(url, dest / item["path"], item["sha256"], item["size"])
    g2pw = args.root / "downloads/G2PWModel.zip"
    verified_download("https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/G2PWModel.zip",
                      g2pw, "46292be0374a49308069233cd5c147ae4c41806558e4781a2467a31a4d8099da", 588856634)
    target = source / "GPT_SoVITS/text"
    with zipfile.ZipFile(g2pw) as archive:
        for member in archive.infolist():
            path = pathlib.PurePosixPath(member.filename)
            if path.is_absolute() or ".." in path.parts or path.parts[0] != "G2PWModel":
                raise RuntimeError("Unsafe G2PW archive member")
            if ((member.external_attr >> 16) & 0o170000) == 0o120000:
                raise RuntimeError("Unexpected symlink in G2PW archive")
        archive.extractall(target)
    verified_download("https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin",
                      dest / "fast_langdetect/lid.176.bin",
                      "7e69ec5451bc261cc7844e49e4792a85d7f09c06789ec800fc4a44aec362764e")
    auxiliary = json.loads((HERE / "auxiliary-assets-manifest.json").read_text())
    for item in auxiliary["files"]:
        if sha256(source / item["path"]) != item["sha256"]:
            raise RuntimeError(f'Auxiliary asset mismatch: {item["path"]}')
    gpu_inventory = subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
                                            "--format=csv,noheader"], text=True).strip()
    report = {"source_repo": REPO, "commit": COMMIT,
              "models": manifest, "auxiliary_assets": auxiliary, "gpu_inventory": gpu_inventory,
              "setup_seconds": time.perf_counter() - started,
              "reference_uploaded_by_setup": False, "model_inference_executed_by_setup": False}
    (args.root / "setup-report.json").write_text(json.dumps(report, indent=2))
    print("SETUP_COMPLETE", json.dumps({"seconds": report["setup_seconds"], "root": str(args.root)}), flush=True)


if __name__ == "__main__":
    main()
