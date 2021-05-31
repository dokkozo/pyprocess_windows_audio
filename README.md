# Process windows desktop audio
This tool processes stream from an output device and write to another output device by utilizing loopback mode of Windows WASAPI.
Especially, this imprementation includes compression of audio, that makes volume uniform by compressing only loud sound and do nothing for small sound.

## Requirements
- Windows Vista and above (for utilizing WASAPI). But only checked with Windows10
- python=3.7
- custom build pyaudio available at https://github.com/intxcc/pyaudio_portaudio/releases
    - This is required to use "as_loopback" option to get output stream as input.
    - direct download from: https://github.com/intxcc/pyaudio_portaudio/releases/download/1.1.1/PyAudio-0.2.11-cp37-cp37m-win_amd64.whl

## How to use
- setup environment
    - setup python37 for Windows
    - `$ pip install PyAudio-0.2.11-cp37-cp37m-win_amd64.whl`
- set `DUMMY_DEV_NAME` in `windows_sound_input.py`
    - The list of device names is available by executing `windows_sound_input.py` with `DUMMY_DEV_NAME = ""`
- specify audio output device of some application (ex. zoom) as you set for `DUMMY_DEV_NAME`

## limitation
- An audio device for "output" and "virtual output" must be different.
    - output: The device from which you actually listen to sound
    - virtual output: The device into which the application outputs audio.
        - The audio given to the "virtual output" (from some application or windows) is processed and then given to the "output" device.