import streamlit as st
import sounddevice as sd
from matplotlib import pyplot as plt
import time
import psutil
import shutil
import numpy as np
import sys
import queue 
import scipy

st.title('Vinyl Recorder')

cols = st.columns(2)
with cols[0]:
    # Set the device
    devices = sd.query_devices()
    sel_dev = st.selectbox('Choose sound device:', options=devices, format_func=lambda d: f"{d['name']} ({d['max_input_channels']}ch / {d['default_samplerate']}Hz)")
    sd.default.device = sel_dev['index']

with cols[1]:
    # Set the sample rate
    fs = st.radio('Sample rate:', options=[44100, 48000], horizontal=True)

cols = st.columns(2)
with cols[0]:
    mins = st.number_input('Minutes', min_value=0, max_value=60, step=1)
with cols[1]:
    secs = st.number_input('Seconds', value=5, min_value=0, max_value=60, step=1)

duration = mins*60 + secs

def get_res_stats():
    hdd = shutil.disk_usage('.')
    return {
        'mem': int(psutil.virtual_memory().percent),
        'cpu': int(psutil.cpu_percent()),
        'hdd': int(float(hdd.used) / hdd.free * 100)
    }

q = queue.Queue()
def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())
    # print('qlen', q.qsize())

res_cols = st.columns(3)
res_labs = ['CPU:', 'Mem:', 'HDD:']
res_indexes = ['cpu','mem','hdd']
current_res = get_res_stats()
res_progs = [c.progress(current_res[res_t], text=lab) for c, res_t, lab in zip(res_cols, res_indexes, res_labs)]
vol_prog_left = st.progress(0.0, text='Left')
vol_prog_right = st.progress(0.0, text='Right')

record_btn = st.button('Record')
stop_btn = st.button('Stop')

wave_box = st.empty()

if 'stream' not in st.session_state:
    st.session_state['stream'] = sd.InputStream(samplerate=fs, channels=2, callback=callback)

# def record_clicked():
#     st.session_state['stream'].start()

# def stop_clicked():
#     print('stopping stream')
#     st.session_state['stream'].stop()

if record_btn:
    st.session_state['stream'].start()
elif stop_btn:
    st.session_state['stream'].stop()

if st.session_state['stream'].active:
    print('active stream')
    st.write('active stream')
    current_waveform = []
    while True:
        sound_data = [np.zeros((0,2))] # empty to start
        while not q.empty():
            # pull out packets of sound from the queue being put there by the callback
            sound_data.append(q.get())
        sound_data = np.vstack(sound_data) # concatenate all packets into one sample
        current_waveform.append(sound_data) # store for current waveform

        # do nothing if we happened to get no data this round
        if sound_data.shape[0] == 0: continue 

        # otherwise, update the vumeters
        vol_prog_left.progress(sound_data[:,0].max(), text='Left')
        vol_prog_right.progress(sound_data[:,1].max(), text='Right')
else:
    print('inactive stream')
    st.write('inactive stream')

# if record_clicked:
#     channels = 2 # stereo
#     sleep_interval = 200 # ms
#     wave_interval = 1000 # ms
#     with sd.InputStream(samplerate=fs,
#                         channels=channels, callback=callback) as stream:
        
#         stop_clicked = record_or_stop.button('⬛ Stop', on_click=stop_stream())
#         current_waveform = []
#         while True:
#             if stop_clicked: 
#                 print('stop clicked')
#                 break # all done recording, will jump out of context and close stream

#             sound_data = [np.zeros((0,2))] # empty to start
#             while not q.empty():
#                 # pull out packets of sound from the queue being put there by the callback
#                 sound_data.append(q.get())
#             sound_data = np.vstack(sound_data) # concatenate all packets into one sample
#             current_waveform.append(sound_data) # store for current waveform

#             # do nothing if we happened to get no data this round
#             if sound_data.shape[0] == 0: continue 

#             # otherwise, update the vumeters
#             vol_prog_left.progress(sound_data[:,0].max(), text='Left')
#             vol_prog_right.progress(sound_data[:,1].max(), text='Right')

#             # check to see if it's time to display another waveform
#             if len(current_waveform) >= (wave_interval / sleep_interval):
#                 if show_wave:
#                     current_waveform = np.vstack(current_waveform)[:,0]
#                     # downsample to prevent freezing browser
#                     current_waveform = scipy.signal.decimate(current_waveform, q=10)
#                     current_waveform = scipy.signal.decimate(current_waveform, q=10)
#                     wave_box.line_chart(current_waveform)
#                 current_waveform = []

#             # current_res = get_res_stats()
#             # for p, idx, lab in zip(res_progs, res_indexes, res_labs):
#             #     p.progress(current_res[idx], text=lab)

#             sd.sleep(sleep_interval)
            
# # '''
# #     rec = sd.rec(int(duration * fs), samplerate=fs, channels=channels)
# #     prog = st.progress(0.0, text='Recording')
# #     with st.empty():
# #         for i in range(duration):
# #             prog.progress((i+1)/float(duration))
# #             current_res = get_res_stats()
# #             for p, idx, lab in zip(res_progs, res_indexes, res_labs):
# #                 p.progress(current_res[idx], text=lab)
            
# #             f = plt.figure()
# #             plt.plot(rec[:,0])
# #             st.pyplot(f)
# #             plt.close()

# #             time.sleep(1.0)
# #     sd.wait()

# #     f = plt.figure()
# #     plt.plot(rec[:,0])
# #     st.pyplot(f)

# #     st.audio(rec.T, sample_rate=fs)

# # '''