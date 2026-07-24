#!/usr/bin/env python3
"""Desktop app for compressing videos for Discord using ffmpeg."""

from tkinter import PhotoImage, filedialog
import customtkinter
from tkinterdnd2 import TkinterDnD, DND_ALL
from math import floor, ceil
from cv2 import CAP_PROP_FRAME_COUNT, CAP_PROP_FPS, VideoCapture
from subprocess import CalledProcessError, STDOUT, PIPE, check_call, Popen
from os import path, remove, name
from time import sleep, time
from threading import Thread
from psutil import process_iter
from json import load, dump
from sys import argv
from re import search

# Platform-specific imports
IS_WINDOWS = name == 'nt'
if IS_WINDOWS:
    from os import startfile
    from subprocess import CREATE_NO_WINDOW

# ---------------------------------------------------------------------------
# Module-level constants & config
# ---------------------------------------------------------------------------

base_path = path.dirname(path.abspath(__file__))
config = load(open(base_path + "/config.json", "r"))
ffmpeg_map = config["ffmpeg_mapping"]["nt"] if IS_WINDOWS else config["ffmpeg_mapping"]["nx"]
_target_size_efficiency = float(config["target_size_efficiency"])
config_path = base_path + "/config.json"

# ---------------------------------------------------------------------------
# UI theme setup
# ---------------------------------------------------------------------------

customtkinter.set_appearance_mode("system")
_theme_map = {
    1: "/cpu-theme.json",
    2: "/amd-theme.json",
    3: "/nvidia-theme.json",
    4: "/intel-theme.json",
}
customtkinter.set_default_color_theme(base_path + _theme_map[config["encoding_choice"]])

# ---------------------------------------------------------------------------
# Display text constants
# ---------------------------------------------------------------------------

texts = {
    "title": "Why Discord, why?",
    "select_input": "Select clip to compress\n(or drop it over this program)",
    "warm_up": "Warming ffmpeg engine ⚙️",
    "first_step_encoding": "Generating video info 🕒",
    "second_step_encoding": "Encoding compressed video 🎥",
    "encoding_completed": "Encoding completed 💯",
    "encoding_error": "Error during video encoding ❌",
    "ffmpeg_not_found": "Couldn't find ffmpeg ❌",
    "file_not_found": "Doesn't look like a video file to me ⁴⁰⁴",
    "description": "CPU is slower but more precise, GPU is way faster, but could generate results bigger than target size",
}

# ---------------------------------------------------------------------------
# CustomTkinter class
# ---------------------------------------------------------------------------

class CTk(customtkinter.CTk, TkinterDnD.DnDWrapper):
    """Custom Tkinter wrapper that works with tkinterdnd2."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

# ---------------------------------------------------------------------------
# Application lifecycle functions
# ---------------------------------------------------------------------------

def save_config():
    """Persist the current config dict to config.json."""
    with open(config_path, "w") as f:
        dump(config, f, indent=4)


def build_ffmpeg_command(template, ffmpeg_path, filename, target_video_codec,
                         video_bitrate, result_filename):
    """Substitute template variables into ffmpeg pass1/pass2 command strings."""
    return (
        template
        .replace("$FFMPEG_PATH", ffmpeg_path)
        .replace("$INPUT", filename.replace(' ', '\x00'))
        .replace("$VIDEO_CODEC", target_video_codec)
        .replace("$VIDEO_BITRATE", str(video_bitrate))
        .replace("$FPS", config["target_fps"])
        .replace("$RESOLUTION", config["target_resolution"])
        .replace("$AUDIO_CODEC", config["target_audio_codec"])
        .replace("$AUDIO_BITRATE", config["target_audio_bitrate"])
        .replace("$DOUBLE_VID_BITRATE", str(video_bitrate * 2))
        .replace("$OUTPUT", result_filename.replace(' ', '\x00'))
    )


def compute_bitrate(filename):
    """Calculate target video bitrate from frame count, FPS, and target size."""
    video = VideoCapture(filename)
    frames = video.get(CAP_PROP_FRAME_COUNT)
    fps = video.get(CAP_PROP_FPS)

    try:
        duration_seconds = ceil(frames / fps)
    except ZeroDivisionError:
        return None

    target_size = int(config["target_size_mb"]) * _target_size_efficiency
    bitrate = floor(target_size * 8388.608 / duration_seconds) - int(config["target_audio_bitrate"])

    print(f"MAXSIZEMB: {config['target_size_mb']}")
    print(f"SECONDS: {duration_seconds}")
    print(f"TARGET_BITRATE: {bitrate}")

    return (duration_seconds, bitrate)


def _open_process(command, filepath):
    """Open a subprocess with platform-appropriate kwargs."""
    kwargs = {"cwd": filepath, "stderr": STDOUT, "stdout": PIPE}
    if IS_WINDOWS:
        kwargs["creationflags"] = CREATE_NO_WINDOW
    return Popen(command, **kwargs)


def ffmpeg_routine(filename, video_bitrate, duration_seconds, filepath):
    """Build and run ffmpeg encoding commands in this thread."""
    progresslabel.configure(text=texts["warm_up"], text_color=yellow)

    choice_map = {1: "cpu", 2: "amd", 3: "nvidia", 4: "intel"}
    encoding_choice = config["encoding_choice"]
    user_radio_choice = radio_encoder_var.get()

    ffmpeg_path = (
        "ffmpeg"
        if not IS_WINDOWS
        else path.abspath(path.join(path.dirname(__file__), "ffmpeg\\ffmpeg.exe"))
    )

    if encoding_choice == user_radio_choice:
        actual_choice = ffmpeg_map[choice_map[encoding_choice]]
    else:
        actual_choice = ffmpeg_map[choice_map[user_radio_choice]]

    target_video_codec = actual_choice["default_video_codec"]
    file_format = filename.split('.')[-1]
    result_filename = (
        filename.replace(f".{file_format}",
                         f"-{target_video_codec}-compressed.{file_format}")
    )
    print(f"RESULT_FILENAME: {result_filename}")

    pass1_string = build_ffmpeg_command(
        actual_choice["pass1"], ffmpeg_path, filename,
        target_video_codec, video_bitrate, result_filename
    )
    pass2_string = build_ffmpeg_command(
        actual_choice["pass2"], ffmpeg_path, filename,
        target_video_codec, video_bitrate, result_filename
    )

    pass1_command = [s.replace('\x00', ' ') for s in pass1_string.split(" ")]
    pass2_command = [s.replace('\x00', ' ') for s in pass2_string.split(" ")]

    print(f"PASS1_COMMAND: {pass1_command}")
    print(f"PASS2_COMMAND: {pass2_command}")

    start_time = time()

    try:
        start_percentage = 0
        end_percentage = 100

        if user_radio_choice == 1:
            end_percentage = 50
            process = _open_process(pass1_command, filepath)
            compute_completion_percentage(
                process, duration_seconds, progresslabel,
                texts["first_step_encoding"], yellow,
                start_percentage, end_percentage
            )
            start_percentage = 50

        process = _open_process(pass2_command, filepath)
        compute_completion_percentage(
            process, duration_seconds, progresslabel,
            texts["second_step_encoding"], orange,
            start_percentage, end_percentage
        )

        progresslabel.configure(text=texts["encoding_completed"], text_color=green)

    except CalledProcessError:
        progresslabel.configure(text=texts["encoding_error"], text_color=red)
        if path.isfile(result_filename) and result_filename != filename:
            remove(result_filename)
    except FileNotFoundError:
        progresslabel.configure(text=texts["ffmpeg_not_found"], text_color=red)

    end_time = time()
    print(f"Encoding took {end_time - start_time:.2f} seconds to complete.")

    change_buttons_status("normal")
    selectfilebutton.configure(text=texts["select_input"])

    # Clean up ffmpeg log files
    log_files = [
        "x265_2pass.log", "x265_2pass.log.cutree",
        "x265_2pass.log.temp", "x265_2pass.log.cutree.temp",
        "ffmpeg2pass-0.log", "ffmpeg2pass-0.log.mbtree",
    ]
    for log_file in log_files:
        log_path = path.join(filepath, log_file)
        if path.isfile(log_path):
            remove(log_path)

    if IS_WINDOWS:
        startfile(filepath=filepath)
    else:
        check_call(["xdg-open", filepath])


def compute_completion_percentage(process, duration_seconds, progresslabel,
                                  original_text, color,
                                  start_percentage, end_percentage):
    """Monitor ffmpeg stdout and update progress label with estimated completion."""
    pattern = r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})"
    while process.poll() is None:
        match = search(pattern, process.stdout.read(200).decode("utf-8").strip())
        if match:
            _, minutes, seconds = match.groups()
            current_seconds = int(minutes) * 60 + floor(float(seconds))
            integer_percentage = floor(
                current_seconds * end_percentage / duration_seconds
            )
            progresslabel.configure(
                text=original_text + " " + f"{start_percentage + integer_percentage:02}%",
                text_color=color
            )
        sleep(0.1)


def select_file_to_compress(fullpath=None):
    """Open file dialog or handle drag-and-drop, then start encoding thread."""
    if fullpath is None:
        fullpath = filedialog.askopenfilename()
    if fullpath in ("", ()):
        change_buttons_status("normal")
        progresslabel.configure(
            text=texts["file_not_found"], text_color="#C96868"
        )
        return

    print(fullpath)
    folderpath = path.dirname(fullpath)
    print(folderpath)

    duration_seconds, bitrate = compute_bitrate(fullpath)
    change_buttons_status("disabled")

    if bitrate:
        selectfilebutton.configure(text=path.basename(fullpath))
        ffmpeg_thread = Thread(
            target=ffmpeg_routine,
            args=(fullpath, bitrate, duration_seconds, folderpath),
            daemon=True
        )
        ffmpeg_thread.start()
    else:
        change_buttons_status("normal")
        progresslabel.configure(
            text=texts["file_not_found"], text_color="#C96868"
        )


def on_close():
    """Destroy the app and kill any running ffmpeg processes."""
    print("Closing...")
    app.destroy()
    for proc in process_iter():
        if proc.name() in ("ffmpeg.exe", "ffmpeg"):
            proc.kill()
            break


def get_dnd_path(event):
    """Handle drag-and-drop file events."""
    dropped_file = event.data.replace("{", "").replace("}", "")
    print(dropped_file)
    select_file_to_compress(dropped_file)


def update_target_size(value):
    """Update the target size label and persist config on slider move."""
    int_value = int(float(value))
    target_size_value.configure(text=f"{int_value} MB")
    config["target_size_mb"] = str(int_value)


def update_target_fps(value):
    """Update the target FPS label and persist config on slider move."""
    int_value = int(value)
    target_fps_value.configure(text=f"{int_value} fps")
    config["target_fps"] = str(int_value)


def on_encoder_change(*args):
    """Persist the selected encoder choice to config on change."""
    config["encoding_choice"] = radio_encoder_var.get()
    save_config()


def change_buttons_status(status):
    """Enable or disable all interactive widgets."""
    selectfilebutton.configure(state=status)
    for rb in encoder_radio_buttons:
        rb.configure(state=status)
    target_size_slider.configure(state=status)

# ---------------------------------------------------------------------------
# App initialization
# ---------------------------------------------------------------------------

app = CTk()
if IS_WINDOWS:
    app.iconbitmap(base_path + "\\icon.ico")
else:
    img = PhotoImage(file=base_path + "/icon.png")
    app.iconphoto(True, img)
app.title(texts["title"])
app.resizable(False, False)

# Color constants for UI elements
red = "#DC143C"
yellow = "#FCDC94"
green = "#008000"
orange = "#FFBE98"
blue = "#1E90FF"

# ---------------------------------------------------------------------------
# Reactive state variables
# ---------------------------------------------------------------------------

radio_encoder_var = customtkinter.IntVar(value=config["encoding_choice"])
target_size_var = customtkinter.DoubleVar(value=float(config["target_size_mb"]))
target_fps_var = customtkinter.IntVar(value=int(config["target_fps"]))

# ---------------------------------------------------------------------------
# GUI layout
# ---------------------------------------------------------------------------

encoder_radio_buttons = []

title_label = customtkinter.CTkLabel(
    master=app, text=texts["title"], font=('Helvetica bold', 32)
)
title_label.grid(row=0, column=0, padx=20, pady=20, columnspan=4)

radio_configs = [
    (1, "CPU (SW)", None),
    (2, "AMD (HW)", red),
    (3, "Nvidia (HW)", green),
    (4, "Intel (HW)", blue),
]
for value, text, color in radio_configs:
    kwargs = {
        "master": app, "text": text, "variable": radio_encoder_var,
        "value": value, "font": ('Helvetica bold', 18),
    }
    if color:
        kwargs["text_color"] = color
    rb = customtkinter.CTkRadioButton(**kwargs)
    rb.grid(row=1, column=value - 1)
    encoder_radio_buttons.append(rb)

radio_encoder_var.trace_add("write", on_encoder_change)

# Target size frame + slider
target_size_frame = customtkinter.CTkFrame(
    master=app, fg_color="transparent"
)
target_size_frame.grid(row=2, column=0, padx=20, pady=(15, 0), columnspan=4)

target_size_prefix = customtkinter.CTkLabel(
    master=target_size_frame, text="Target size: ", font=('Helvetica', 16)
)
target_size_prefix.grid(row=0, column=0)

target_size_value = customtkinter.CTkLabel(
    master=target_size_frame,
    text=f"{config['target_size_mb']} MB",
    font=('Helvetica bold', 16)
)
target_size_value.grid(row=0, column=1)

target_size_slider = customtkinter.CTkSlider(
    master=app, from_=5, to=500, variable=target_size_var,
    command=update_target_size, number_of_steps=99
)
target_size_slider.grid(
    row=3, column=0, padx=20, pady=(0, 10), columnspan=4, sticky="ew"
)
target_size_slider.bind("<ButtonRelease-1>", lambda e: save_config())

# Target FPS frame + slider
target_fps_frame = customtkinter.CTkFrame(
    master=app, fg_color="transparent"
)
target_fps_frame.grid(row=4, column=0, padx=20, pady=(15, 0), columnspan=4)

target_fps_prefix = customtkinter.CTkLabel(
    master=target_fps_frame, text="Target fps: ", font=('Helvetica', 16)
)
target_fps_prefix.grid(row=0, column=0)

target_fps_value = customtkinter.CTkLabel(
    master=target_fps_frame,
    text=f"{config['target_fps']} fps",
    font=('Helvetica bold', 16)
)
target_fps_value.grid(row=0, column=1)

target_fps_slider = customtkinter.CTkSlider(
    master=app, from_=0, to=60, variable=target_fps_var,
    command=update_target_fps, number_of_steps=60
)
target_fps_slider.grid(
    row=5, column=0, padx=20, pady=(0, 10), columnspan=4, sticky="ew"
)
target_fps_slider.bind("<ButtonRelease-1>", lambda e: save_config())

# Warning label
warninglabel = customtkinter.CTkLabel(
    master=app, text=texts["description"], font=('Helvetica bold', 14)
)
warninglabel.grid(row=6, column=0, padx=20, pady=20, columnspan=4)

# File selection button
selectfilebutton = customtkinter.CTkButton(
    master=app, text=texts["select_input"],
    command=lambda: select_file_to_compress(None),
    font=('Helvetica bold', 18)
)
selectfilebutton.grid(row=7, column=0, padx=20, pady=20, columnspan=4)

# Drag-and-drop support
app.drop_target_register(DND_ALL)
app.dnd_bind("<<Drop>>", get_dnd_path)

# Progress label
progresslabel = customtkinter.CTkLabel(
    master=app, text="", font=('Helvetica bold', 18)
)
progresslabel.grid(row=8, column=0, padx=20, pady=20, columnspan=4)

# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

if len(argv) == 2:
    select_file_to_compress(argv[1].replace("\\", "/"))

app.protocol("WM_DELETE_WINDOW", on_close)
app.mainloop()
