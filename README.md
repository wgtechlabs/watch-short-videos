# watch-short-videos

![watch-short-videos banner with the subtitle Short videos, timestamped in Codex](<https://ghrb.waren.build/render/banner?header=watch-short-videos&subheader=Short+videos%2C+timestamped+in+Codex&bg=101E35-244872&color=F6FAFF&subheadercolor=C5DCFF&headerfont=Inter&subheaderfont=Inter&stats=false>)
<!-- Created with GitHub Repo Banner by Waren Gonzaga: https://ghrb.waren.build -->

A local Codex plugin and Python CLI for summarizing short videos. It samples frames, collects available captions, and gives Codex timestamps for what it sees and what the captions say.

## ✨ Features

- Extracts timestamped frames from accessible YouTube Shorts, TikToks, Instagram Reels, and Facebook Reels.
- Prefers creator-provided WebVTT captions, then tries automatic captions. Frame extraction still works when captions are unavailable.
- Keeps media and JSON manifests on your machine.

## 🚀 Getting Started

Install Python 3.10+, [yt-dlp](https://github.com/yt-dlp/yt-dlp#installation), and [FFmpeg](https://ffmpeg.org/download.html) (including `ffprobe`). Make sure `python3`, `yt-dlp`, `ffmpeg`, and `ffprobe` are on your PATH. Some YouTube videos also need a [JavaScript runtime supported by yt-dlp](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

Register the marketplace and install the plugin in Codex:

```sh
codex plugin marketplace add wgtechlabs/watch-short-videos
codex plugin add watch-short-videos@wgtechlabs-video-tools
```

## 📖 Usage

Start a new Codex chat and replace `<URL>` with a video you’re authorized to access:

> Use Watch Short Videos to summarize `<URL>`. Include timestamps for what you see and what the captions say.

Codex reads the sampled frames and attributes caption text separately. Uniform sampling can miss quick events. The plugin uses available captions and does not transcribe audio or use browser cookies.

### Use the CLI directly

From a clone of this repository, run:

```sh
python3 -m engine.cli extract "https://www.youtube.com/shorts/VIDEO_ID"
python3 -m engine.cli extract "VIDEO_URL" --mode full --output ./video-cache
```

The CLI prints the path to a JSON manifest with the video path, duration, frame timestamps and paths, and extraction limits. If available, `captions` contains the source (`creator` or `automatic`), language, and cues with start and end times in seconds. If captions are unavailable, the field is `null`.

## ⚙️ Configuration

- `--mode fast` is the default and samples up to 8 frames. Use `--mode full` for up to 24.
- `--output` sets the cache directory. The default is `.watch-short-videos-cache/` under the working directory. Delete the cache directory you used to remove the downloaded media, frames, and manifests when no extraction is running.
- Caption selection tries up to three tracks per source. Within each source, it prefers the media language, then original tracks, then English, then other available tracks.

## 📚 Documentation

- [Codex skill instructions](skills/watch-short-videos/SKILL.md) describe how the plugin turns frames and captions into a summary.
- [Clean README specification](https://github.com/wgtechlabs/clean-readme/blob/main/SPECIFICATION.md) defines this README’s structure.

## 🛠️ Development

From the repository root, with FFmpeg and ffprobe on PATH:

```sh
python3 -m unittest discover -s tests -v
```

The offline suite uses a generated local video and controlled downloader responses. GitHub Actions runs the suite on Linux and macOS.

### Releases

Run **Tests and release** manually from the Actions tab on `main`. The release job waits for both test jobs. It uses Clean Commit messages to calculate the version, then updates the manifests and changelog and creates the GitHub release.

### Recover a release after its tag was pushed

If the workflow pushed a tag but failed to create the release, verify the tag points to the intended commit and no GitHub release exists for it. Substitute that existing tag for `v0.2.0`:

```sh
gh release create v0.2.0 --repo wgtechlabs/watch-short-videos --verify-tag --generate-notes
```

The [GitHub CLI](https://cli.github.com/manual/gh_release_create) verifies the remote tag and generates release notes without creating or moving the tag.

## 🤝 Contributing

Branch from `dev` and open your pull request against `dev`. Follow [Clean Commit](https://github.com/wgtechlabs/clean-commit) and include the checks you ran.

## 🐛 Issues & Support

Search or open an issue on [GitHub](https://github.com/wgtechlabs/watch-short-videos/issues). Include the platform, your yt-dlp version, and the error message. Share a sample link only if it’s public and you’re authorized to share it.

Availability varies by link and downloader version. In the v0.2 smoke check, one public sample per supported platform produced eight frames. The YouTube sample also returned creator captions.

## 📄 License

Licensed under the [MIT License](LICENSE).

## 👥 Authors & Contributors

Maintained by [WG Technology Labs](https://github.com/wgtechlabs). See the [contributors](https://github.com/wgtechlabs/watch-short-videos/graphs/contributors).
