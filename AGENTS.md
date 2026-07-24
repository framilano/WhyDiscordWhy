# WhyDiscordWhy

Desktop app for compressing videos for Discord using ffmpeg. Built with CustomTkinter + tkinterdnd2.

## Project Structure

- `whydiscordwhy.py` — Main app (GUI + encoding logic, ~317 lines)
- `config.json` — User config + ffmpeg command templates per platform/encoder
- `cpu-theme.json` / `amd-theme.json` / `nvidia-theme.json` / `intel-theme.json` — CTk themes

## Architecture

### Config (`config.json`)
- `target_size_mb` — stored as string, used as int via `int(config["target_size_mb"])`
- `encoding_choice` — 1=cpu, 2=amd, 3=nvidia, 4=intel
- `ffmpeg_mapping.nt` / `ffmpeg_mapping.nx` — ffmpeg command templates per encoder

### Key functions in `whydiscordwhy.py`
| Function | Purpose |
|---|---|
| `save_config()` | Persists config dict to `config.json` |
| `build_ffmpeg_command()` | Substitutes template vars into pass1/pass2 strings |
| `compute_bitrate()` | Calculates target video bitrate from duration + target size |
| `_open_process()` | Opens subprocess with platform-appropriate kwargs |
| `ffmpeg_routine()` | Builds ffmpeg commands, runs encoding in thread |
| `compute_completion_percentage()` | Monitors ffmpeg stdout and updates progress label |
| `select_file_to_compress()` | Opens file dialog, starts encoding thread |
| `get_dnd_path()` | Handles drag-and-drop file events |
| `update_target_size()` | Updates target size label and config |
| `update_target_fps()` | Updates target FPS label and config |
| `on_encoder_change()` | Persists radio button choice on change |
| `change_buttons_status()` | Enables/disables all interactive widgets |
| `on_close()` | Kills ffmpeg on window close |

### GUI layout (grid)
- Row 0: Title (colspan 4)
- Row 1: Encoder radio buttons (cols 0–3)
- Row 2: Target size label (colspan 4)
- Row 3: Target size slider (colspan 4, sticky="ew", range 5–500 MB, steps of 5)
- Row 4: Target fps label (colspan 4)
- Row 5: Target fps slider (colspan 4, sticky="ew", range 0–60 fps, steps of 1)
- Row 6: Description/warning label (colspan 4)
- Row 7: Select file button (colspan 4)
- Row 8: Progress label (colspan 4)

### Widget lists
- `encoder_radio_buttons` — list of 4 CTkRadioButton widgets, iterated in `change_buttons_status()`

### Persistence
- Slider value saves to `config.json` on `<ButtonRelease-1>` (not every tick)
- Radio button choice saves immediately on change via `trace_add("write", on_encoder_change)`
- Config loaded at startup from `base_path + "/config.json"`

### Module-level constants
- `IS_WINDOWS` — Centralized Windows platform check (`name == 'nt'`)
- `base_path` — Computed via `path.dirname(path.abspath(__file__))`
- `_target_size_efficiency` — Precomputed float from config for efficiency
- `texts` — Dictionary of UI text strings

### Windows-specific
- `CREATE_NO_WINDOW` / `startfile` — Conditionally imported and used for Windows
- `_open_process()` — Handles `creationflags` platform detection
