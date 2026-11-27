# watch-short-videos

Get a timestamped summary of a short video in Codex using locally extracted frames and available WebVTT captions.

## Quickstart

1. Install Python 3.10+, [yt-dlp](https://github.com/yt-dlp/yt-dlp#installation), and [FFmpeg](https://ffmpeg.org/download.html) (including ffprobe). Check that `python3 --version`, `yt-dlp --version`, `ffmpeg -version`, and `ffprobe -version` work in your terminal. Some YouTube videos also require a [supported JavaScript runtime](https://github.com/yt-dlp/yt-dlp/wiki/EJS).
2. Register the GitHub marketplace and install its local plugin:

   ```sh
   codex plugin marketplace add wgtechlabs/watch-short-videos
   codex plugin add watch-short-videos@wgtechlabs-video-tools
   ```

3. Open a new Codex chat and try: “Use Watch Short Videos to summarize this YouTube Short. Include timestamps for what you see and what the captions say: <URL>.”

## CLI

From the repository root:

```sh
python3 -m engine.cli extract "https://www.youtube.com/shorts/VIDEO_ID"
python3 -m engine.cli extract "VIDEO_URL" --mode full --output ./video-cache
```

The command prints the JSON manifest path. Fast samples up to 8 frames and Full up to 24. The manifest includes the video path, duration, timestamped frame paths, limitations, and a nullable `captions` field. Caption objects contain a `source` (creator or automatic), `language`, and `cues` with start/end times in seconds and text. Within a source, the media language and original tracks take priority, then English, then the next available track. Visual extraction remains available if captions cannot be retrieved.

Downloaded videos, frames, and manifests stay in `.watch-short-videos-cache/` under the working directory unless `--output` is set. Delete the cache directory you used to remove those files when no extraction is running.

## Platform support

The CLI recognizes YouTube, TikTok, Instagram, and Facebook URLs. Availability depends on the individual link, the platform, and your yt-dlp version. Only use links you are authorized to access. The plugin does not use browser cookies or transcribe audio. Uniform frame sampling can miss rapid events.

In the v0.2 smoke check, one public sample each from YouTube Shorts, TikTok, Instagram Reels, and Facebook Reels produced eight frames. The YouTube sample also returned captions. Results vary by link.

## Tests

Run `python3 -m unittest discover -s tests -v` with FFmpeg and ffprobe on PATH. Tests use a generated local video and controlled downloader responses.

## Releases

Run **Tests and release** manually from the Actions tab on `main`. The release job waits for both test jobs, then uses Clean Commit messages to calculate the version, update the manifests and changelog, and create the GitHub release.
