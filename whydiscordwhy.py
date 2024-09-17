import customtkinter
from math import floor, ceil
from cv2 import CAP_PROP_FRAME_COUNT, CAP_PROP_FPS, VideoCapture
from subprocess import CalledProcessError, STDOUT, check_call, CREATE_NO_WINDOW
from threading import Thread
from os import path, remove
from psutil import process_iter

customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

app = customtkinter.CTk()
app.geometry("670x300")
app.title("Why Discord, why?")
app.resizable(False, False)

MAX_SIZE_MB = 10

red = "#FF8A8A"
yellow = "#FCDC94"
green = "#A5DD9B"
orange = "#FFBE98"
blue = "#2463aa"

# Defines which radio button is currently selected
radio_encoder_var = customtkinter.IntVar(value=1)

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

    target_size = MAX_SIZE_MB * 0.9 if encoding_hw == "cpu" else MAX_SIZE_MB * 0.75

    print("MAXSIZEMB: ", MAX_SIZE_MB)
    print("SECONDS: ", seconds)
    # Computing bitrate
    return floor(target_size * 8388.608 / seconds) - 64

def get_selected_encoding_hw():
    if radio_encoder_var.get() == 1: return "cpu"
    if radio_encoder_var.get() == 2: return "amd_hevc"
    if radio_encoder_var.get() == 3: return "nvidia_hevc"
    if radio_encoder_var.get() == 4: return "intel_hevc"

def ffmpeg_routine(filename, bitrate, filepath, encoding_hw):
    ffmpeg_path = path.dirname(__file__) + "/ffmpeg/ffmpeg"
    result_filename = filename.replace(".mp4", f"-{encoding_hw}-compressed.mp4")

    ffmpeg_args = {
        "cpu": {
            "pass1": [ffmpeg_path, "-y", "-i", filename, "-c:v", "libx265", "-b:v", f"{bitrate}k", "-filter:v", "fps=30,scale=1280:720", "-x265-params", "pass=1", "-an", "-f", "mp4", "NUL"],
            "pass2": [ffmpeg_path, "-y", "-i", filename, "-c:v", "libx265", "-b:v", f"{bitrate}k", "-filter:v", "fps=30,scale=1280:720", "-x265-params", "pass=2", "-c:a", "aac", "-b:a", "64k", result_filename]
        },
        "amd_hevc": {
            "pass2": [ffmpeg_path, "-y", "-i", filename, "-c:v", "hevc_amf", "-b:v", f"{bitrate}k", "-filter:v", "fps=30,scale=1280:720", "-c:a", "aac", "-b:a", "64k", result_filename],
        },
        "nvidia_hevc": {
            "pass2": [ffmpeg_path, "-y", "-i", filename, "-c:v", "hevc_nvenc", "-b:v", f"{bitrate}k", "-filter:v", "fps=30,scale=1280:720", "-c:a", "aac", "-b:a", "64k", result_filename],
        },
        "intel_hevc": {
            "pass2": [ffmpeg_path, "-y", "-i", filename, "-c:v", "hevc_qsv", "-b:v", f"{bitrate}k", "-filter:v", "fps=30,scale=1280:720", "-c:a", "aac", "-b:a", "64k", result_filename],
        }
    }


    try:
        change_buttons_status("disabled")
        if (encoding_hw == "cpu"):
            progresslabel.configure(text="Generating video info 🕒")
            progresslabel.configure(text_color=yellow)
            check_call(ffmpeg_args[encoding_hw]["pass1"], cwd=filepath, stderr=STDOUT, creationflags=CREATE_NO_WINDOW)
        
        progresslabel.configure(text="Encoding compressed video 🎞️")
        progresslabel.configure(text_color=orange)
        check_call(ffmpeg_args[encoding_hw]["pass2"], cwd=filepath, stderr=STDOUT, creationflags=CREATE_NO_WINDOW)
        
        progresslabel.configure(text="Encoding completed 💯")
        progresslabel.configure(text_color=green)
    except(CalledProcessError):
        progresslabel.configure(text="Error during video encoding ❌")
        progresslabel.configure(text_color=red)

        if path.isfile(result_filename): remove(result_filename)
    except(FileNotFoundError):
        progresslabel.configure(text="Couldn't find ffmpeg ❌")
        progresslabel.configure(text_color=red)
    
    change_buttons_status("normal")
    selectfilebutton.configure(text = "Select clip to compress")

    #Cleaning...
    if path.isfile(filepath + "/x265_2pass.log"): remove(filepath + "/x265_2pass.log")
    if path.isfile(filepath + "/x265_2pass.log.cutree"): remove(filepath + "/x265_2pass.log.cutree")
    if path.isfile(filepath + "/x265_2pass.log.temp"): remove(filepath + "/x265_2pass.log.temp")
    if path.isfile(filepath + "/x265_2pass.log.cutree.temp"): remove(filepath + "/x265_2pass.log.cutree.temp")
    if path.isfile(filepath + "/ffmpeg2pass-0.log"): remove(filepath + "/ffmpeg2pass-0.log")

def selectfile():
    filename = customtkinter.filedialog.askopenfilename()
    filepath = "/".join(filename.split("/")[0:-1])
    encoding_hw = get_selected_encoding_hw()
    bitrate = compute_bitrate(filename, encoding_hw)
    print("BITRATE: ", bitrate)
    print("ENCODING_HW: ", encoding_hw)

    if (bitrate):
        selectfilebutton.configure(text = filename.split("/")[-1])
        ffmpeg_thread = Thread(target=ffmpeg_routine, args=(filename, bitrate, filepath, encoding_hw, ), daemon=True)
        ffmpeg_thread.start()
    else:
        progresslabel.configure(text = "Doesn't look like a video file to me ⁴⁰⁴")
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

title_label = customtkinter.CTkLabel(master=app, text="Why Discord, why?", font=('Helvetica bold', 32), text_color=blue)
title_label.grid(row=0, column=0, padx=20, pady=20, columnspan=4)

radiobutton_1 = customtkinter.CTkRadioButton(master=app, text="CPU (default)", variable=radio_encoder_var, value=1)
radiobutton_1.grid(row=1, column=0)
radiobutton_2 = customtkinter.CTkRadioButton(master=app, text="AMD (GPU)", variable=radio_encoder_var, value=2, text_color=red)
radiobutton_2.grid(row=1, column=1)
radiobutton_3 = customtkinter.CTkRadioButton(master=app, text="Nvidia (GPU)", variable=radio_encoder_var, value=3, text_color=green)
radiobutton_3.grid(row=1, column=2)
radiobutton_4 = customtkinter.CTkRadioButton(master=app, text="Intel (GPU)", variable=radio_encoder_var, value=4, text_color=blue)
radiobutton_4.grid(row=1, column=3)

warninglabel = customtkinter.CTkLabel(master=app, text="CPU is slower but more precise, GPU is way faster, but could generate results bigger than target size", font=('Helvetica bold', 14), text_color=blue)
warninglabel.grid(row=2, column=0, padx=20, pady=20, columnspan=4)

selectfilebutton = customtkinter.CTkButton(master=app, text="Select clip to compress", command=selectfile, font=('Helvetica bold', 18))
selectfilebutton.grid(row=3, column=0, padx=20, pady=20, sticky="ew", columnspan=4)

progresslabel = customtkinter.CTkLabel(master=app, text="", font=('Helvetica bold', 18))
progresslabel.grid(row=4, column=0, padx=20, pady=20, columnspan=4)


app.protocol("WM_DELETE_WINDOW",  on_close)
app.mainloop()