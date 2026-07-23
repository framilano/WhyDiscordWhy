# WhyDiscordWhy

Desktop app for compressing videos for Discord using ffmpeg. Built with CustomTkinter + tkinterdnd2.

## Project Structure

- `whydiscordwhy.py` — Main app (GUI + encoding logic, ~296 lines)
- `config.json` — User config + ffmpeg command templates per platform/encoder
- `cpu-theme.json` / `amd-theme.json` / `nvidia-theme.json` / `intel-theme.json` — CTk themes

## Architecture

### Config (`config.json`)
- `target_size_mb` — stored as string, used as int via `int(config["target_size_mb"])`
- `encoding_choice` — 1=cpu, 2=amd, 3=nvidia, 4=intel
- `ffmpeg_mapping.nt` / `ffmpeg_mapping.nx` — ffmpeg command templates per encoder

### Key functions in `whydiscordwhy.py`
| Function | Line | Purpose |
|---|---|---|
| `build_ffmpeg_command()` | 83 | Substitutes template vars into pass1/pass2 strings |
| `update_target_size()` | 96 | Updates label + config dict on slider move |
| `on_encoder_change()` | 101 | Persists radio button choice on change |
| `save_config()` | 79 | Writes config dict to `config.json` |
| `change_buttons_status()` | 110 | Enables/disables all interactive widgets |
| `compute_bitrate()` | 116 | Calculates target video bitrate from duration + target size |
| `ffmpeg_routine()` | 136 | Builds ffmpeg commands, runs encoding in thread |
| `select_file_to_compress()` | 219 | Opens file dialog, starts encoding thread |
| `on_close()` | 242 | Kills ffmpeg on window close |

### GUI layout (grid)
- Row 0: Title (colspan 4)
- Row 1: Encoder radio buttons (cols 0–3)
- Row 2: Target size label (colspan 4)
- Row 3: Target size slider (colspan 4, sticky="ew", range 5–500 MB, steps of 5)
- Row 4: Description/warning label (colspan 4)
- Row 5: Select file button (colspan 4)
- Row 6: Progress label (colspan 4)

### Widget lists
- `encoder_radio_buttons` — list of 4 CTkRadioButton widgets, iterated in `change_buttons_status()`

### Persistence
- Slider value saves to `config.json` on `<ButtonRelease-1>` (not every tick)
- Radio button choice saves immediately on change via `trace_add("write", on_encoder_change)`
- Config loaded at startup from `base_path + "/config.json"`

### Base path
- `base_path` computed once at line 22: strips `/_internal` or `\_internal` suffix from `__file__` directory
