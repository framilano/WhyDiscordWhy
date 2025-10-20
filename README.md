# WhyDiscordWhy
### A video compressor that generates video clips compatible with Discord non-nitro plan (current limit 10MB)

![image](https://github.com/user-attachments/assets/32147eed-3643-4180-9c92-b6d60fdcdaf0)

## How does it work?
- Tries its best using ffmpeg HEVC/X265 encoders to reduce video file size to less than 10MB. 
- Uses [ffmpeg 2-pass encoding](https://trac.ffmpeg.org/wiki/Encode/H.265#Two-PassEncoding) procedure to reach the required size.
- Supports GPU encoding with AMD/NVIDIA/INTEL GPUs, these encoders don't support 2-pass encoding, so the generated file size could be bigger than 10MB. Of course GPU encoding is way faster in most cases.


## How to use
https://github.com/user-attachments/assets/043ffb47-97ac-41b8-a21e-4ad11fa2cc59

*You can even Drag-n-Drop files directly on top of the program to start the compression*

**Linux build only supports AMD VAAPI for HW Acceleration and CPU encoding currently, Windows works with all profiles**

## Config
You can define different encoders or targets size editing `config.json`:
```json
{
    "encoding_choice": 2,
    "target_size_mb": "10",
    "target_resolution": "1280:720",
    "target_audio_bitrate": "32",
    "target_audio_codec": "libopus",
    "target_fps": "30",
}
```
* `encoding_choice`, forces CPU software encoding, `2` uses AMD HW encoding, `3` is for NVIDIA and `4` is for Intel
* `target_size_mb`, changes target compressed file size, default is 10MB
* `target_resolution`, changes output file resolution
* `target_audio_bitrate`, changes output file audio bitrate, default is 32
* `target_audio_codec`, changes output file audio codec, default is libopus
* `target_fps`, changes output file frame rate


## Themes
You can edit every single aspect of the GUI color palette editing per profile. You can edit them modifying all the `profile-theme.json` files near the executable.

More info regarding theme editing are available [here](https://github.com/TomSchimansky/CustomTkinter/wiki/Themes)

## Testing
On Linux you need tk installed to run this script
```
sudo pacman -Sy --needed tk
```