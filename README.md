# Club Maquis

**DJ Nerys drops beats. Shelter pets get treats.**

A cat DJ streaming channel. Nerys makes music by walking on a Launchpad.

![Club Maquis Banner](assets/club_maquis_banner_v9.png)

## The Concept

Nerys (a cat) makes music by stepping on a Launchpad MIDI controller. That's it. That's the show.

## Links

| Platform | Link |
|----------|------|
| YouTube | [@ClubMaquis](https://www.youtube.com/@ClubMaquis) |
| Patreon | [ClubMaquis](https://www.patreon.com/c/ClubMaquis) |
| Buy Me a Coffee | [ClubMaquis](https://buymeacoffee.com/ClubMaquis) |

## The Crew

- **Nerys** (cat) - Head DJ, professional pad-stepper
- **Beckett** (dog) - Hype beast, occasional guest appearance

Named after our favorite Star Trek characters.

## Technical Pipeline

This repo contains Python tools for processing cat DJ footage.

### Quick Start

```bash
# Clone the repo
git clone https://github.com/stharrold/clubmaquis.git
cd clubmaquis

# Install dependencies
uv sync
brew install ffmpeg fluidsynth  # macOS system dependencies

# Run full pipeline
uv run python cat_dj_pipeline.py --session ./sessions/[date]/raw/ --output ./sessions/[date]/
```

### Processing Modules

| Module | Purpose |
|--------|---------|
| `cat_dj_sync_pipeline.py` | Synchronize multi-source recordings using audio transient detection |
| `cat_activity_detector.py` | Detect active segments using frame differencing, FFT, wavelet, MIDI analysis |
| `magenta_pipeline.py` | Generate AI drums and humanize timing from cat's random pad hits |
| `video_compositor.py` | Combine camera sources (PIP, split-screen, triple view) |
| `dj_style_analyzer.py` | Apply beat-synced cuts and camera switches |

See [docs/pipeline.md](docs/pipeline.md) for the complete 8-phase pipeline documentation.

## Equipment

- **Camera**: iPhone with mount
- **MIDI Controller**: Novation Launchpad Mini MK3
- **DAW**: Ableton Live 12 Suite
- **AI Music**: Magenta Studio (post-processing)
- **Recording**: QuickTime Player (webcam + screen)
- **Cat Lure**: Bird/fish videos via VLC

## Project Structure

```
clubmaquis/
├── README.md
├── CLAUDE.md                 # AI assistant context
├── pyproject.toml            # Dependencies and tool config
├── assets/                   # Banner images and graphics
├── docs/
│   ├── pipeline.md           # Full pipeline documentation
│   ├── ableton_automation.md # DAW setup guide
│   └── channel_copy.md       # Marketing copy templates
└── sessions/                 # Recording session data
    └── [date]/
        ├── raw/              # Original recordings
        ├── synced/           # Aligned sources
        └── final/            # Export formats
```

## The Name

"Maquis" is a reference to Star Trek: Deep Space Nine. The Maquis were a resistance organization - scrappy underdogs fighting for what they believe in.

- **Nerys**: Named after Major Kira Nerys (DS9)
- **Beckett**: Named after Ensign Beckett Mariner (Lower Decks)

## License

MIT License - do whatever you want with this code.

---

*Where cats drop beats.*
