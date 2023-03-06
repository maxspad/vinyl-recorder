import streamlit as st
import sounddevice as sd
from matplotlib import pyplot as plt
import time
import psutil
import shutil
import numpy as np
import sys
import queue 

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
record_or_stop = st.empty()  

wave_box = st.empty()

record_clicked = record_or_stop.button('🔴 Record')

if record_clicked:
    channels = 2 # stereo
    stop_clicked = record_or_stop.button('⬛ Stop')
    with sd.InputStream(samplerate=fs,
                        channels=channels, callback=callback):
        while True:
            if stop_clicked: 
                break
            sound_data = [np.zeros((0,2))]
            while not q.empty():
                sound_data.append(q.get())
            sound_data = np.vstack(sound_data)
            if sound_data.shape[0] > 0:
                vol_prog_left.progress(sound_data[:,0].max(), text='Left')
                vol_prog_right.progress(sound_data[:,1].max(), text='Right')
                wave_box.line_chart(sound_data[:,0]) # TODO make this update less frequently

            current_res = get_res_stats()
            for p, idx, lab in zip(res_progs, res_indexes, res_labs):
                p.progress(current_res[idx], text=lab)

            sd.sleep(100)
'''
    rec = sd.rec(int(duration * fs), samplerate=fs, channels=channels)
    prog = st.progress(0.0, text='Recording')
    with st.empty():
        for i in range(duration):
            prog.progress((i+1)/float(duration))
            current_res = get_res_stats()
            for p, idx, lab in zip(res_progs, res_indexes, res_labs):
                p.progress(current_res[idx], text=lab)
            
            f = plt.figure()
            plt.plot(rec[:,0])
            st.pyplot(f)
            plt.close()

            time.sleep(1.0)
    sd.wait()

    f = plt.figure()
    plt.plot(rec[:,0])
    st.pyplot(f)

    st.audio(rec.T, sample_rate=fs)

'''