# WhyDiscordWhy
### A video compressor that generates video clips compatible with Discord non-nitro plan (current limit 10MB)

![image](https://github.com/user-attachments/assets/32147eed-3643-4180-9c92-b6d60fdcdaf0)

## How does it work?
- Tries its best using ffmpeg HEVC/X265 encoders to reduce video file size to less than 10MB. 
- Uses [ffmpeg 2-pass encoding](https://trac.ffmpeg.org/wiki/Encode/H.265#Two-PassEncoding) procedure to reach the required size.
- Supports GPU encoding with AMD/NVIDIA/INTEL GPUs, these encoders don't support 2-pass encoding, so the generated file size could be bigger than 10MB. Of course GPU encoding is way faster in most cases.


## How do you use it?
https://github.com/user-attachments/assets/043ffb47-97ac-41b8-a21e-4ad11fa2cc59

## Args
You can define different encoders as command line arguments, check ffmpeg docs to see which codecs are available:
- `--amd-codec h264_amf` to use AMD X264 as encoder
- `--nvidia-codec h264_nvenc` to use Nvidia X264 as encoder
- `--intel-codec h264_qsv` to use Intel X264 as encoder

Or just the default hevc ones, you don't have to specify any cli arg for this
