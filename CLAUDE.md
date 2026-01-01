# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Club Maquis is a cat DJ streaming channel where Nerys (a cat) makes music by stepping on a Novation Launchpad MIDI controller. This repository contains Python tools for processing multi-source recordings into polished YouTube/TikTok content.

## Development Commands

```bash
# Install dependencies
uv sync                                    # Install all dependencies
brew install ffmpeg fluidsynth gphotos-uploader-cli  # System dependencies (macOS)

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

- **Input sources**: Webcam (QuickTime), iPhone, Screen Recording (Ableton), MIDI track
- **Sync method**: Clap at session start creates audio transient for alignment
- **DAW**: Ableton Live 12 Suite with Launchpad Mini MK3
- **Cat lure**: Bird/fish videos via Chrome (YouTube cat TV)
- **Session data**: `/Users/stharrold/Documents/Data/ClubMaquis/YYYYMMDDTHHMMSSZ/`
- **Session log**: Each session has `log.jsonl` with timestamped actions

### Automation Scripts

Located in `scripts/` directory, these automate recording session lifecycle:

```
scripts/
├── common/
│   └── logger.py             # Self-documenting JSONL logger (shared)
├── setup/
│   ├── recording.py          # Launch apps, create session dir
│   └── launchers.py          # App launching utilities
├── shutdown/                 # Graceful session shutdown
│   ├── main.py               # CLI: stops recordings, saves files, uploads to Google Photos
│   ├── quicktime.py          # AppleScript control for QuickTime
│   ├── ableton.py            # Ableton file management + close
│   ├── gphotos.py            # Google Photos upload via gphotos-uploader-cli
│   └── utils.py              # Shared AppleScript utilities
└── process/                  # (future) Run pipeline
```

**Shutdown script workflow**:
1. Stops QuickTime recordings → waits for files to stabilize
2. Moves recordings from Desktop to session directory
3. Copies Ableton project files with naming: `YYYYMMDDTHHMMSSZ_ableton_<type>.<ext>`
4. Closes Ableton Live
5. Uploads to Google Photos album `ClubMaquis_<session_id>`
6. Logs all actions to self-documenting `log.jsonl`

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

### Common Commands

```bash
# Development
uv sync                                    # Install dependencies
uv run pytest                              # Run tests
uv run ruff check .                        # Lint
uv run ruff check --fix .                  # Auto-fix linting

# Pre-commit hooks
uv run pre-commit install                  # Install hooks (one-time)
uv run pre-commit run --all-files          # Run manually
```

## Critical Guidelines

- **Branch workflow**: Always work on `contrib/stharrold` or feature branches, never directly on `main` or `develop`
- **End on editable branch**: All workflows must end on `contrib/*` (never `develop` or `main`)
- **Use feature worktrees**: Create isolated worktrees for feature development
