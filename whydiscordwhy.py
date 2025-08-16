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
#Constructor for customtkinter that works with tkinterdnd2
class CTk(customtkinter.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

#Map of texts
texts = {
    "title": "Why Discord, why?",
    "select_input": "Select clip to compress\n(or drop it over this box)",
    "first_step_encoding": "Generating video info 🕒",
    "second_step_encoding": "Encoding compressed video 🎞️",
    "encoding_completed": "Encoding completed 💯",
    "encoding_error": "Error during video encoding ❌",
    "ffmpeg_not_found": "Couldn't find ffmpeg ❌",
    "file_not_found": "Doesn't look like a video file to me ⁴⁰⁴",
    "description": "CPU is slower but more precise, GPU is way faster, but could generate results bigger than target size"
}

#APP code starts here

customtkinter.set_appearance_mode("system")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme(path.dirname(__file__).replace(internal_folder_name, "") + "/" + config["theme_file_name"])  # Themes: blue (default), dark-blue, green

app = CTk()
if name == 'nt': app.iconbitmap(path.dirname(__file__).replace(internal_folder_name, "") + "\\icon.ico")
else:
    img = PhotoImage(file=path.dirname(__file__).replace(internal_folder_name, "") + "/icon.png")  
    app.iconphoto(True, img)
app.title(texts["title"])
app.resizable(False, False)

MAX_SIZE_MB = config["target_size_mb"]

red = "#DC143C"
yellow = "#FCDC94"
green = "#008000"
orange = "#FFBE98"
blue = "#1E90FF"

# Defines which radio button is currently selected
radio_encoder_var = customtkinter.IntVar(value=config["encoding_hw"])

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

def compute_bitrate(filename, encoding_hw):
    video = VideoCapture(filename)
    
    # count the number of frames 
    frames = video.get(CAP_PROP_FRAME_COUNT) 
    fps = video.get(CAP_PROP_FPS) 
    
    # calculate duration of the video 
    try: seconds = ceil(frames / fps) 
    except (ZeroDivisionError): return None

    #target_size = MAX_SIZE_MB * 0.9 if encoding_hw == "cpu" else MAX_SIZE_MB * 0.75
    target_size = MAX_SIZE_MB * 0.9

    print("MAXSIZEMB: ", MAX_SIZE_MB)
    print("SECONDS: ", seconds)
    # Computing bitrate
    return floor(target_size * 8388.608 / seconds) - 64

def get_selected_encoding_hw():
    if (radio_encoder_var.get() == config["encoding_hw"]): return config["hw_ffmpeg_codec"]
    if radio_encoder_var.get() == 1: return "cpu"
    if radio_encoder_var.get() == 2: return "hevc_amf"
    if radio_encoder_var.get() == 3: return "hevc_nvenc"
    if radio_encoder_var.get() == 4: return "hevc_qsv"

def ffmpeg_routine(filename, bitrate, filepath, encoding_hw):
    file_format = filename.split('.')[-1]
    ffmpeg_path = "ffmpeg"
    result_filename = filename.replace(f".{file_format}", f"-{encoding_hw}-compressed.{file_format}")

    ffmpeg_args = {
        "cpu": {
            "pass1": [ffmpeg_path, "-y", "-i", filename, "-c:v", "libx265", "-b:v", f"{bitrate}k", "-filter:v", f"fps=30,scale={config["target_resolution"]}", "-x265-params", "pass=1", "-an", "-f", "mp4", "NUL"],
            "pass2": [ffmpeg_path, "-y", "-i", filename, "-c:v", "libx265", "-b:v", f"{bitrate}k", "-filter:v", f"fps=30,scale={config["target_resolution"]}", "-x265-params", "pass=2", "-c:a", "aac", "-b:a", "64k", result_filename]
        },
        "gpu": {
            "pass2": [ffmpeg_path, "-y", "-i", filename, "-c:v", encoding_hw, "-b:v", f"{bitrate}k", "-filter:v", f"fps=30,scale={config["target_resolution"]}", "-c:a", "aac", "-b:a", "64k", result_filename],
        }
    }


    try:
        if (encoding_hw == "cpu"):
            progresslabel.configure(text=texts["first_step_encoding"])
            progresslabel.configure(text_color=yellow)
            if name == 'nt': check_call(ffmpeg_args["cpu"]["pass1"], cwd=filepath, stderr=STDOUT, creationflags=CREATE_NO_WINDOW)
            else: check_call(ffmpeg_args["cpu"]["pass1"], cwd=filepath, stderr=STDOUT)
            progresslabel.configure(text=texts["second_step_encoding"])
            progresslabel.configure(text_color=orange)
            check_call(ffmpeg_args["cpu"]["pass2"], cwd=filepath, stderr=STDOUT)
        else:
            progresslabel.configure(text=texts["second_step_encoding"])
            progresslabel.configure(text_color=orange)
            if name == 'nt': check_call(ffmpeg_args["gpu"]["pass2"], cwd=filepath, stderr=STDOUT, creationflags=CREATE_NO_WINDOW)
            else: check_call(ffmpeg_args["gpu"]["pass2"], cwd=filepath, stderr=STDOUT)
        
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
    encoding_hw = get_selected_encoding_hw()
    bitrate = compute_bitrate(fullpath, encoding_hw)
    print("BITRATE: ", bitrate)
    print("ENCODING_HW: ", encoding_hw)

    #Disabling select button after selecting a file
    change_buttons_status("disabled")

    if (bitrate):
        selectfilebutton.configure(text = fullpath.split("/")[-1])
        ffmpeg_thread = Thread(target=ffmpeg_routine, args=(fullpath, bitrate, folderpath, encoding_hw, ), daemon=True)
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
        if proc.name() == "ffmpeg.exe":
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
selectfilebutton.drop_target_register(DND_ALL)
selectfilebutton.dnd_bind("<<Drop>>", get_dnd_path)
selectfilebutton.grid(row=3, column=0, padx=20, pady=20, sticky="ew", columnspan=4)

progresslabel = customtkinter.CTkLabel(master=app, text="", font=('Helvetica bold', 18))
progresslabel.grid(row=4, column=0, padx=20, pady=20, columnspan=4)

if (len(argv) == 2): select_file_to_compress(argv[1].replace("\\", "/"))

app.protocol("WM_DELETE_WINDOW",  on_close)
app.mainloop()