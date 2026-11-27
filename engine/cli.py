import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

PLATFORMS = {
    "youtube.com": "youtube", "youtu.be": "youtube",
    "facebook.com": "facebook", "fb.watch": "facebook",
    "instagram.com": "instagram", "tiktok.com": "tiktok",
}

def detect_platform(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Expected an http(s) video URL")
    host = parsed.hostname.lower()
    for domain, platform in PLATFORMS.items():
        if host == domain or host.endswith("." + domain):
            return platform
    raise ValueError("Unsupported video host")

def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout

def extract(url, mode, output):
    platform = detect_platform(url)
    for binary in ("yt-dlp", "ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            raise RuntimeError(f"Missing required executable: {binary}")
    cache_key = hashlib.sha256(url.encode()).hexdigest()[:16]
    folder = output / cache_key
    folder.mkdir(parents=True, exist_ok=True)
    template = str(folder / "video.%(ext)s")
    existing = sorted(p for p in folder.glob("video.*") if p.suffix not in (".part", ".json"))
    if not existing:
        run(["yt-dlp", "--no-playlist", "--max-filesize", "250M", "-o", template, url])
        existing = sorted(p for p in folder.glob("video.*") if p.suffix not in (".part", ".json"))
    if not existing:
        raise RuntimeError("No downloaded video found")
    video = existing[0]
    metadata = json.loads(run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(video)]))
    duration = float(metadata.get("format", {}).get("duration", 0))
    if duration <= 0:
        raise RuntimeError("Unable to determine video duration")
    if duration > 600:
        raise RuntimeError("Video exceeds the 10-minute short-video safety limit")
    count = 8 if mode == "fast" else 24
    frames = folder / mode
    frames.mkdir(exist_ok=True)
    timestamps = [(i + 0.5) * duration / count for i in range(count)]
    extracted = []
    for index, timestamp in enumerate(timestamps):
        target = frames / f"frame_{index:03}.jpg"
        if not target.exists():
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(timestamp), "-i", str(video),
                 "-frames:v", "1", "-vf", "scale=640:-2", "-y", str(target)])
        if target.exists():
            extracted.append({"timestamp_seconds": round(timestamp, 2), "path": str(target.resolve())})
    result = {
        "source_url": url, "platform": platform, "mode": mode,
        "duration_seconds": duration, "video_path": str(video.resolve()),
        "frames": extracted, "audio_transcript": None,
        "limitations": ["Uniform sampling may miss rapid changes", "Speech transcription not implemented in MVP"]
    }
    manifest = folder / f"context-{mode}.json"
    manifest.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return manifest

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("extract")
    p.add_argument("url")
    p.add_argument("--mode", choices=("fast", "full"), default="fast")
    p.add_argument("--output", type=Path, default=Path(".watch-short-videos-cache"))
    args = parser.parse_args()
    try:
        manifest = extract(args.url, args.mode, args.output)
        print(manifest.resolve())
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Extraction failed: {exc}\n")

if __name__ == "__main__":
    main()
