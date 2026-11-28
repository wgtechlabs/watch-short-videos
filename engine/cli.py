import argparse
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

if __package__:
    from .captions import get_captions
else:
    from captions import get_captions


PLATFORMS = {
    "youtube.com": "youtube", "youtu.be": "youtube",
    "facebook.com": "facebook", "fb.watch": "facebook",
    "instagram.com": "instagram", "tiktok.com": "tiktok",
}
DOWNLOADER = ("yt-dlp", "--ignore-config", "--no-playlist", "--no-cache-dir")
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".mov", ".flv", ".3gp", ".ts", ".avi", ".m4v"}


def detect_platform(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Expected an http(s) video URL")
    host = parsed.hostname.lower()
    for domain, platform in PLATFORMS.items():
        if host == domain or host.endswith("." + domain):
            return platform
    raise ValueError("Unsupported video host")


def run(args, timeout=30):
    try:
        return subprocess.run(args, check=True, capture_output=True, text=True,
                              errors="replace", stdin=subprocess.DEVNULL, timeout=timeout).stdout
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{args[0]} timed out after {timeout} seconds") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip().splitlines()
        raise RuntimeError(detail[-1] if detail else f"{args[0]} exited with status {exc.returncode}") from exc


def download_video(url, folder):
    with TemporaryDirectory(dir=folder) as scratch:
        template = str(Path(scratch) / "video.%(ext)s")
        try:
            name = run([*DOWNLOADER, "--max-filesize", "250M", "--print", "after_move:filepath",
                        "-o", template, "--", url], timeout=180).strip()
        except RuntimeError as exc:
            raise RuntimeError(f"Could not download video. Check that the link is accessible. {exc}") from exc
        video = Path(name)
        if (video.parent != Path(scratch) or video.stem != "video"
                or not video.is_file() or not video.stat().st_size):
            raise RuntimeError("Download did not produce a video file. Check the link and size limit.")
        return video.replace(folder / video.name)


def extract(url, mode, output):
    platform = detect_platform(url)
    missing = [binary for binary in ("yt-dlp", "ffmpeg", "ffprobe") if not shutil.which(binary)]
    if missing:
        raise RuntimeError(f"Install {', '.join(missing)} and make it available on PATH")

    cache_key = hashlib.sha256(url.encode()).hexdigest()[:16]
    folder = output.resolve() / cache_key
    folder.mkdir(parents=True, exist_ok=True)
    existing = sorted(p for p in folder.glob("video.*")
                      if p.suffix in VIDEO_EXTENSIONS and p.is_file() and p.stat().st_size)
    video = existing[0] if existing else download_video(url, folder)
    try:
        metadata = json.loads(run(["ffprobe", "-v", "error", "-print_format", "json",
                                   "-show_format", str(video)]))
        duration = float(metadata.get("format", {}).get("duration", 0))
    except (RuntimeError, ValueError, TypeError) as exc:
        raise RuntimeError(f"Could not read video metadata. {exc}") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise RuntimeError("Unable to determine video duration")
    if duration > 600:
        raise RuntimeError("Video exceeds the 10-minute short-video limit")

    count = 8 if mode == "fast" else 24
    frames = folder / mode
    frames.mkdir(exist_ok=True)
    extracted = []
    with TemporaryDirectory(dir=folder) as scratch:
        for index in range(count):
            timestamp = (index + 0.5) * duration / count
            target = frames / f"frame_{index:03}.jpg"
            if not target.is_file() or not target.stat().st_size:
                staged = Path(scratch) / target.name
                try:
                    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(timestamp),
                         "-i", str(video), "-frames:v", "1", "-vf", "scale=640:-2", str(staged)])
                except RuntimeError as exc:
                    raise RuntimeError(f"Could not process video frame at {timestamp:.2f}s. {exc}") from exc
                if staged.is_file() and staged.stat().st_size:
                    staged.replace(target)
            if target.is_file() and target.stat().st_size:
                extracted.append({"timestamp_seconds": round(timestamp, 2), "path": str(target)})
        if not extracted:
            raise RuntimeError("Could not extract any images from the video")

        limitations = ["Uniform sampling may miss rapid changes", "Speech transcription is not implemented"]
        try:
            captions = get_captions(run, DOWNLOADER, url, folder)
            if captions is None:
                limitations.append("No supported WebVTT captions were available")
        except (RuntimeError, ValueError, OSError):
            captions = None
            limitations.append("Caption retrieval failed")
        result = {
            "source_url": url, "platform": platform, "mode": mode,
            "duration_seconds": duration, "video_path": str(video),
            "frames": extracted, "audio_transcript": None,
            "limitations": limitations, "captions": captions,
        }
        manifest = folder / f"context-{mode}.json"
        staged = Path(scratch) / manifest.name
        staged.write_text(json.dumps(result, indent=2), encoding="utf-8")
        staged.replace(manifest)
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
        print(extract(args.url, args.mode, args.output))
    except (ValueError, RuntimeError, OSError) as exc:
        parser.exit(1, f"Extraction failed: {exc}\n")


if __name__ == "__main__":
    main()
