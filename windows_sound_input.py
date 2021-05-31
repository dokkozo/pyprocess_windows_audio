#!/usr/bin/env python3

# this program only work with custom built pyaudio https://github.com/intxcc/pyaudio_portaudio/releases that is compatible only with python 3.7
# specify dummy output device as Windows audio output.

import pyaudio
import numpy as np

DUMMY_DEV_NAME = "3-4 (QUAD-CAPTURE)"
RATE = 48000
CHUNK = 256
CHANNEL_IN = 2
CHANNEL_OUT = 2
Previous_gain = 1

def signal_proc_buff(input_buff, Previous_gain=1):
    dtype=np.int16
    # Convert framebuffer into nd-array
    input_data = np.fromstring(input_buff, dtype=dtype).reshape(CHUNK, CHANNEL_IN)
    
    # Signal processing
    # Set output as L-ch
    output_data = np.zeros((CHUNK, CHANNEL_OUT))
    
    output_data, Target_gain = signal_proc(input_data, Previous_gain)

    # Convert nd-array into framebuffer
    output_buff = output_data.astype(dtype).tostring()
    return output_buff, Target_gain

def signal_proc(input_audio, Previous_gain):
    # input_audio: ndarray (len, ch)
    # output_audio: ndarray (len, ch)
    thres = 0.02
    makeup = 5
    transition = 64

    # normalize (to calc rms)
    input_audio_float = input_audio/(2**16/2)
    
    rms = np.sqrt(np.sum(input_audio_float ** 2) / len(input_audio_float.reshape(-1)))

    Target_gain = makeup * thres / max(thres, rms)
    if max(thres, rms) > thres:
        print(f"compress: {20 * np.log10(max(thres, rms)/thres):.02f} dB")

    # to prevent discoutinuous of audio, linearly interporate gain from previous gain to target gain
    gain = np.hstack([np.linspace(Previous_gain, Target_gain, transition), np.ones(CHUNK - transition)*Target_gain])[:,None]

    output_audio = gain * input_audio
    return output_audio, Target_gain

# get wasapi device
useloopback = False
p = pyaudio.PyAudio()
for i_api in range(p.get_host_api_count()):
    if 'Windows WASAPI' in p.get_host_api_info_by_index(i_api).get('name'): # use WASAPI
        InputDeviceID = p.get_host_api_info_by_index(i_api).get('defaultInputDevice') # use WASAPI default input 
        OutputDeviceID = p.get_host_api_info_by_index(i_api).get('defaultOutputDevice') # use WASAPI default output

        for i_dev in range(p.get_host_api_info_by_index(i_api)["deviceCount"]): # use DUMMY_DEV_NAME output device as virtual output

            dev_info = p.get_device_info_by_host_api_device_index(host_api_device_index= i_dev, host_api_index = i_api)
            print(dev_info["name"])
            if dev_info["name"] == DUMMY_DEV_NAME and dev_info["maxOutputChannels"] > 0:
                dummyOutputDeviceID = dev_info["index"]
                break
        else:
            raise RuntimeError("Cannot find dummy device")        
        
        useloopback = True
        break
else:
    raise RuntimeError("not wasapi device")

input_device_info = p.get_device_info_by_index(InputDeviceID)
output_device_info = p.get_device_info_by_index(OutputDeviceID)
dummy_output_device_info = p.get_device_info_by_index(dummyOutputDeviceID)

stream_in = p.open( 
        format=pyaudio.paInt16,
        channels=CHANNEL_IN,
        rate = RATE,
        frames_per_buffer=CHUNK,
        input_device_index=input_device_info["index"],
        input = True,
        output = False,
    )

stream_virtualout = p.open(    
        format=pyaudio.paInt16,
        channels=CHANNEL_OUT,
        rate=RATE,
        frames_per_buffer=CHUNK,
        input_device_index=dummy_output_device_info["index"], # use output device as input device with as_loopback=True
        input=True,
        as_loopback = useloopback,  
    )

stream_out = p.open(    
        format=pyaudio.paInt16,
        channels=CHANNEL_OUT,
        rate=RATE,
        frames_per_buffer=CHUNK,
        output_device_index=output_device_info["index"],
        input=False,
        output=True,
    )

while stream_in.is_active() and stream_out.is_active() and stream_virtualout.is_active():
    input_buff = stream_virtualout.read(CHUNK)
    output_buff, Target_gain = signal_proc_buff(input_buff, Previous_gain)
    Previous_gain = Target_gain
    stream_out.write(output_buff)

    
stream_in.stop_stream()
stream_in.close() 
stream_out.stop_stream()
stream_out.close()
p.terminate()