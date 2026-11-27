import html
import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory


def timestamp(value):
    seconds = 0.0
    for part in value.split(":"):
        seconds = seconds * 60 + float(part)
    return round(seconds, 3)


def parse_vtt(data):
    cues = []
    for block in re.split(r"\n[ \t]*\n", data):
        lines = block.splitlines()
        if not lines or lines[0].startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        for index, line in enumerate(lines[:2]):
            match = re.fullmatch(r"((?:\d{2,}:)?\d{2}:\d{2}\.\d{3})\s+-->\s+"
                                 r"((?:\d{2,}:)?\d{2}:\d{2}\.\d{3})(?:\s+.*)?", line)
            if match:
                start, end = map(timestamp, match.groups())
                text = html.unescape(re.sub(r"<[^>]*>", "", " ".join(lines[index + 1:])))
                text = " ".join(text.split())
                if text and end > start:
                    cues.append({"start_seconds": start, "end_seconds": end, "text": text})
                break
    return cues


def get_captions(run, downloader, url, folder):
    info = json.loads(run([*downloader, "--dump-single-json", "--", url], timeout=60))
    attempted = False
    for field, option, source in (
        ("subtitles", "--write-subs", "creator"),
        ("automatic_captions", "--write-auto-subs", "automatic"),
    ):
        tracks = info.get(field) or {}
        languages = sorted(
            (lang for lang, formats in tracks.items()
             if re.fullmatch(r"[a-zA-Z0-9_-]+", lang)
             and any(fmt.get("ext") == "vtt" for fmt in formats)),
            key=lambda lang: (
                lang != info.get("language"),
                not lang.endswith("-orig"),
                lang.split("-")[0] != "en",
                lang,
            ),
        )
        if not languages:
            continue
        language = languages[0]
        attempted = True
        with TemporaryDirectory(dir=folder) as scratch:
            template = str(Path(scratch).resolve() / "captions.%(ext)s")
            try:
                run([*downloader, "--skip-download", option, "--sub-langs", language,
                     "--sub-format", "vtt", "-o", template, "--", url], timeout=60)
                path = Path(scratch) / f"captions.{language}.vtt"
                if path.is_file():
                    cues = parse_vtt(path.read_text(encoding="utf-8-sig"))
                    if cues:
                        return {"source": source, "language": language, "cues": cues}
            except (RuntimeError, OSError, UnicodeError):
                continue
    if attempted:
        raise RuntimeError("Available caption tracks could not be read")
    return None
