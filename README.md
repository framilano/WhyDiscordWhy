# WhyDiscordWhy
### A video compressor that generates video clips compatible with Discord non-nitro plan (current limit 10MB)

![image](https://github.com/user-attachments/assets/32147eed-3643-4180-9c92-b6d60fdcdaf0)

## How does it work?
- Tries its best using ffmpeg HEVC/X265 encoders to reduce video file size to less than 10MB. 
- Uses [ffmpeg 2-pass encoding](https://trac.ffmpeg.org/wiki/Encode/H.265#Two-PassEncoding) procedure to reach the required size.
- Supports GPU encoding with AMD/NVIDIA/INTEL GPUs, these encoders don't support 2-pass encoding, so the generated file size could be bigger than 10MB. Of course GPU encoding is way faster in most cases.


## How do you use it?
https://github.com/user-attachments/assets/043ffb47-97ac-41b8-a21e-4ad11fa2cc59

