# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Club Maquis is a cat DJ streaming channel where Nerys (a cat) makes music by stepping on a Novation Launchpad MIDI controller. This repository contains Python tools for processing multi-source recordings into polished YouTube/TikTok content.

## Development Commands

```bash
# Install dependencies
uv sync                                    # Install all dependencies
brew install ffmpeg fluidsynth             # System dependencies (macOS)

# Linting and formatting
uv run ruff check .                        # Lint
uv run ruff check --fix .                  # Auto-fix linting

# Pre-commit hooks
uv run pre-commit install                  # Install hooks (one-time)
uv run pre-commit run --all-files          # Run manually

# Testing (infrastructure ready, tests pending v0.2.0)
uv run pytest                              # Run tests
uv run pytest -v -k test_name              # Single test

# Session management scripts (in scripts/)
uv run python scripts/shutdown/main.py 20251231T120000Z  # Shutdown recording session

# Recording session automation
uv run python -m scripts.setup.recording   # Set up recording session (creates dir, launches apps)
uv run python -m scripts.setup.recording --cat-tv-url "https://..."  # Custom cat TV URL

# Run full pipeline
uv run python cat_dj_pipeline.py --session ./sessions/[date]/raw/ --output ./sessions/[date]/ --magenta-tools drumify,groove --simple

# Run individual phases
uv run python cat_dj_sync_pipeline.py --input-dir ./raw/ --output-dir ./synced/
uv run python cat_activity_detector.py --video ./synced/webcam_sync.mp4 --midi ./synced/session_sync.mid --output segments.json
uv run python magenta_pipeline.py --input ./session.mid --output ./magenta/ --tools drumify,groove --simple
uv run python video_compositor.py --webcam webcam.mp4 --phone phone.mp4 --audio mix.wav --output final.mp4 --layout pip
```

## Architecture

### Processing Pipeline (8 Phases)

1. **Sync** (`cat_dj_sync_pipeline.py`) - Aligns recordings from multiple sources (webcam, phone, screen, MIDI) using audio transient detection to find the sync clap
2. **Activity Detection** (`cat_activity_detector.py`) - Identifies active segments using frame differencing, 2D FFT, wavelet decomposition, and MIDI density analysis
3. **Segment Extraction** - Cuts video/audio/MIDI at segment boundaries using ffmpeg
4. **Magenta AI** (`magenta_pipeline.py`) - Generates drums, humanizes timing, extends melodies from cat's random pad hits
5. **Audio Rendering** - Renders MIDI to audio via FluidSynth or Ableton
6. **Video Compositing** (`video_compositor.py`) - Combines camera sources (PIP, split-screen, triple view)
7. **Style & Editing** (`dj_style_analyzer.py`) - Beat-synced cuts, camera switches, transitions
8. **Final Export** - Branding, multiple format exports (YouTube 1080p, Shorts, TikTok)

### Session Directory Structure

```
sessions/[date]/
├── raw/                    # Original recordings
├── synced/                 # Phase 1: Aligned sources
├── segments.json           # Phase 2: Activity detection output
├── segments/               # Phase 3: Extracted clips
├── magenta/                # Phase 4: AI-generated MIDI
├── rendered/               # Phase 5: Audio mixes
├── composited/             # Phase 6: Combined video
├── edited/                 # Phase 7: Styled output
└── final/                  # Phase 8: Export formats
```

### Recording Setup

- **Input sources**: Webcam (QuickTime), iPhone
- **MIDI controller**: Novation Launchpad Mini MK3
- **Sync method**: Clap at session start creates audio transient for alignment
- **Cat lure**: Bird/fish videos via Chrome (YouTube cat TV) + Launchpad light patterns
- **Session data**: `~/Library/CloudStorage/GoogleDrive-samuel.harrold@gmail.com/My Drive/My_Drive/ClubMaquis/YYYYMMDDTHHMMSSZ/`
- **Session log**: `YYYYMMDDTHHMMSSZ_log.jsonl` with self-documenting entries and absolute file paths
- **File naming**: User names files as `YYYYMMDD_<type>.mov` (e.g., `20250101_webcam.mov`)

### Automation Scripts

Located in `scripts/` directory, these manage recording session lifecycle:

```
scripts/
├── common/
│   └── logger.py             # Self-documenting JSONL logger (shared)
├── setup/
│   ├── recording.py          # Create session dir, launch apps, start Launchpad lights
│   ├── launchers.py          # App launching utilities (QuickTime, Chrome)
│   └── launchpad_lights.py   # Cat-enticing LED patterns for Launchpad Mini MK3
├── shutdown/
│   ├── main.py               # CLI: prompts user to save files, logs session
│   ├── quicktime.py          # AppleScript control for QuickTime
│   └── utils.py              # Shared AppleScript utilities
└── process/                  # (future) Run pipeline
```

### Launchpad Light Patterns

The setup script automatically runs cat-enticing light patterns on the Launchpad Mini MK3 to attract Nerys:
- **7 patterns** cycle randomly every 8 seconds: snake, sparkle, rain, spiral, wave, diagonal, expand
- Uses MIDI port (not DAW port) for LED control
- Based on Launchpad Mini MK3 Programmer's Reference Manual (`docs/`)
- Patterns use warm colors (red, orange, yellow) that cats notice

**Setup script workflow**:
1. Creates session directory in Google Drive
2. Detects Launchpad and starts light patterns (if connected)
3. Launches QuickTime Player
4. Opens Chrome to cat TV URL
5. Displays manual steps for recording
6. Lights run until user presses Enter

**Shutdown script workflow**:
1. Prompts user to save QuickTime recordings to session directory
2. Prompts user to AirDrop iPhone video to session directory
3. Waits for user confirmation
4. Scans and logs all files with absolute paths

## Key Technical Concepts

- **Activity scoring**: `combined_score = 0.6 * video_score + 0.4 * midi_score` where video_score combines frame differencing (0.4), FFT (0.3), and wavelet (0.3)
- **Magenta tools**: Drumify (rhythm extraction), Groove (humanize timing), Continue (extend melody), Generate (accompaniment)
- **SimpleMagenta mode**: Use `--simple` flag to avoid TensorFlow dependency

## v6 Workflow

This repository uses a 4-phase workflow for feature development:

```
/workflow:v6_1_worktree "feature description"
    | creates worktree, user runs /feature-dev in worktree
    v
/workflow:v6_2_integrate "feature/YYYYMMDDTHHMMSSZ_slug"
    | PR feature->contrib->develop
    v
/workflow:v6_3_release
    | create release, PR to main, tag
    v
/workflow:v6_4_backmerge
    | PR release->develop, rebase contrib, cleanup
```

### Branch Structure

```
main                           <- Production (tagged vX.Y.Z)
  ^
develop                        <- Integration branch
  ^
contrib/stharrold              <- Personal contribution branch
  ^
feature/<timestamp>_<slug>     <- Isolated feature (worktree)
```

## Critical Guidelines

- **Branch workflow**: Always work on `contrib/stharrold` or feature branches, never directly on `main` or `develop`
- **End on editable branch**: All workflows must end on `contrib/*` (never `develop` or `main`)
- **Use feature worktrees**: Create isolated worktrees for feature development
