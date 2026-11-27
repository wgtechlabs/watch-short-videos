---
name: watch-short-videos
description: Extract video context from short-form video links using local tools, then analyze selected frames with the agent's vision.
---

# Watch Short Videos

When a user supplies a Facebook Reel, Instagram Reel, TikTok, or YouTube Short and asks to watch or extract context:

1. Check that the user is authorized to access the video.
2. Run `python -m engine.cli extract "<URL>" --mode fast` from the repository root. Use `--mode full` only if requested.
3. Read the generated manifest and inspect referenced frame images with your available image-reading tools. Do not assume file paths alone provide vision.
4. Summarize observed visuals with timestamps, and distinguish visual observations from metadata or inferred details.
5. State missing audio or unavailable content explicitly. Never invent narration or events.
6. Do not save knowledge permanently, modify code, or take further actions unless requested.

Fast is the default. Full samples more frames and can consume more model tokens.
If local binaries, network access, or image-reading tools are unavailable, explain the limitation.
