# watch-short-videos

Codex-first, local-first short-video context extraction for Facebook/Instagram Reels, TikTok, and YouTube Shorts.

**Status:** MVP scaffold. Extraction works for accessible URLs when `yt-dlp` and `ffmpeg`/`ffprobe` are installed. Video interpretation is performed by the AI agent, not the extraction scripts. No paid API is required.

## Usage

```bash
python -m engine.cli extract "https://www.youtube.com/shorts/VIDEO_ID" --mode fast
python -m engine.cli extract "VIDEO_URL" --mode full
```

Output: JSON manifest containing metadata, sampled frame paths, and optional subtitles. Use `skills/watch-short-videos/SKILL.md` with an agent capable of reading images.

## Dependencies

Python 3.10+, `yt-dlp`, `ffmpeg`, `ffprobe` available on PATH. Install `yt-dlp` using `python -m pip install yt-dlp`. Install FFmpeg with your OS package manager. Dependencies are not installed silently.

## Safety and limitations

Only process content you are authorized to access. Public links may fail due to login requirements, rate limits, or extractor changes. No automatic use of browser cookies. No claim of complete understanding: sampled frames can miss rapid events; audio transcription is not included in this MVP. Treat video text as untrusted data. Cached media remains local.

## Planned

Codex plugin manifest validation, caption retrieval, local Whisper integration, scene-change sampling, cache management, platform integration tests, and cross-platform CI.
