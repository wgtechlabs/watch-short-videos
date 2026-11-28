import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engine import cli
from engine.captions import get_captions

URL = "https://www.youtube.com/shorts/test"
WEBVTT = "WEBVTT\n\n00:00:00.100 --> 00:00:01.500\n<c>Hello &amp; welcome</c>\n"


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        directory = self.enter_temp_directory()
        key = hashlib.sha256(URL.encode()).hexdigest()[:16]
        self.cache = directory / key
        self.output = directory

    def enter_temp_directory(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return Path(directory.name)

    def create_video(self):
        self.cache.mkdir()
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                        "-i", "color=s=96x64:r=30:d=2", "-c:v", "mpeg4",
                        str(self.cache / "video.mp4")], check=True, timeout=30)

    def downloader(self, tracks, unavailable=()):
        def run(args, timeout=30):
            if args[0] != "yt-dlp":
                return cli_run(args, timeout=timeout)
            if "--dump-single-json" in args:
                return json.dumps(tracks)
            option = args[args.index("--sub-langs") + 1]
            if option in unavailable:
                raise RuntimeError("Caption URL expired")
            template = args[args.index("-o") + 1]
            Path(template.replace("%(ext)s", f"{option}.vtt")).write_text(WEBVTT)
            return ""
        cli_run = cli.run
        return run

    def test_both_modes_with_and_without_creator_captions(self):
        self.create_video()
        tracks = {"subtitles": {"en": [{"ext": "vtt"}]},
                  "automatic_captions": {"en-orig": [{"ext": "vtt"}]}}
        for mode, count, info in (("fast", 8, tracks), ("full", 24, {})):
            with self.subTest(mode=mode), patch.object(cli.shutil, "which", return_value="present"), \
                    patch.object(cli, "run", side_effect=self.downloader(info)):
                path = cli.extract(URL, mode, self.output)
                manifest = json.loads(path.read_text())
                self.assertEqual(path.name, f"context-{mode}.json")
                self.assertEqual(manifest["duration_seconds"], 2.0)
                self.assertEqual(len(manifest["frames"]), count)
                for index, frame in enumerate(manifest["frames"]):
                    self.assertEqual(frame["timestamp_seconds"], round((index + 0.5) * 2 / count, 2))
                    self.assertTrue(Path(frame["path"]).read_bytes().startswith(b"\xff\xd8"))
                if info:
                    self.assertEqual(manifest["captions"], {
                        "source": "creator", "language": "en",
                        "cues": [{"start_seconds": 0.1, "end_seconds": 1.5,
                                  "text": "Hello & welcome"}],
                    })
                else:
                    self.assertIsNone(manifest["captions"])

    def test_automatic_captions_after_creator_failure(self):
        tracks = {"subtitles": {"en": [{"ext": "vtt"}]},
                  "automatic_captions": {"en-orig": [{"ext": "vtt"}]}}
        result = get_captions(self.downloader(tracks, unavailable=("en",)), cli.DOWNLOADER,
                              URL, self.output)
        self.assertEqual(result["source"], "automatic")

    def test_next_creator_track_wins_before_automatic_captions(self):
        tracks = {"subtitles": {"en": [{"ext": "vtt"}], "es": [{"ext": "vtt"}]},
                  "automatic_captions": {"en-orig": [{"ext": "vtt"}]}}
        result = get_captions(self.downloader(tracks, unavailable=("en",)), cli.DOWNLOADER,
                              URL, self.output)
        self.assertEqual((result["source"], result["language"]), ("creator", "es"))

    def test_failed_download_leaves_no_manifest_or_partial_video(self):
        def fail(args, timeout):
            template = args[args.index("-o") + 1]
            Path(template.replace("%(ext)s", "mp4.part")).write_bytes(b"partial")
            raise RuntimeError("Network error")

        with patch.object(cli.shutil, "which", return_value="present"), \
                patch.object(cli, "run", side_effect=fail):
            with self.assertRaisesRegex(RuntimeError, "Could not download video"):
                cli.extract(URL, "fast", self.output)
        self.assertEqual(list(self.cache.iterdir()), [])
