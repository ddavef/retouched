#!/usr/bin/env python3
import json, os, shutil, sys, zipfile, subprocess, stat
from pathlib import Path
from urllib.request import urlopen, Request

BASE_DIR = Path(__file__).resolve().parent
IGNORE_DIR = BASE_DIR / "ignore"
APK_PATH = IGNORE_DIR / "Touchy.1.7.apk"
DECOMP_DIR = IGNORE_DIR / "Touchy.1.7.apk-decompiled"
DIST_DIR = IGNORE_DIR / "dist"
SIGNED_DIR = IGNORE_DIR / "signed"

APKTOOL_DL_PAGE = "https://bitbucket.org/iBotPeaches/apktool/downloads/"
JADX_RELEASE_API = "https://api.github.com/repos/skylot/jadx/releases/latest"
UBER_RELEASE_API = "https://api.github.com/repos/patrickfav/uber-apk-signer/releases/latest"

UA = {"User-Agent": "python"}

def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(Request(url, headers=UA)) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)

def latest_apktool(dest: Path) -> Path:
    api = "https://api.bitbucket.org/2.0/repositories/iBotPeaches/apktool/downloads?pagelen=50"
    with urlopen(Request(api, headers=UA)) as r:
        data = json.load(r)
    for item in data.get("values", []):
        name = item.get("name", "")
        if name.endswith(".jar") and "apktool_" in name:
            dl = item.get("links", {}).get("self", {}).get("href")
            if not dl:
                continue
            download(dl, dest)
            return dest
    raise RuntimeError("No apktool jar link found via API")

def latest_jadx(dest_zip: Path, dest_dir: Path) -> Path:
    with urlopen(Request(JADX_RELEASE_API, headers=UA)) as r:
        data = json.load(r)
    asset = next((a for a in data.get("assets", [])
                  if a["name"].startswith("jadx-") and a["name"].endswith(".zip")
                  and "sources" not in a["name"] and "gui" not in a["name"]), None)
    if not asset:
        raise RuntimeError("No jadx zip asset found")
    download(asset["browser_download_url"], dest_zip)
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    with zipfile.ZipFile(dest_zip, "r") as zf:
        zf.extractall(dest_dir)
    return dest_dir

def latest_uber(dest: Path) -> Path:
    with urlopen(Request(UBER_RELEASE_API, headers=UA)) as r:
        data = json.load(r)
    asset = next((a for a in data.get("assets", [])
                  if a["name"].endswith(".jar") and "uber-apk-signer" in a["name"]), None)
    if not asset:
        raise RuntimeError("No uber apk signer asset found")
    download(asset["browser_download_url"], dest)
    return dest

def make_executable(path: Path):
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def run_cmd(cmd):
    print("Running:", " ".join(cmd))
    subprocess.check_call(cmd)

def ensure_tools():
    apktool_path = IGNORE_DIR / "apktool.jar"
    if not apktool_path.exists():
        apktool_path = latest_apktool(apktool_path)

    uber_path = IGNORE_DIR / "uber-apk-signer.jar"
    if not uber_path.exists():
        uber_path = latest_uber(uber_path)

    jadx_root = IGNORE_DIR / "jadx"
    if not jadx_root.exists():
        latest_jadx(IGNORE_DIR / "jadx.zip", jadx_root)
    jadx_bin = "jadx.bat" if os.name == "nt" else "jadx"
    jadx_path = next((p for p in jadx_root.rglob(jadx_bin)), None)
    if not jadx_path:
        raise RuntimeError("jadx executable not found")
    if os.name != "nt":
        make_executable(jadx_path)
    return apktool_path, jadx_path, uber_path

def patch_strings(ip: str):
    strings_xml = DECOMP_DIR / "res" / "values" / "strings.xml"
    if not strings_xml.exists():
        raise FileNotFoundError(f"Missing strings.xml at {strings_xml}")
    content = strings_xml.read_text(encoding="utf-8")
    replacements = {
        'registry.monkeysecurity.com': ip,
        'http://registry.monkeysecurity.com:8080': f"http://{ip}:8080",
        'http://playbrassmonkey.com/alternate-hosts.json': f"http://{ip}/alternate-hosts.json",
        'https://registry.monkeysecurity.com': f"https://{ip}",
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    strings_xml.write_text(content, encoding="utf-8")

def confirm_cleanup():
    targets = []
    if DECOMP_DIR.exists():
        targets.append(str(DECOMP_DIR))
    if SIGNED_DIR.exists():
        targets.append(str(SIGNED_DIR))
    if not targets:
        return
    print("Warning: the following directories will be deleted since the script was already run:\n- " + "\n- ".join(targets))
    if input("Proceed? [y/N]: ").strip().lower() != "y":
        sys.exit("Aborted by user.")

def main():
    IGNORE_DIR.mkdir(parents=True, exist_ok=True)
    if not APK_PATH.exists():
        sys.exit(f"APK not found at {APK_PATH}. Place Touchy.1.7.apk in the ignore directory and retry. Is the APK name correct?")
    ip = input("Enter IP address to inject: ").strip()
    if not ip:
        sys.exit("No IP provided; aborting.")
    apktool_path, jadx_path, uber_path = ensure_tools()

    confirm_cleanup()

    if DECOMP_DIR.exists():
        shutil.rmtree(DECOMP_DIR)
    DECOMP_DIR.mkdir(parents=True, exist_ok=True)

    run_cmd([
        "java", "-Xmx256m", "-jar", str(apktool_path),
        "d", "-f", "-o", str(DECOMP_DIR), str(APK_PATH)
    ])

    run_cmd([
        str(jadx_path), "-r", "-d", str(DECOMP_DIR), str(APK_PATH)
    ])

    patch_strings(ip)

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    run_cmd([
        "java", "-Xmx256m", "-jar", str(apktool_path),
        "b", str(DECOMP_DIR), "-o", str(DIST_DIR / "Touchy.1.7-rebuilt.apk")
    ])

    if SIGNED_DIR.exists():
        shutil.rmtree(SIGNED_DIR)
    SIGNED_DIR.mkdir(parents=True, exist_ok=True)
    run_cmd([
        "java", "-Xmx256m", "-jar", str(uber_path),
        "--apks", str(DIST_DIR / "Touchy.1.7-rebuilt.apk"),
        "--out", str(SIGNED_DIR)
    ])

    print(f"Signed APK in {SIGNED_DIR}")

if __name__ == "__main__":
    main()
