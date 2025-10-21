from tkinter import PhotoImage, filedialog
import customtkinter
from tkinterdnd2 import TkinterDnD, DND_ALL
from math import floor, ceil
from cv2 import CAP_PROP_FRAME_COUNT, CAP_PROP_FPS, VideoCapture
from subprocess import CalledProcessError, STDOUT, check_call
from os import path, remove, name
if name == 'nt':
    from subprocess import CREATE_NO_WINDOW
    from os import startfile
from threading import Thread
from psutil import process_iter
from json import load
from sys import argv

#Loading config file
internal_folder_name = ""
if name == 'nt': internal_folder_name = "\\_internal"
else: internal_folder_name = "/_internal"
config = load(open(path.dirname(__file__).replace(internal_folder_name, "") + "/config.json", "r"))
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
    "first_step_encoding": "Generating video info 🕒",
    "second_step_encoding": "Encoding compressed video 🎞️",
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
    case 1: customtkinter.set_default_color_theme(path.dirname(__file__).replace(internal_folder_name, "") + "/cpu-theme.json")
    case 2: customtkinter.set_default_color_theme(path.dirname(__file__).replace(internal_folder_name, "") + "/amd-theme.json")
    case 3: customtkinter.set_default_color_theme(path.dirname(__file__).replace(internal_folder_name, "") + "/nvidia-theme.json")
    case 4: customtkinter.set_default_color_theme(path.dirname(__file__).replace(internal_folder_name, "") + "/intel-theme.json")

# Load app and icon
app = CTk()
if name == 'nt': app.iconbitmap(path.dirname(__file__).replace(internal_folder_name, "") + "\\icon.ico")
else:
    img = PhotoImage(file=path.dirname(__file__).replace(internal_folder_name, "") + "/icon.png")  
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

def get_dnd_path(event):
    dropped_file = event.data.replace("{","").replace("}", "")
    print(dropped_file)
    select_file_to_compress(dropped_file)

def change_buttons_status(status):
    selectfilebutton.configure(state=status)
    radiobutton_1.configure(state=status)
    radiobutton_2.configure(state=status)
    radiobutton_3.configure(state=status)
    radiobutton_4.configure(state=status)

def compute_bitrate(filename):
    video = VideoCapture(filename)
    
    # count the number of frames 
    frames = video.get(CAP_PROP_FRAME_COUNT) 
    fps = video.get(CAP_PROP_FPS) 
    
    # calculate duration of the video 
    try: seconds = ceil(frames / fps) 
    except (ZeroDivisionError): return None

    target_size = int(config["target_size_mb"]) * 0.9

    print("MAXSIZEMB: ", config["target_size_mb"])
    print("SECONDS: ", seconds)
    # Computing bitrate
    return floor(target_size * 8388.608 / seconds) - int(config["target_audio_bitrate"])

def ffmpeg_routine(filename, video_bitrate, filepath):
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

    pass1_string = actual_choice["pass1"]
    pass2_string = actual_choice["pass2"]
    
    pass1_string = pass1_string \
        .replace("$FFMPEG_PATH", ffmpeg_path) \
        .replace("$INPUT", filename) \
        .replace("$VIDEO_CODEC", target_video_codec) \
        .replace("$VIDEO_BITRATE", str(video_bitrate)) \
        .replace("$FPS", config["target_fps"]) \
        .replace("$RESOLUTION", config["target_resolution"]) \
        .replace("$AUDIO_CODEC", config["target_audio_codec"]) \
        .replace("$AUDIO_BITRATE", config["target_audio_bitrate"]) \
        .replace("$DOUBLE_VID_BITRATE", str(video_bitrate*2)) \
        .replace("$OUTPUT", result_filename)
    
    pass2_string = pass2_string \
        .replace("$FFMPEG_PATH", ffmpeg_path) \
        .replace("$INPUT", filename) \
        .replace("$VIDEO_CODEC", target_video_codec) \
        .replace("$VIDEO_BITRATE", str(video_bitrate)) \
        .replace("$FPS", config["target_fps"]) \
        .replace("$RESOLUTION", config["target_resolution"]) \
        .replace("$AUDIO_CODEC", config["target_audio_codec"]) \
        .replace("$AUDIO_BITRATE", config["target_audio_bitrate"]) \
        .replace("$DOUBLE_VID_BITRATE", str(video_bitrate*2)) \
        .replace("$OUTPUT", result_filename)
    
    print("PASS1_STRING:", pass1_string)
    print("PASS2_STRING:", pass2_string)


    try:
        if (user_radio_choice == 1):
            progresslabel.configure(text=texts["first_step_encoding"])
            progresslabel.configure(text_color=yellow)
            if name == 'nt': check_call(pass1_string.split(" "), cwd=filepath, stderr=STDOUT, creationflags=CREATE_NO_WINDOW)
            else: check_call(pass1_string.split(" "), cwd=filepath, stderr=STDOUT)
        progresslabel.configure(text=texts["second_step_encoding"])
        progresslabel.configure(text_color=orange)
        if name == 'nt': check_call(pass2_string.split(" "), cwd=filepath, stderr=STDOUT, creationflags=CREATE_NO_WINDOW)
        else: check_call(pass2_string.split(" "), cwd=filepath, stderr=STDOUT)
        
        progresslabel.configure(text=texts["encoding_completed"])
        progresslabel.configure(text_color=green)
    except(CalledProcessError):
        progresslabel.configure(text=texts["encoding_error"])
        progresslabel.configure(text_color=red)

        if path.isfile(result_filename) and result_filename != filename: remove(result_filename)
    except(FileNotFoundError):
        progresslabel.configure(text=texts["ffmpeg_not_found"])
        progresslabel.configure(text_color=red)
    
    change_buttons_status("normal")
    selectfilebutton.configure(text = texts["select_input"])

    #Cleaning...
    if path.isfile(filepath + "/x265_2pass.log"): remove(filepath + "/x265_2pass.log")
    if path.isfile(filepath + "/x265_2pass.log.cutree"): remove(filepath + "/x265_2pass.log.cutree")
    if path.isfile(filepath + "/x265_2pass.log.temp"): remove(filepath + "/x265_2pass.log.temp")
    if path.isfile(filepath + "/x265_2pass.log.cutree.temp"): remove(filepath + "/x265_2pass.log.cutree.temp")
    if path.isfile(filepath + "/ffmpeg2pass-0.log"): remove(filepath + "/ffmpeg2pass-0.log")

    if name == 'nt': startfile(filepath=filepath)
    else: check_call(["xdg-open", filepath])

def select_file_to_compress(fullpath):
    if (fullpath is None): fullpath = filedialog.askopenfilename()
    if fullpath == () or fullpath == '':
        change_buttons_status("normal")
        progresslabel.configure(text = texts["file_not_found"])
        progresslabel.configure(text_color="#C96868") 
        return
    
    print(fullpath)
    folderpath = "/".join(fullpath.split("/")[0:-1])
    print(folderpath)
    bitrate = compute_bitrate(fullpath)
    print("BITRATE: ", bitrate)

    #Disabling select button after selecting a file
    change_buttons_status("disabled")

    if (bitrate):
        selectfilebutton.configure(text = fullpath.split("/")[-1])
        ffmpeg_thread = Thread(target=ffmpeg_routine, args=(fullpath, bitrate, folderpath, ), daemon=True)
        ffmpeg_thread.start()
    else:
        change_buttons_status("normal")
        progresslabel.configure(text = texts["file_not_found"])
        progresslabel.configure(text_color="#C96868")

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

radiobutton_1 = customtkinter.CTkRadioButton(master=app, text="CPU (SW)", variable=radio_encoder_var, value=1, font=('Helvetica bold', 18))
radiobutton_1.grid(row=1, column=0)
radiobutton_2 = customtkinter.CTkRadioButton(master=app, text="AMD (HW)", variable=radio_encoder_var, value=2, text_color=red, font=('Helvetica bold', 18))
radiobutton_2.grid(row=1, column=1)
radiobutton_3 = customtkinter.CTkRadioButton(master=app, text="Nvidia (HW)", variable=radio_encoder_var, value=3, text_color=green, font=('Helvetica bold', 18))
radiobutton_3.grid(row=1, column=2)
radiobutton_4 = customtkinter.CTkRadioButton(master=app, text="Intel (HW)", variable=radio_encoder_var, value=4, text_color=blue, font=('Helvetica bold', 18))
radiobutton_4.grid(row=1, column=3)

warninglabel = customtkinter.CTkLabel(master=app, text=texts["description"], font=('Helvetica bold', 14))
warninglabel.grid(row=2, column=0, padx=20, pady=20, columnspan=4)

selectfilebutton = customtkinter.CTkButton(master=app, text=texts["select_input"], command=lambda: select_file_to_compress(None), font=('Helvetica bold', 18))
selectfilebutton.grid(row=3, column=0, padx=20, pady=20, columnspan=4)

# Makes the whole program drag-n-droppable
app.drop_target_register(DND_ALL)
app.dnd_bind("<<Drop>>", get_dnd_path)

progresslabel = customtkinter.CTkLabel(master=app, text="", font=('Helvetica bold', 18))
progresslabel.grid(row=4, column=0, padx=20, pady=20, columnspan=4)

if (len(argv) == 2): select_file_to_compress(argv[1].replace("\\", "/"))

app.protocol("WM_DELETE_WINDOW",  on_close)
app.mainloop()