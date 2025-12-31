# Club Maquis: Complete Data Pipeline

## Input Sources

| Source | Recording App | Type | Contains | Sync Signal |
|--------|---------------|------|----------|-------------|
| Webcam | QuickTime (New Movie Recording) | MOV | Wide shot of cat + Launchpad | Room audio (captures clap) |
| Cellphone | iPhone Camera | MOV | Close-up of cat/paws | Room audio (captures clap) |
| Synthpad (Launchpad) | Ableton Live | MIDI | Note events from cat paws | MIDI timestamps |
| Screen Recording | QuickTime (New Screen Recording) | MOV | Ableton session view | System audio (DAW output) |

## Pipeline Overview

```
+-----------------------------------------------------------------------------+
|                           RECORDING SESSION                                  |
+-----------------------------------------------------------------------------+
|                                                                             |
|  [Webcam]     [Cellphone]     [Launchpad]     [Screen Recording]           |
|  QuickTime    iPhone          Ableton         QuickTime                    |
|     |              |               |                  |                     |
|     v              v               v                  v                     |
|  webcam.mov   phone.mov      session.mid      screen.mov                   |
|                                                                             |
|  1. QuickTime > File > New Movie Recording (webcam)                        |
|  2. QuickTime > File > New Screen Recording (Ableton window)               |
|  3. iPhone Camera app                                                       |
|  4. Ableton MIDI track (armed)                                             |
|  5. Click Record on all                                                    |
|  6. CLAP for sync point                                                    |
|  7. Let cat play                                                           |
|  8. Stop all recordings                                                    |
|                                                                             |
+-----------------------------------------------------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------------+
|                         PHASE 1: INGEST & SYNC                              |
|                         (cat_dj_sync_pipeline.py)                           |
+-----------------------------------------------------------------------------+
|                                                                             |
|  +----------+  +----------+  +----------+  +----------+                    |
|  | webcam   |  | phone    |  | screen   |  | MIDI     |                    |
|  | .mov     |  | .mov     |  | .mov     |  | .mid     |                    |
|  +----+-----+  +----+-----+  +----+-----+  +----+-----+                    |
|       |             |             |             |                           |
|       v             v             v             |                           |
|  +-------------------------------------+       |                           |
|  |      AUDIO EXTRACTION               |       |                           |
|  |      (ffmpeg -vn)                   |       |                           |
|  +-------------------------------------+       |                           |
|       |             |             |             |                           |
|       v             v             v             |                           |
|  +-------------------------------------+       |                           |
|  |      TRANSIENT DETECTION            |       |                           |
|  |      (find clap in audio)           |       |                           |
|  |      - librosa onset detection      |       |                           |
|  |      - find loudest transient       |       |                           |
|  +-------------------------------------+       |                           |
|       |             |             |             |                           |
|       v             v             v             v                           |
|  +-------------------------------------------------+                       |
|  |      CALCULATE TIME OFFSETS                     |                       |
|  |      - Align all to earliest clap               |                       │
│  │      - MIDI aligned to first note after clap    │                       │
│  └─────────────────────────────────────────────────┘                       │
│                         │                                                   │
│                         ▼                                                   │
│  ┌─────────────────────────────────────────────────┐                       │
│  │      TRIM & ALIGN                               │                       │
│  │      (ffmpeg -ss offset)                        │                       │
│  └─────────────────────────────────────────────────┘                       │
│                         │                                                   │
│                         ▼                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ webcam   │  │ phone    │  │ screen   │  │ MIDI     │                    │
│  │ _sync    │  │ _sync    │  │ _sync    │  │ _sync    │                    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                    │
│                                                                             │
│  OUTPUT: All sources aligned to same timeline                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 2: ACTIVITY DETECTION                            │
│                      (cat_activity_detector.py)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT: webcam_sync.mp4, phone_sync.mp4, session_sync.mid                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │                    VIDEO ANALYSIS                           │           │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │           │
│  │  │ Frame       │  │ 2D FFT      │  │ Wavelet     │         │           │
│  │  │ Differencing│  │ (texture)   │  │ Decomp      │         │           │
│  │  │ (motion)    │  │             │  │ (multi-scale│         │           │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │           │
│  │         │                │                │                 │           │
│  │         └────────────────┼────────────────┘                 │           │
│  │                          ▼                                  │           │
│  │              ┌───────────────────────┐                      │           │
│  │              │  WEIGHTED COMBINATION │                      │           │
│  │              │  video_score =        │                      │           │
│  │              │    0.4*diff +         │                      │           │
│  │              │    0.3*fft +          │                      │           │
│  │              │    0.3*wavelet        │                      │           │
│  │              └───────────────────────┘                      │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                    │                                        │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │                    MIDI ANALYSIS                            │           │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │           │
│  │  │ Note        │  │ Velocity    │  │ Note        │         │           │
│  │  │ Density     │  │ Variance    │  │ Spread      │         │           │
│  │  │ (notes/sec) │  │             │  │ (pitch range│         │           │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │           │
│  │         │                │                │                 │           │
│  │         └────────────────┼────────────────┘                 │           │
│  │                          ▼                                  │           │
│  │              ┌───────────────────────┐                      │           │
│  │              │  midi_score =         │                      │           │
│  │              │    0.5*density +      │                      │           │
│  │              │    0.3*velocity +     │                      │           │
│  │              │    0.2*spread         │                      │           │
│  │              └───────────────────────┘                      │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │                 COMBINE & SEGMENT                           │           │
│  │                                                             │           │
│  │  combined_score = 0.6 * video_score + 0.4 * midi_score     │           │
│  │                                                             │           │
│  │  ┌─────────────────────────────────────────────────────┐   │           │
│  │  │ Score over time:                                    │   │           │
│  │  │                                                     │   │           │
│  │  │   1.0 ─┐      ┌──┐        ┌────┐      ┌─┐          │   │           │
│  │  │        │  ┌───┘  │    ┌───┘    └──┐   │ │          │   │           │
│  │  │   0.5 ─┼──┘      └────┘           └───┘ └──        │   │           │
│  │  │        │                                           │   │           │
│  │  │   0.0 ─┴───────────────────────────────────────────│   │           │
│  │  │        0s   10s   20s   30s   40s   50s   60s      │   │           │
│  │  │                                                     │   │           │
│  │  │  threshold = 0.3  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─    │   │           │
│  │  │                                                     │   │           │
│  │  │  Segments: [2-12s], [18-35s], [42-55s], [58-62s]   │   │           │
│  │  └─────────────────────────────────────────────────────┘   │           │
│  │                                                             │           │
│  │  Filter: min_duration = 2.0s                               │           │
│  │  Merge: gap < 1.0s                                         │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  OUTPUT: activity_segments.json                                            │
│  [                                                                          │
│    {"start": 2.0, "end": 12.0, "score": 0.72, "type": "active"},           │
│    {"start": 18.0, "end": 35.0, "score": 0.85, "type": "peak"},            │
│    ...                                                                      │
│  ]                                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 3: SEGMENT EXTRACTION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  For each segment in activity_segments.json:                               │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  ffmpeg -i webcam_sync.mp4 -ss {start} -to {end}           │           │
│  │         -c copy segment_webcam_{n}.mp4                      │           │
│  │                                                             │           │
│  │  ffmpeg -i phone_sync.mp4 -ss {start} -to {end}            │           │
│  │         -c copy segment_phone_{n}.mp4                       │           │
│  │                                                             │           │
│  │  ffmpeg -i screen_sync.mp4 -ss {start} -to {end}           │           │
│  │         -c copy segment_screen_{n}.mp4                      │           │
│  │                                                             │           │
│  │  python midi_slice.py session_sync.mid {start} {end}       │           │
│  │         -o segment_midi_{n}.mid                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  OUTPUT: segments/                                                          │
│          ├── segment_01/                                                    │
│          │   ├── webcam.mp4                                                │
│          │   ├── phone.mp4                                                 │
│          │   ├── screen.mp4                                                │
│          │   └── midi.mid                                                  │
│          ├── segment_02/                                                    │
│          │   └── ...                                                       │
│          └── ...                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 4: MAGENTA AI PROCESSING                         │
│                      (magenta_pipeline.py)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  For each segment_midi_{n}.mid:                                            │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │                                                             │           │
│  │  INPUT: segment_midi_01.mid (cat's random pad hits)        │           │
│  │                                                             │           │
│  │                          │                                  │           │
│  │                          ▼                                  │           │
│  │  ┌─────────────────────────────────────────────────────┐   │           │
│  │  │              DRUMIFY                                 │   │           │
│  │  │                                                     │   │           │
│  │  │  Cat's random notes --> Extract rhythm --> VAE      │   │           │
│  │  │                                                     │   │           │
│  │  │  temperature=0.8, variations=4                      │   │           │
│  │  │                                                     │   │           │
│  │  │  OUTPUT: segment_01_drums_00.mid                    │   │           │
│  │  │          segment_01_drums_01.mid                    │   │           │
│  │  │          segment_01_drums_02.mid                    │   │           │
│  │  │          segment_01_drums_03.mid                    │   │           │
│  │  └─────────────────────────────────────────────────────┘   │           │
│  │                          │                                  │           │
│  │                          ▼                                  │           │
│  │  ┌─────────────────────────────────────────────────────┐   │           │
│  │  │              GROOVE (HUMANIZE)                       │   │           │
│  │  │                                                     │   │           │
│  │  │  Take best drum variation --> Add micro-timing      │   │           │
│  │  │                                                     │   │           │
│  │  │  OUTPUT: segment_01_drums_grooved.mid               │   │           │
│  │  └─────────────────────────────────────────────────────┘   │           │
│  │                          │                                  │           │
│  │                          ▼                                  │           │
│  │  ┌─────────────────────────────────────────────────────┐   │           │
│  │  │              CONTINUE (MELODY)                       │   │           │
│  │  │                                                     │   │           │
│  │  │  Cat's notes --> Extend melodically --> VAE         │   │           │
│  │  │                                                     │   │           │
│  │  │  OUTPUT: segment_01_melody_continued.mid            │   │           │
│  │  └─────────────────────────────────────────────────────┘   │           │
│  │                          │                                  │           │
│  │                          ▼                                  │           │
│  │  ┌─────────────────────────────────────────────────────┐   │           │
│  │  │              GENERATE (ACCOMPANIMENT)                │   │           │
│  │  │                                                     │   │           │
│  │  │  Random latent --> Bass/pad accompaniment           │   │           │
│  │  │                                                     │   │           │
│  │  │  OUTPUT: segment_01_accomp.mid                      │   │           │
│  │  └─────────────────────────────────────────────────────┘   │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  OUTPUT: magenta/                                                           │
│          ├── segment_01/                                                    │
│          │   ├── drums_00.mid ... drums_03.mid                             │
│          │   ├── drums_grooved.mid                                         │
│          │   ├── melody_continued.mid                                      │
│          │   └── accomp.mid                                                │
│          └── ...                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 5: AUDIO RENDERING                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  MIDI TO AUDIO (for each .mid file)                        │           │
│  │                                                             │           │
│  │  Option A: FluidSynth (command line)                       │           │
│  │  fluidsynth -ni soundfont.sf2 input.mid -F output.wav      │           │
│  │                                                             │           │
│  │  Option B: Ableton (render in DAW)                         │           │
│  │  - Import MIDI to tracks                                   │           │
│  │  - Route through instruments                               │           │
│  │  - Export audio                                            │           │
│  │                                                             │           │
│  │  Option C: Python (pretty_midi + pydub)                    │           │
│  │  Programmatic rendering with custom synth                  │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  AUDIO MIXING                                               │           │
│  │                                                             │           │
│  │  ┌─────────────┐                                           │           │
│  │  │ Cat pads    │──┐                                        │           │
│  │  │ (original)  │  │                                        │           │
│  │  └─────────────┘  │    ┌─────────────┐   ┌─────────────┐   │           │
│  │  ┌─────────────┐  ├───►│   MIXER     │──►│   MASTER    │   │           │
│  │  │ AI drums    │──┤    │             │   │   (limiter, │   │           │
│  │  │ (grooved)   │  │    │ Volume/Pan  │   │    EQ)      │   │           │
│  │  └─────────────┘  │    └─────────────┘   └─────────────┘   │           │
│  │  ┌─────────────┐  │                             │          │           │
│  │  │ AI melody   │──┤                             ▼          │           │
│  │  │ (continued) │  │                      ┌─────────────┐   │           │
│  │  └─────────────┘  │                      │ segment_01  │   │           │
│  │  ┌─────────────┐  │                      │ _audio.wav  │   │           │
│  │  │ AI accomp   │──┘                      └─────────────┘   │           │
│  │  └─────────────┘                                           │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  OUTPUT: rendered/                                                          │
│          ├── segment_01_audio.wav                                          │
│          ├── segment_02_audio.wav                                          │
│          └── ...                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 6: VIDEO COMPOSITING                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  For each segment:                                                          │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  VIDEO LAYOUT OPTIONS                                       │           │
│  │                                                             │           │
│  │  Option A: Picture-in-Picture                              │           │
│  │  ┌───────────────────────────────┐                         │           │
│  │  │                               │                         │           │
│  │  │         WEBCAM                │                         │           │
│  │  │      (main shot)         ┌────┴────┐                    │           │
│  │  │                          │ PHONE   │                    │           │
│  │  │                          │(closeup)│                    │           │
│  │  └──────────────────────────┴─────────┘                    │           │
│  │                                                             │           │
│  │  Option B: Split Screen                                    │           │
│  │  ┌────────────────┬────────────────┐                       │           │
│  │  │                │                │                       │           │
│  │  │    WEBCAM      │     PHONE      │                       │           │
│  │  │                │                │                       │           │
│  │  └────────────────┴────────────────┘                       │           │
│  │                                                             │           │
│  │  Option C: Triple View                                     │           │
│  │  ┌──────────┬──────────┬──────────┐                        │           │
│  │  │          │          │          │                        │           │
│  │  │  WEBCAM  │  PHONE   │  SCREEN  │                        │           │
│  │  │          │          │          │                        │           │
│  │  └──────────┴──────────┴──────────┘                        │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  FFMPEG COMPOSITE                                           │           │
│  │                                                             │           │
│  │  # PiP example                                              │           │
│  │  ffmpeg -i webcam.mp4 -i phone.mp4 -i audio.wav \          │           │
│  │    -filter_complex "                                        │           │
│  │      [0:v]scale=1920:1080[main];                           │           │
│  │      [1:v]scale=480:270[pip];                              │           │
│  │      [main][pip]overlay=W-w-20:H-h-20                      │           │
│  │    " -map 2:a -c:v h264 -c:a aac segment_01_composite.mp4  │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  OUTPUT: composited/                                                        │
│          ├── segment_01_composite.mp4                                      │
│          ├── segment_02_composite.mp4                                      │
│          └── ...                                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 7: STYLE & EDITING                                 │
│                    (dj_style_analyzer.py)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  BEAT-AWARE EDITING                                         │           │
│  │                                                             │           │
│  │  1. Detect beats in audio                                  │           │
│  │     librosa.beat.beat_track()                              │           │
│  │                                                             │           │
│  │  2. Snap cuts to beat boundaries                           │           │
│  │     - Camera switches on beats                             │           │
│  │     - Transitions on downbeats                             │           │
│  │                                                             │           │
│  │  3. Apply DJ editing patterns                              │           │
│  │     - Quick cuts during drops                              │           │
│  │     - Longer shots during builds                           │           │
│  │     - Zoom effects on hits                                 │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  TRANSITIONS                                                │           │
│  │                                                             │           │
│  │  Between segments:                                         │           │
│  │  - Crossfade (0.5-1.0s)                                    │           │
│  │  - Beat-synced cuts                                        │           │
│  │  - Wipe effects                                            │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  OUTPUT: edited/                                                            │
│          └── session_edited.mp4                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 8: FINAL OUTPUT                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  ADD BRANDING                                               │           │
│  │                                                             │           │
│  │  - Intro: Club Maquis logo (2-3s)                          │           │
|  |  - Lower third: "DJ Nerys" + "Club Maquis"                   |           |
|  |  - Outro: Subscribe CTA (5s)                                  |           |
│  │  - Watermark: Small logo corner                            │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  EXPORT FORMATS                                             │           │
│  │                                                             │           │
│  │  YouTube:  1080p H.264, AAC, 8-15 Mbps                     │           │
│  │  Shorts:   1080x1920 (vertical crop), <60s                 │           │
│  │  TikTok:   1080x1920, <3min                                │           │
│  │  Twitch:   1080p, for VOD                                  │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  OUTPUT: final/                                                             │
│          ├── club_maquis_session_001_youtube.mp4                           │
│          ├── club_maquis_session_001_short.mp4                             │
│          ├── club_maquis_session_001_tiktok.mp4                            │
│          └── metadata.json                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 9: ENGAGEMENT OPTIMIZATION                         │
│                    (engagement_optimizer.py)                                │
│                    [AFTER PUBLISHING - FEEDBACK LOOP]                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  COLLECT METRICS                                            │           │
│  │                                                             │           │
│  │  YouTube Analytics API:                                    │           │
│  │  - Retention curve (where do people drop off?)             │           │
│  │  - Replay moments (what do people rewatch?)                │           │
│  │  - Click-through rate                                      │           │
│  │  - Average view duration                                   │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  ANALYZE PATTERNS                                           │           │
│  │                                                             │           │
│  │  - Which segments have highest retention?                  │           │
│  │  - What cat behaviors get replays?                         │           │
│  │  - Optimal video length?                                   │           │
│  │  - Best thumbnail moments?                                 │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐           │
│  │  GENERATE OPTIMIZED REMIX                                   │           │
│  │                                                             │           │
│  │  - Keep high-retention segments                            │           │
│  │  - Cut low-retention moments                               │           │
│  │  - Reorder for better flow                                 │           │
│  │  - Create "best of" compilation                            │           │
│  │                                                             │           │
│  └─────────────────────────────────────────────────────────────┘           │
│                                                                             │
│  OUTPUT: Feedback to improve future sessions                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
clubmaquis/
├── sessions/
│   └── 2024-01-15_session_001/
│       ├── raw/                          # PHASE 0: Raw recordings
│       │   ├── webcam.mp4
│       │   ├── phone.mp4
│       │   ├── screen.mp4
│       │   └── session.mid
│       │
│       ├── 01_synced/                    # PHASE 1: Synchronized
│       │   ├── webcam_sync.mp4
│       │   ├── phone_sync.mp4
│       │   ├── screen_sync.mp4
│       │   ├── session_sync.mid
│       │   └── sync_metadata.json
│       │
│       ├── 02_activity/                  # PHASE 2: Activity detection
│       │   └── activity_segments.json
│       │
│       ├── 03_segments/                  # PHASE 3: Extracted segments
│       │   ├── segment_01/
│       │   │   ├── webcam.mp4
│       │   │   ├── phone.mp4
│       │   │   ├── screen.mp4
│       │   │   └── midi.mid
│       │   ├── segment_02/
│       │   └── ...
│       │
│       ├── 04_magenta/                   # PHASE 4: AI processing
│       │   ├── segment_01/
│       │   │   ├── drums_00.mid
│       │   │   ├── drums_01.mid
│       │   │   ├── drums_grooved.mid
│       │   │   ├── melody_continued.mid
│       │   │   └── accomp.mid
│       │   └── ...
│       │
│       ├── 05_rendered/                  # PHASE 5: Audio rendered
│       │   ├── segment_01_mix.wav
│       │   ├── segment_02_mix.wav
│       │   └── ...
│       │
│       ├── 06_composited/                # PHASE 6: Video composited
│       │   ├── segment_01_composite.mp4
│       │   └── ...
│       │
│       ├── 07_edited/                    # PHASE 7: Styled/edited
│       │   └── session_edited.mp4
│       │
│       └── 08_final/                     # PHASE 8: Final outputs
│           ├── club_maquis_001_youtube.mp4
│           ├── club_maquis_001_short.mp4
│           └── metadata.json
│
├── src/                                  # Python modules
│   ├── cat_dj_sync_pipeline.py
│   ├── cat_activity_detector.py
│   ├── magenta_pipeline.py
│   ├── dj_style_analyzer.py
│   ├── engagement_optimizer.py
│   ├── video_compositor.py
│   └── cat_dj_pipeline.py               # Main orchestrator
│
├── assets/                               # Branding assets
│   ├── logo.png
│   ├── intro.mp4
│   ├── outro.mp4
│   └── soundfonts/
│       └── cat_dj_drums.sf2
│
├── config/                               # Configuration
│   ├── pipeline_config.yaml
│   ├── magenta_presets.json
│   └── export_profiles.json
│
└── analytics/                            # YouTube data
    ├── video_001_retention.csv
    └── engagement_analysis.json
```

## Quick Reference: Command Sequence

```bash
# 1. After recording session, run full pipeline
python cat_dj_pipeline.py \
    --session ./sessions/2024-01-15/raw/ \
    --output ./sessions/2024-01-15/ \
    --magenta-tools drumify,groove,continue \
    --temperature 0.8

# 2. Or run phases individually:

# Sync sources
python cat_dj_sync_pipeline.py \
    --input-dir ./raw/ \
    --output-dir ./01_synced/

# Detect activity
python cat_activity_detector.py \
    --video ./01_synced/webcam_sync.mp4 \
    --midi ./01_synced/session_sync.mid \
    --output ./02_activity/segments.json

# Process with Magenta
python magenta_pipeline.py \
    --input ./03_segments/segment_01/midi.mid \
    --output ./04_magenta/segment_01/ \
    --tools drumify,groove \
    --simple  # Use SimpleMagenta if TensorFlow issues

# Composite video
python video_compositor.py \
    --webcam ./03_segments/segment_01/webcam.mp4 \
    --phone ./03_segments/segment_01/phone.mp4 \
    --audio ./05_rendered/segment_01_mix.wav \
    --output ./06_composited/segment_01.mp4 \
    --layout pip

# Final export
python export_final.py \
    --input ./07_edited/session_edited.mp4 \
    --output ./08_final/ \
    --formats youtube,short,tiktok \
    --add-branding
```

## Data Flow Summary

```
INPUT                    PROCESSING                      OUTPUT
─────                    ──────────                      ──────

webcam.mp4  ─┐                                     
phone.mp4   ─┼─► SYNC ─► ACTIVITY ─► SEGMENT ─┐   
screen.mp4  ─┤           DETECT      EXTRACT   │   
session.mid ─┘                                 │   
                                               │   
                                               ▼   
                                                   
                         ┌─ DRUMIFY ──► drums.mid ─┐
              segment ───┼─ GROOVE ───► humanized ─┼─► MIX ─┐
              .mid       ├─ CONTINUE ─► melody ────┤        │
                         └─ GENERATE ─► accomp ────┘        │
                                                            │
                                                            ▼
                                                            
webcam ──┐                                          final_youtube.mp4
phone  ──┼─► COMPOSITE ─► EDIT ─► BRAND ─────────► final_short.mp4
screen ──┘       ▲                                  final_tiktok.mp4
                 │                                         
            audio_mix.wav                                  
```

## Key Dependencies

| Phase | Dependencies |
|-------|--------------|
| Sync | ffmpeg, librosa, scipy |
| Activity | opencv-python, numpy, scipy, pywavelets, mido |
| Magenta | magenta, note-seq, tensorflow (or mido for simple mode) |
| Render | fluidsynth or timidity, soundfonts |
| Composite | ffmpeg |
| Style | librosa, scenedetect |
| Export | ffmpeg |

```bash
# Install all
pip install numpy scipy opencv-python librosa mido pywavelets scenedetect
pip install magenta note-seq tensorflow  # Optional, for full Magenta

# System dependencies
brew install ffmpeg fluidsynth  # macOS
# apt install ffmpeg fluidsynth  # Linux
```
