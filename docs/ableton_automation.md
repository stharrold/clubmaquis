# Club Maquis: Ableton Automation Guide

Comprehensive guide to automating your Ableton Live setup for cat DJ sessions.

## Table of Contents

1. [Template Project Setup](#template-project-setup)
2. [Options.txt Configuration](#optionstxt-configuration)
3. [Python Launcher Script](#python-launcher-script)
4. [AbletonOSC Control](#abletonosc-control)
5. [MIDI Controller Scripts](#midi-controller-scripts)
6. [ClyphX Pro Automation](#clyphx-pro-automation)
7. [Full Session Workflow](#full-session-workflow)
8. [Troubleshooting](#troubleshooting)

---

## Template Project Setup

The easiest and most reliable automation method. Create once, use forever.

### What to Include in Your Template

#### Audio Tracks

| Track | Purpose | Configuration |
|-------|---------|---------------|
| 1 - Cat Pads | Launchpad sounds | Input: Launchpad, armed |
| 2 - Magenta Out | AI-generated accompaniment | Input: Magenta Studio |
| 3 - Master Mix | Final output | Receives from all |
| 4 - Recording | Capture everything | Input: Master, armed |

#### MIDI Tracks

| Track | Purpose | Configuration |
|-------|---------|---------------|
| 1 - Launchpad In | Raw MIDI from cat | Input: Launchpad Mini MK3 |
| 2 - Magenta Drums | AI drums | Magenta Drumify device |
| 3 - Magenta Melody | AI melody | Magenta Continue device |

#### Launchpad Pad Mapping

Create a Drum Rack with cat-friendly sounds:

```
Pad Layout (Launchpad Mini MK3):
+---+---+---+---+---+---+---+---+
| C | D | E | F | G | A | B | C |  <- Row 8 (melodic)
+---+---+---+---+---+---+---+---+
| K | S | H | H | K | S | H | H |  <- Row 7 (drums)
+---+---+---+---+---+---+---+---+
| P | P | P | P | P | P | P | P |  <- Row 6 (pads/chords)
+---+---+---+---+---+---+---+---+
| ... continue pattern ...      |
+---+---+---+---+---+---+---+---+

K = Kick, S = Snare, H = Hi-hat, P = Pad/Synth
```

**Sound Selection Tips for Cats:**
- Use sounds that work at ANY velocity (cats don't press consistently)
- Avoid harsh/startling sounds (scares the cat)
- Layer soft attack sounds (pads, strings)
- Keep everything in the same key (can't sound "wrong")

#### Recommended Scale/Key Lock

```
Key: C Major (all white notes = safe)
Scale: Pentatonic (even safer - C, D, E, G, A)

Use Ableton's Scale MIDI effect:
- Insert on MIDI track
- Set to C Major Pentatonic
- Now ANY note the cat triggers sounds good
```

#### Magenta Studio Configuration

```
Drumify Settings:
- Temperature: 0.8 (some variety, not too crazy)
- Steps: 32
- Variation: Medium

Continue Settings:
- Temperature: 0.7
- Steps: 16
- Player: Cat's MIDI input
```

#### Audio Routing

```
System Setup:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Launchpad   │────>│ Ableton     │────>│ Speakers/   │
│ (cat paws)  │     │ Live        │     │ Headphones  │
└─────────────┘     └─────────────┘     └─────────────┘

Recording captures:
- Screen recording: Ableton window + system audio
- Webcam: Room audio (for sync clap)
- Phone: Room audio (for sync clap)
- Ableton: MIDI notes directly

Ableton Preferences > Audio:
- Output: Built-in Output (or audio interface)
- Sample Rate: 48000
- Buffer: 256-512 samples
```

#### Default Settings

```
BPM: 120 (standard, easy math for editing)
Time Signature: 4/4
Metronome: OFF (don't scare the cat)
Count-in: OFF
Record Quantize: OFF (keep cat timing authentic)
```

### Saving the Template

1. Configure everything above
2. File > Save Live Set As... > `cat_dj_template.als`
3. File > Save Live Set as Template (makes it default)

**Template Location:**
```
macOS: /Users/[username]/Music/Ableton/User Library/Templates/
Windows: C:\Users\[username]\Documents\Ableton\User Library\Templates\
```

### Creating Multiple Templates

| Template | Use Case |
|----------|----------|
| `cat_dj_chill.als` | Ambient/lo-fi session |
| `cat_dj_edm.als` | Higher energy sounds |
| `cat_dj_minimal.als` | Simple setup for short clips |
| `cat_dj_collab.als` | Beckett (dog) guest appearance |

---

## Options.txt Configuration

Hidden Ableton settings not in preferences UI.

### File Location

```
macOS: /Users/[username]/Library/Preferences/Ableton/Live [version]/Options.txt
Windows: C:\Users\[username]\AppData\Roaming\Ableton\Live [version]\Preferences\Options.txt
```

Create this file if it doesn't exist.

### Useful Options for Cat DJ

```
# Options.txt for Club Maquis

# Disable update check (fewer popups)
-NoAutoUpdates

# Start with specific template
-DefaultTemplate="/Users/[username]/Music/Ableton/cat_dj_template.als"

# Reduce CPU usage
-EnableMapperExclusion

# Higher MIDI precision
-EnableHighPriorityMidi

# Disable Live's browser scanning on startup (faster boot)
-DisableBrowserPluginScanning

# Use larger audio buffer (stability over latency)
-AudioBufferSize=512
```

### Options Reference

| Option | Effect |
|--------|--------|
| `-NoAutoUpdates` | Disables update notifications |
| `-EnableHighPriorityMidi` | Better MIDI timing |
| `-EnableMapperExclusion` | Reduces CPU on mapped parameters |
| `-DisableBrowserPluginScanning` | Faster startup |
| `-AllowMultipleInstances` | Run multiple Ableton instances |

---

## Python Launcher Script

Automate launching everything needed for a cat DJ session.

### Basic Launcher

```python
#!/usr/bin/env python3
"""
Club Maquis Session Launcher
Launches all applications needed for a cat DJ session.
"""

import subprocess
import time
import os
from pathlib import Path

# Configuration
ABLETON_TEMPLATE = Path.home() / "Music/Ableton/User Library/Templates/cat_dj_template.als"
BIRD_VIDEO = Path.home() / "Videos/bird_videos/birds_for_cats.mp4"

def launch_ableton():
    """Launch Ableton with template."""
    print("Launching Ableton Live...")
    
    if ABLETON_TEMPLATE.exists():
        subprocess.Popen(["open", str(ABLETON_TEMPLATE)])
    else:
        # Just open Ableton (will use default template)
        subprocess.Popen(["open", "-a", "Ableton Live 12 Suite"])
    
    time.sleep(5)  # Wait for Ableton to start

def launch_quicktime_webcam():
    """Launch QuickTime for webcam recording."""
    print("Launching QuickTime for webcam...")
    # Open QuickTime - user will need to start New Movie Recording manually
    subprocess.Popen(["open", "-a", "QuickTime Player"])
    time.sleep(2)

def launch_quicktime_screen():
    """Remind to start screen recording."""
    print("\n" + "="*50)
    print("REMINDER: In QuickTime, start:")
    print("  1. File > New Movie Recording (webcam)")
    print("  2. File > New Screen Recording (Ableton)")
    print("="*50 + "\n")

def launch_bird_video():
    """Launch bird video in VLC for cat enticement."""
    print("Launching bird video...")
    
    if BIRD_VIDEO.exists():
        subprocess.Popen([
            "open", "-a", "VLC", 
            str(BIRD_VIDEO),
            "--args", "--loop", "--fullscreen"
        ])
    else:
        print(f"Warning: Bird video not found at {BIRD_VIDEO}")

def launch_iphone_camera():
    """
    Remind to start iPhone camera.
    """
    print("\n" + "="*50)
    print("REMINDER: Start iPhone camera recording!")
    print("="*50 + "\n")

def check_launchpad():
    """Check if Launchpad is connected."""
    # List MIDI devices (macOS)
    result = subprocess.run(
        ["system_profiler", "SPUSBDataType"],
        capture_output=True, text=True
    )
    
    if "Launchpad" in result.stdout:
        print("Launchpad Mini MK3: CONNECTED")
        return True
    else:
        print("WARNING: Launchpad not detected!")
        return False

def create_session_folder():
    """Create folder for this session's recordings."""
    from datetime import datetime
    
    session_name = datetime.now().strftime("session_%Y%m%d_%H%M%S")
    session_path = Path.home() / "Music/ClubMaquis/Sessions" / session_name
    session_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Session folder: {session_path}")
    return session_path

def main():
    print("""
    +=======================================+
    |        CLUB MAQUIS LAUNCHER           |
    |   DJ Nerys drops beats.               |
    |   Shelter pets get treats.            |
    +=======================================+
    """)
    
    # Pre-flight checks
    check_launchpad()
    session_folder = create_session_folder()
    
    # Launch applications
    launch_ableton()
    launch_quicktime_webcam()
    launch_quicktime_screen()
    launch_bird_video()
    launch_iphone_camera()
    
    print("\n" + "="*50)
    print("SESSION READY!")
    print(f"Recordings will be saved to: {session_folder}")
    print("="*50)
    print("\nWorkflow:")
    print("1. Wait for Ableton to fully load")
    print("2. Check Launchpad lights up")
    print("3. QuickTime: File > New Movie Recording (webcam)")
    print("4. QuickTime: File > New Screen Recording (Ableton)")
    print("5. Start iPhone recording")
    print("6. Click Record on all sources")
    print("7. CLAP for sync point")
    print("8. Let Nerys make music!")
    print("\nPress Ctrl+C when done to run post-session script.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSession ended. Running post-processing...")
        post_session(session_folder)

def post_session(session_folder):
    """Post-session tasks."""
    print("\nPost-session checklist:")
    print("[ ] Stop all recordings")
    print("[ ] Save Ableton project")
    print("[ ] Copy files to session folder")
    print(f"[ ] Run: python cat_dj_sync_pipeline.py --input-dir {session_folder}")

if __name__ == "__main__":
    main()
```

### Advanced Launcher with GUI

```python
#!/usr/bin/env python3
"""
Club Maquis Session Launcher - GUI Version
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import threading
from pathlib import Path

class ClubMaquisLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Club Maquis Launcher")
        self.root.geometry("400x500")
        self.root.configure(bg='#1a1a2e')
        
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        title = tk.Label(
            self.root, 
            text="CLUB MAQUIS",
            font=("Impact", 32),
            fg='#ff6b35',
            bg='#1a1a2e'
        )
        title.pack(pady=20)
        
        subtitle = tk.Label(
            self.root,
            text="DJ Nerys drops beats.\nShelter pets get treats.",
            font=("Arial", 12),
            fg='#aaaaaa',
            bg='#1a1a2e'
        )
        subtitle.pack()
        
        # Status frame
        status_frame = tk.Frame(self.root, bg='#1a1a2e')
        status_frame.pack(pady=20)
        
        self.status_labels = {}
        for item in ["Launchpad", "Ableton", "QuickTime", "Bird Video"]:
            frame = tk.Frame(status_frame, bg='#1a1a2e')
            frame.pack(fill='x', pady=2)
            
            label = tk.Label(frame, text=item, fg='white', bg='#1a1a2e', width=15, anchor='w')
            label.pack(side='left')
            
            status = tk.Label(frame, text="NOT READY", fg='#ff4444', bg='#1a1a2e')
            status.pack(side='left')
            self.status_labels[item] = status
        
        # Buttons
        btn_frame = tk.Frame(self.root, bg='#1a1a2e')
        btn_frame.pack(pady=30)
        
        launch_btn = tk.Button(
            btn_frame,
            text="LAUNCH SESSION",
            font=("Arial", 14, "bold"),
            bg='#ff6b35',
            fg='white',
            command=self.launch_all,
            width=20,
            height=2
        )
        launch_btn.pack(pady=10)
        
        check_btn = tk.Button(
            btn_frame,
            text="Check Status",
            bg='#4a4a6a',
            fg='white',
            command=self.check_status,
            width=20
        )
        check_btn.pack(pady=5)
    
    def update_status(self, item, ready):
        if ready:
            self.status_labels[item].config(text="READY", fg='#44ff44')
        else:
            self.status_labels[item].config(text="NOT READY", fg='#ff4444')
    
    def check_status(self):
        # Check Launchpad
        result = subprocess.run(
            ["system_profiler", "SPUSBDataType"],
            capture_output=True, text=True
        )
        self.update_status("Launchpad", "Launchpad" in result.stdout)
    
    def launch_all(self):
        threading.Thread(target=self._launch_all_threaded).start()
    
    def _launch_all_threaded(self):
        # Launch Ableton
        subprocess.Popen(["open", "-a", "Ableton Live 12 Suite"])
        self.root.after(3000, lambda: self.update_status("Ableton", True))
        
        # Launch QuickTime
        subprocess.Popen(["open", "-a", "QuickTime Player"])
        self.root.after(2000, lambda: self.update_status("QuickTime", True))
        
        # Launch bird video
        video_path = Path.home() / "Videos/birds_for_cats.mp4"
        if video_path.exists():
            subprocess.Popen(["open", "-a", "VLC", str(video_path)])
            self.root.after(1000, lambda: self.update_status("Bird Video", True))
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ClubMaquisLauncher()
    app.run()
```

### Shell Script Alternative (simpler)

```bash
#!/bin/bash
# club_maquis_launch.sh

echo "================================"
echo "    CLUB MAQUIS LAUNCHER"
echo "================================"

# Check Launchpad
if system_profiler SPUSBDataType | grep -q "Launchpad"; then
    echo "[OK] Launchpad connected"
else
    echo "[!!] Launchpad NOT detected"
fi

# Create session folder
SESSION=$(date +%Y%m%d_%H%M%S)
SESSION_DIR="$HOME/Music/ClubMaquis/Sessions/$SESSION"
mkdir -p "$SESSION_DIR"
echo "[OK] Session folder: $SESSION_DIR"

# Launch Ableton
echo "Launching Ableton..."
open -a "Ableton Live 12 Suite"
sleep 3

# Launch QuickTime
echo "Launching QuickTime..."
open -a "QuickTime Player"
sleep 2

# Launch bird video
BIRD_VIDEO="$HOME/Videos/birds_for_cats.mp4"
if [ -f "$BIRD_VIDEO" ]; then
    echo "Launching bird video..."
    open -a VLC "$BIRD_VIDEO" --args --loop
else
    echo "[!!] Bird video not found"
fi

echo ""
echo "================================"
echo "SESSION READY!"
echo "================================"
echo ""
echo "1. Wait for Ableton to load"
echo "2. QuickTime: File > New Movie Recording (webcam)"
echo "3. QuickTime: File > New Screen Recording (Ableton)"
echo "4. Start iPhone camera"
echo "5. Click Record on all sources"
echo "6. CLAP for sync"
echo "7. Let Nerys DJ!"
echo ""
echo "Session folder: $SESSION_DIR"
```

Make executable:
```bash
chmod +x club_maquis_launch.sh
./club_maquis_launch.sh
```

---

## AbletonOSC Control

For deeper automation - control Ableton from Python via OSC.

### Installation

```bash
# Install AbletonOSC (Max for Live device)
# Download from: https://github.com/ideoforms/AbletonOSC

# Install Python OSC library
pip install python-osc
```

### Setup

1. Install AbletonOSC.amxd in Ableton
2. Drop it on any track
3. Note the port (default: 11000 receive, 11001 send)

### Python Control Script

```python
#!/usr/bin/env python3
"""
Control Ableton via OSC for Club Maquis sessions.
"""

from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
import threading
import time

class AbletonController:
    def __init__(self, send_port=11000, receive_port=11001):
        self.client = udp_client.SimpleUDPClient("127.0.0.1", send_port)
        self.receive_port = receive_port
        
    def play(self):
        """Start playback."""
        self.client.send_message("/live/song/start_playing", [])
    
    def stop(self):
        """Stop playback."""
        self.client.send_message("/live/song/stop_playing", [])
    
    def record(self):
        """Start recording."""
        self.client.send_message("/live/song/record", [])
    
    def set_tempo(self, bpm):
        """Set tempo."""
        self.client.send_message("/live/song/set/tempo", [float(bpm)])
    
    def arm_track(self, track_index):
        """Arm a track for recording."""
        self.client.send_message(f"/live/track/set/arm", [track_index, 1])
    
    def trigger_clip(self, track, clip):
        """Trigger a clip."""
        self.client.send_message("/live/clip/fire", [track, clip])
    
    def set_track_volume(self, track, volume):
        """Set track volume (0.0 - 1.0)."""
        self.client.send_message("/live/track/set/volume", [track, float(volume)])
    
    def create_clip(self, track, slot, length=4.0):
        """Create a new clip."""
        self.client.send_message("/live/clip_slot/create_clip", [track, slot, float(length)])
    
    def start_cat_session(self):
        """Initialize a cat DJ session."""
        print("Initializing cat DJ session...")
        
        # Set tempo
        self.set_tempo(120)
        
        # Arm recording tracks
        self.arm_track(0)  # Cat pads track
        self.arm_track(3)  # Master recording track
        
        # Start recording
        self.record()
        
        print("Recording started! Let Nerys DJ!")
    
    def end_cat_session(self):
        """End the session."""
        self.stop()
        print("Session ended. Don't forget to save!")

# Usage
if __name__ == "__main__":
    ableton = AbletonController()
    
    print("Commands:")
    print("  p = play")
    print("  s = stop")
    print("  r = record")
    print("  c = start cat session")
    print("  e = end session")
    print("  q = quit")
    
    while True:
        cmd = input("> ").strip().lower()
        
        if cmd == 'p':
            ableton.play()
        elif cmd == 's':
            ableton.stop()
        elif cmd == 'r':
            ableton.record()
        elif cmd == 'c':
            ableton.start_cat_session()
        elif cmd == 'e':
            ableton.end_cat_session()
        elif cmd == 'q':
            break
```

### AbletonOSC Message Reference

| Message | Parameters | Description |
|---------|------------|-------------|
| `/live/song/start_playing` | - | Start playback |
| `/live/song/stop_playing` | - | Stop playback |
| `/live/song/record` | - | Toggle recording |
| `/live/song/set/tempo` | [float] | Set BPM |
| `/live/track/set/arm` | [track, 0/1] | Arm track |
| `/live/track/set/volume` | [track, 0-1] | Set volume |
| `/live/track/set/mute` | [track, 0/1] | Mute track |
| `/live/clip/fire` | [track, clip] | Trigger clip |
| `/live/clip_slot/create_clip` | [track, slot, length] | Create clip |

---

## MIDI Controller Scripts

Custom Launchpad behavior via Python MIDI scripts.

### Location

```
macOS: /Applications/Ableton Live [version]/Contents/App-Resources/MIDI Remote Scripts/
Windows: C:\ProgramData\Ableton\Live [version]\Resources\MIDI Remote Scripts\
```

### Custom Script Structure

```
MIDI Remote Scripts/
└── ClubMaquis/
    ├── __init__.py
    └── ClubMaquis.py
```

### Basic Custom Script

```python
# __init__.py
from .ClubMaquis import ClubMaquis

def create_instance(c_instance):
    return ClubMaquis(c_instance)
```

```python
# ClubMaquis.py
"""
Custom Launchpad script for Club Maquis.
Optimized for cat paw interaction.
"""

from __future__ import absolute_import
import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.ButtonElement import ButtonElement
from _Framework.InputControlElement import MIDI_NOTE_TYPE

class ClubMaquis(ControlSurface):
    
    def __init__(self, c_instance):
        super(ClubMaquis, self).__init__(c_instance)
        
        with self.component_guard():
            self._setup_controls()
            self.log_message("Club Maquis script loaded - DJ Nerys ready!")
    
    def _setup_controls(self):
        """Set up Launchpad buttons."""
        # Configure for cat-friendly behavior
        # All pads trigger on any velocity
        pass
    
    def disconnect(self):
        """Clean up when disconnecting."""
        super(ClubMaquis, self).disconnect()
```

**Note:** Custom MIDI scripts are complex. For most use cases, the built-in Launchpad support + Drum Rack is sufficient.

---

## ClyphX Pro Automation

Third-party text-based scripting ($40, very powerful).

### Installation

1. Purchase from isotonikstudios.com
2. Install .amxd device
3. Create action lists in text files

### Example Actions for Cat DJ

```
# ClyphX Pro X-Triggers

# When session starts
[START_SESSION]
METRO OFF; ARM 1 ON; ARM 4 ON; BPM 120

# Panic button - stop everything
[PANIC]
STOPALL; ALL/ARM OFF; METRO OFF

# Start recording
[REC_START]
ARM 1 ON; ARM 4 ON; WAIT 1; REC

# Quick save
[SAVE]
SAVE; MSG "Session saved!"

# Cat walked away - pause
[CAT_BREAK]
STOP; MSG "Cat break time"
```

### Button Mapping

Map Launchpad buttons to trigger X-Clips:
- Top row for session control
- Bottom rows for cat interaction (sounds)

---

## Full Session Workflow

### Pre-Session (5 minutes before)

```bash
# Run launcher script
./club_maquis_launch.sh

# Or Python version
python session_launcher.py
```

**Checklist:**
- [ ] Launchpad connected and lit
- [ ] Ableton loaded with template
- [ ] QuickTime open
- [ ] Bird video playing on second monitor
- [ ] iPhone mounted and ready
- [ ] Treats nearby for cat motivation

### Session Start

1. **Start all recordings:**
   - QuickTime: File > New Movie Recording, click Record (webcam)
   - QuickTime: File > New Screen Recording, click Record (Ableton window)
   - iPhone: Start camera recording
   - Ableton: Already armed from template

2. **Create sync point:**
   ```
   CLAP LOUDLY (or use clicker)
   This creates audio spike for syncing later
   ```

3. **Attract the cat:**
   - Point to bird video
   - Place treats on/near Launchpad
   - Wait for curiosity

4. **Let Nerys DJ:**
   - Don't interfere
   - Cat will step on pads
   - Ableton plays sounds
   - Music happens

### During Session

**If using AbletonOSC:**
```python
# Monitor and adjust from Python
ableton = AbletonController()

# If tempo feels wrong
ableton.set_tempo(110)

# If track too loud
ableton.set_track_volume(0, 0.7)
```

**Manual adjustments:**
- Adjust volumes if needed
- Mute tracks if needed
- Let it roll - imperfection is charming

### Session End

1. **Stop recordings:**
   - QuickTime: Click stop on both recordings, save files
   - iPhone: Stop camera
   - Ableton: Stop (spacebar)

2. **Save everything:**
   - Ableton: Cmd+S (save project)
   - QuickTime: Save recordings to session folder
   - Note session folder location

3. **Export MIDI:**
   - Ableton: Export MIDI clip from cat track

### Post-Session Processing

```bash
# Navigate to session folder
cd ~/Music/ClubMaquis/Sessions/[session_date]

# Sync all sources
python cat_dj_sync_pipeline.py --input-dir . --output-dir ./synced

# Detect cat activity
python cat_activity_detector.py \
    --video ./synced/webcam_sync.mp4 \
    --midi ./session.mid \
    --output segments.json

# Process with Magenta AI
python magenta_pipeline.py \
    --input ./synced/session_sync.mid \
    --output ./magenta/ \
    --tools drumify,groove \
    --simple

# Composite video
python video_compositor.py \
    --webcam ./synced/webcam_sync.mp4 \
    --phone ./synced/phone_sync.mp4 \
    --audio ./rendered/mix.wav \
    --output ./final.mp4
```

---

## Troubleshooting

### Launchpad Not Detected

```bash
# Check USB connection
system_profiler SPUSBDataType | grep -A 10 "Launchpad"

# Reset MIDI in Ableton
# Preferences > Link/MIDI > Reset all MIDI devices

# Restart Launchpad
# Unplug, wait 5 seconds, replug
```

### Audio Issues

```
No sound from Launchpad presses:
1. Check Ableton track is armed (record button lit)
2. Check MIDI input in Preferences > Link/MIDI
3. Check track output routing
4. Check master volume

QuickTime screen recording has no audio:
1. When starting screen recording, click dropdown arrow
2. Select "Internal Microphone" or audio source
3. For system audio, need BlackHole or similar virtual audio device
```

### Ableton Won't Start with Template

```bash
# Check template path
ls ~/Music/Ableton/User\ Library/Templates/

# Check Options.txt syntax
cat ~/Library/Preferences/Ableton/Live\ 12/Options.txt

# Remove Options.txt to reset
rm ~/Library/Preferences/Ableton/Live\ 12/Options.txt
```

### QuickTime Recording Issues

```
Camera not available:
1. System Preferences > Security & Privacy > Camera
2. Enable QuickTime Player
3. Restart QuickTime

Screen recording permission:
1. System Preferences > Security & Privacy > Screen Recording
2. Enable QuickTime Player
3. Restart QuickTime
```

### Cat Won't Cooperate

```
Solutions:
- Try different time of day (cats are crepuscular - dawn/dusk)
- Use higher value treats
- Change bird video (fish might work better)
- Put catnip on Launchpad (carefully)
- Be patient - cats gonna cat
```

---

## Quick Reference

### File Locations (macOS)

| File | Path |
|------|------|
| Ableton Templates | `~/Music/Ableton/User Library/Templates/` |
| Options.txt | `~/Library/Preferences/Ableton/Live [ver]/Options.txt` |
| MIDI Scripts | `/Applications/Ableton Live [ver]/Contents/App-Resources/MIDI Remote Scripts/` |
| Session Recordings | `~/Music/ClubMaquis/Sessions/` |

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Play/Stop | Space |
| Record | F9 |
| Save | Cmd+S |
| Export | Cmd+Shift+R |
| Arm Track | Select track, press button |
| Metronome | Cmd+Shift+M |

### Emergency Commands

```bash
# Kill all audio apps
killall "Ableton Live 12 Suite" "QuickTime Player" VLC

# Force quit Ableton
killall -9 "Ableton Live 12 Suite"

# Reset audio
sudo killall coreaudiod
```

---

## Summary

| Automation Level | Method | Effort |
|------------------|--------|--------|
| Basic | Template project | 30 min setup, then automatic |
| Intermediate | Launch script + Template | 1-2 hours |
| Advanced | AbletonOSC + Python | 4-8 hours |
| Expert | Custom MIDI scripts | Days |

**Recommendation:** Start with Template + Shell Script. Add AbletonOSC only if you need real-time Python control.

---

*Where cats drop beats. Shelter pets get treats.*
