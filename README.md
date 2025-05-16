# WhyDiscordWhy
### A video compressor that generates video clips compatible with Discord non-nitro plan (current limit 10MB)

![image](https://github.com/user-attachments/assets/32147eed-3643-4180-9c92-b6d60fdcdaf0)

## How does it work?
- Tries its best using ffmpeg HEVC/X265 encoders to reduce video file size to less than 10MB. 
- Uses [ffmpeg 2-pass encoding](https://trac.ffmpeg.org/wiki/Encode/H.265#Two-PassEncoding) procedure to reach the required size.
- Supports GPU encoding with AMD/NVIDIA/INTEL GPUs, these encoders don't support 2-pass encoding, so the generated file size could be bigger than 10MB. Of course GPU encoding is way faster in most cases.


## How to use
https://github.com/user-attachments/assets/043ffb47-97ac-41b8-a21e-4ad11fa2cc59

## Config
You can define different encoders or targets size editing `config.json`:
```json
{
    "target_size_mb": 10,
    "encoding_hw": 1,
    "hw_ffmpeg_codec": "libx265",
    "theme_file_name": "theme.json"
}
```
* `target_size_mb`, changes target compressed file size, default is 10MB
* `encoding_hw`, `1` forces CPU software encoding, `2` uses AMD HW encoding, `3` is for NVIDIA and `4` is for Intel
* `hw_ffmpeg_codec`, by default the selected codec is HEVC, but can you choose AV1 or H264 too (for AV1 with AMD just use `av1_amf`). Check ffmpeg docs to select the best codec for your system
* `theme_file_name`, you can select other theme files for this program, check the Themes section


## Themes
You can edit every single aspect of the GUI color palette editing `theme.json` (or creating new files and selecting them using the config entry `theme_file_name`).

More info regarding theme editing are available [here](https://github.com/TomSchimansky/CustomTkinter/wiki/Themes)

## Testing
On Linux you need tk installed
```
sudo pacman -Sy --needed tk
```