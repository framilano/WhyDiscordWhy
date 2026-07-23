from tkinter import PhotoImage, filedialog
import customtkinter
from tkinterdnd2 import TkinterDnD, DND_ALL
from math import floor, ceil
from cv2 import CAP_PROP_FRAME_COUNT, CAP_PROP_FPS, VideoCapture
from subprocess import CalledProcessError, STDOUT, PIPE, check_call, Popen
from os import path, remove, name
if name == 'nt':
    from os import startfile
from time import sleep
from threading import Thread
from psutil import process_iter
from json import load, dump
from sys import argv
from re import search
from time import time

#Loading config file
internal_folder_name = ""
if name == 'nt': internal_folder_name = "\\_internal"
else: internal_folder_name = "/_internal"
base_path = path.dirname(__file__).replace(internal_folder_name, "")
config = load(open(base_path + "/config.json", "r"))
ffmpeg_map = config["ffmpeg_mapping"]["nt"] if (name == "nt") else config["ffmpeg_mapping"]["nx"]
#Constructor for customtkinter that works with tkinterdnd2
class CTk(customtkinter.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

#Map of texts
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
    "description": "CPU is slower but more precise, GPU is way faster, but could generate results bigger than target size"
}

#APP code starts here

# Load theme
customtkinter.set_appearance_mode("system")  # Modes: system (default), light, dark
match config["encoding_choice"]:
    case 1: customtkinter.set_default_color_theme(base_path + "/cpu-theme.json")
    case 2: customtkinter.set_default_color_theme(base_path + "/amd-theme.json")
    case 3: customtkinter.set_default_color_theme(base_path + "/nvidia-theme.json")
    case 4: customtkinter.set_default_color_theme(base_path + "/intel-theme.json")

# Load app and icon
app = CTk()
if name == 'nt': app.iconbitmap(base_path + "\\icon.ico")
else:
    img = PhotoImage(file=base_path + "/icon.png")  
    app.iconphoto(True, img)
app.title(texts["title"])
app.resizable(False, False)

red = "#DC143C"
yellow = "#FCDC94"
green = "#008000"
orange = "#FFBE98"
blue = "#1E90FF"


# Defines which radio button is currently selected
radio_encoder_var = customtkinter.IntVar(value=config["encoding_choice"])

target_size_var = customtkinter.DoubleVar(value=float(config["target_size_mb"]))

config_path = base_path + "/config.json"
encoder_radio_buttons = []

def save_config():
    with open(config_path, "w") as f:
        dump(config, f, indent=4)

def build_ffmpeg_command(template, ffmpeg_path, filename, target_video_codec, video_bitrate, result_filename):
    return template \
        .replace("$FFMPEG_PATH", ffmpeg_path) \
        .replace("$INPUT", filename.replace(' ', '\x00')) \
        .replace("$VIDEO_CODEC", target_video_codec) \
        .replace("$VIDEO_BITRATE", str(video_bitrate)) \
        .replace("$FPS", config["target_fps"]) \
        .replace("$RESOLUTION", config["target_resolution"]) \
        .replace("$AUDIO_CODEC", config["target_audio_codec"]) \
        .replace("$AUDIO_BITRATE", config["target_audio_bitrate"]) \
        .replace("$DOUBLE_VID_BITRATE", str(video_bitrate*2)) \
        .replace("$OUTPUT", result_filename.replace(' ', '\x00'))

def update_target_size(value):
    int_value = int(float(value))
    target_size_value.configure(text=f"{int_value} MB")
    config["target_size_mb"] = str(int_value)

def on_encoder_change(*args):
    config["encoding_choice"] = radio_encoder_var.get()
    save_config()

def get_dnd_path(event):
    dropped_file = event.data.replace("{","").replace("}", "")
    print(dropped_file)
    select_file_to_compress(dropped_file)

def change_buttons_status(status):
    selectfilebutton.configure(state=status)
    for rb in encoder_radio_buttons:
        rb.configure(state=status)
    target_size_slider.configure(state=status)

def compute_bitrate(filename):
    video = VideoCapture(filename)
    
    # count the number of frames 
    frames = video.get(CAP_PROP_FRAME_COUNT) 
    fps = video.get(CAP_PROP_FPS) 
    
    # calculate duration of the video 
    try: duration_seconds = ceil(frames / fps) 
    except (ZeroDivisionError): return None

    target_size = int(config["target_size_mb"]) * float(config["target_size_efficiency"])
    bitrate = floor(target_size * 8388.608 / duration_seconds) - int(config["target_audio_bitrate"])
    print("MAXSIZEMB:", config["target_size_mb"])
    print("SECONDS:", duration_seconds)
    print("TARGET_BITRATE:", bitrate)
   
    # Computing bitrate
    return (duration_seconds, bitrate)

def ffmpeg_routine(filename, video_bitrate, duration_seconds, filepath):
    progresslabel.configure(text=texts["warm_up"], text_color=yellow)
    choice_map = {1: "cpu", 2: "amd", 3: "nvidia", 4: "intel"}
    encoding_choice = config["encoding_choice"]
    user_radio_choice = radio_encoder_var.get()
    ffmpeg_path = (path.abspath(path.join(path.dirname(__file__), 'ffmpeg\\ffmpeg.exe')) if name == "nt" else "ffmpeg")
    file_format = filename.split('.')[-1]
    
    if (encoding_choice == user_radio_choice): actual_choice = ffmpeg_map[choice_map[encoding_choice]]
    else: actual_choice = ffmpeg_map[choice_map[user_radio_choice]]
   
    target_video_codec = actual_choice["default_video_codec"]
    result_filename = filename.replace(f".{file_format}", f"-{target_video_codec}-compressed.{file_format}")

    print("RESULT_FILENAME:", result_filename)

    pass1_string = build_ffmpeg_command(actual_choice["pass1"], ffmpeg_path, filename, target_video_codec, video_bitrate, result_filename)
    pass2_string = build_ffmpeg_command(actual_choice["pass2"], ffmpeg_path, filename, target_video_codec, video_bitrate, result_filename)
    
    #If path contains spaces, we replace them with NUL characters, so can now split safely to obtain 'check_chall' input list
    #check_call needs these spaces in the list though, so we just replace them back to get this:
    #["ffmpeg", "-i", "my file with spaces"] 'check call' will automatically put quotes around one single element in the list if 
    #it contains any space
    pass1_command = [s.replace('\x00', ' ') for s in pass1_string.split(" ")]
    pass2_command = [s.replace('\x00', ' ') for s in pass2_string.split(" ")]

    print("PASS1_COMMAND:", pass1_command)
    print("PASS2_COMMAND:", pass2_command)

    # Starting time
    start_time = time()

    try:
        start_percentage = 0
        end_percentage = 100
        if (user_radio_choice == 1):
            end_percentage = 50
            if name == 'nt': process = Popen(pass1_command, cwd=filepath, stderr=STDOUT, stdout=PIPE)
            else: process = Popen(pass1_command, cwd=filepath, stderr=STDOUT, stdout=PIPE)
            compute_completion_percentage(process, duration_seconds, progresslabel, texts["first_step_encoding"], yellow, start_percentage, end_percentage)
            start_percentage = 50
        if name == 'nt': process = Popen(pass2_command, cwd=filepath, stderr=STDOUT, stdout=PIPE)
        else: process = Popen(pass2_command, cwd=filepath, stderr=STDOUT, stdout=PIPE)
        compute_completion_percentage(process, duration_seconds, progresslabel, texts["second_step_encoding"], orange, start_percentage, end_percentage)

        progresslabel.configure(text=texts["encoding_completed"], text_color=green)
    except(CalledProcessError):
        progresslabel.configure(text=texts["encoding_error"], text_color=red)
        if path.isfile(result_filename) and result_filename != filename: remove(result_filename)
    except(FileNotFoundError):
        progresslabel.configure(text=texts["ffmpeg_not_found"], text_color=red)
    
    end_time = time()  # Record the end time
    elapsed_time = end_time - start_time
    print(f"Encoding took {elapsed_time:.2f} seconds to complete.")
    change_buttons_status("normal")
    selectfilebutton.configure(text = texts["select_input"])

    #Cleaning...
    log_files = [
        "x265_2pass.log", "x265_2pass.log.cutree",
        "x265_2pass.log.temp", "x265_2pass.log.cutree.temp",
        "ffmpeg2pass-0.log", "ffmpeg2pass-0.log.mbtree",
    ]
    for log_file in log_files:
        log_path = path.join(filepath, log_file)
        if path.isfile(log_path):
            remove(log_path)

    if name == 'nt': startfile(filepath=filepath)
    else: check_call(["xdg-open", filepath])

def compute_completion_percentage(process, duration_seconds, progresslabel, original_text, color, start_percentage, end_percentage):
    pattern = r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})"
    while process.poll() is None:
        match = search(pattern, process.stdout.read(200).decode("utf-8").strip())
        if (match):
            hours, minutes, seconds = match.groups()
            current_seconds = int(minutes) * 60 + floor(float(seconds))
            integer_percentage = floor(current_seconds * end_percentage / duration_seconds)
            progresslabel.configure(text=original_text + " " + f"{start_percentage + integer_percentage:02}%", text_color=color)
        sleep (0.1)

def select_file_to_compress(fullpath):
    if (fullpath is None): fullpath = filedialog.askopenfilename()
    if fullpath == () or fullpath == '':
        change_buttons_status("normal")
        progresslabel.configure(text = texts["file_not_found"], text_color="#C96868")
        return
    
    print(fullpath)
    folderpath = "/".join(fullpath.split("/")[0:-1])
    print(folderpath)
    (duration_seconds, bitrate) = compute_bitrate(fullpath)

    #Disabling select button after selecting a file
    change_buttons_status("disabled")

    if (bitrate):
        selectfilebutton.configure(text = fullpath.split("/")[-1])
        ffmpeg_thread = Thread(target=ffmpeg_routine, args=(fullpath, bitrate, duration_seconds, folderpath, ), daemon=True)
        ffmpeg_thread.start()
    else:
        change_buttons_status("normal")
        progresslabel.configure(text = texts["file_not_found"], text_color="#C96868")

def on_close():  
    print("Closing...")  
    app.destroy()

    # Manually closing ffmpeg process...
    for proc in process_iter():
        if proc.name() == "ffmpeg.exe" or proc.name() =="ffmpeg":
            proc.kill()
            break

# ----------GUI SECTION----------

title_label = customtkinter.CTkLabel(master=app, text=texts["title"], font=('Helvetica bold', 32))
title_label.grid(row=0, column=0, padx=20, pady=20, columnspan=4)

radio_configs = [
    (1, "CPU (SW)", None),
    (2, "AMD (HW)", red),
    (3, "Nvidia (HW)", green),
    (4, "Intel (HW)", blue),
]
for value, text, color in radio_configs:
    kwargs = {"master": app, "text": text, "variable": radio_encoder_var, "value": value, "font": ('Helvetica bold', 18)}
    if color:
        kwargs["text_color"] = color
    rb = customtkinter.CTkRadioButton(**kwargs)
    rb.grid(row=1, column=value - 1)
    encoder_radio_buttons.append(rb)

radio_encoder_var.trace_add("write", on_encoder_change)

target_size_frame = customtkinter.CTkFrame(master=app, fg_color="transparent")
target_size_frame.grid(row=2, column=0, padx=20, pady=(15, 0), columnspan=4)
target_size_prefix = customtkinter.CTkLabel(master=target_size_frame, text="Target size: ", font=('Helvetica', 16))
target_size_prefix.grid(row=0, column=0)
target_size_value = customtkinter.CTkLabel(master=target_size_frame, text=f"{config['target_size_mb']} MB", font=('Helvetica bold', 16))
target_size_value.grid(row=0, column=1)

target_size_slider = customtkinter.CTkSlider(master=app, from_=5, to=500, variable=target_size_var, command=update_target_size, number_of_steps=99)
target_size_slider.grid(row=3, column=0, padx=20, pady=(0, 10), columnspan=4, sticky="ew")
target_size_slider.bind("<ButtonRelease-1>", lambda e: save_config())

warninglabel = customtkinter.CTkLabel(master=app, text=texts["description"], font=('Helvetica bold', 14))
warninglabel.grid(row=4, column=0, padx=20, pady=20, columnspan=4)

selectfilebutton = customtkinter.CTkButton(master=app, text=texts["select_input"], command=lambda: select_file_to_compress(None), font=('Helvetica bold', 18))
selectfilebutton.grid(row=5, column=0, padx=20, pady=20, columnspan=4)

# Makes the whole program drag-n-droppable
app.drop_target_register(DND_ALL)
app.dnd_bind("<<Drop>>", get_dnd_path)

progresslabel = customtkinter.CTkLabel(master=app, text="", font=('Helvetica bold', 18))
progresslabel.grid(row=6, column=0, padx=20, pady=20, columnspan=4)

if (len(argv) == 2): select_file_to_compress(argv[1].replace("\\", "/"))

app.protocol("WM_DELETE_WINDOW",  on_close)
app.mainloop()