import streamlit as st
import sounddevice as sd
import numpy as np
import helpers
import scipy
import librosa
from matplotlib import pyplot as plt

st.title('Vinyl Recorder')

# Set the device and sample rate
cols = st.columns(2)
with cols[0]:
    # Set the device
    devices = sd.query_devices()
    sel_dev = st.selectbox('Choose sound device:', options=devices, format_func=lambda d: f"{d['name']} ({d['max_input_channels']}ch / {d['default_samplerate']}Hz)")
    sd.default.device = sel_dev['index']

with cols[1]:
    # Set the sample rate
    fs = st.radio('Sample rate:', options=[44100, 48000], horizontal=True)

# get the recording duration
cols = st.columns(2)
with cols[0]:
    mins = st.number_input('Minutes', min_value=0, max_value=60, step=1)
with cols[1]:
    secs = st.number_input('Seconds', value=5, min_value=0, max_value=60, step=1)
duration = mins*60 + secs

# initialize the stream and store it in the session state
if 'stream' not in st.session_state:
    st.session_state['stream'] = sd.InputStream(samplerate=fs, channels=2,
                                                dtype='float32') 

# get our global stream
stream = st.session_state['stream']

# make our buttons
def record_callback():
    st.session_state['recorded_data'] = []
    stream.start()

def stop_callback():
    stream.stop()
control_cols = st.columns([2,2,6])
record_clicked = control_cols[0].button('🔴 Record', key='btn_rec',
                                        on_click=record_callback)
stop_clicked = control_cols[1].button('⬛ Stop', key='btn_stop', 
                                      on_click=stop_callback)

update_interval = st.slider('Update interval (ms)', min_value=100, max_value=10000,
                            value=250, step=100)

if 'recorded_data' not in st.session_state:
    st.session_state['recorded_data'] = []
recorded_data = st.session_state['recorded_data']


if stream.active:
    st.header('🔴 Recording...')
    
    # Set up progress bars
    res_cols = st.columns(3)
    res_labs = ['CPU:', 'Mem:', 'HDD:']
    res_indexes = ['cpu','mem','hdd']
    current_res = helpers.get_res_stats()
    res_progs = [c.progress(current_res[res_t], text=lab) for c, res_t, lab in zip(res_cols, res_indexes, res_labs)]

    vumeter_left = st.progress(0.0, text='Left')
    vumeter_right = st.progress(0.0, text='Right')

    downsampled_rec_data = []
    live_preview = st.empty()
    while True:
        # Calculate how long to read for (and how long to block for)
        # based on the requested update frequency
        frames_to_read = int(update_interval / 1000.0 * fs)
        
        read, overflowed = stream.read(frames_to_read)

        # Update vumeters and resource usage statistics
        vumeter_left.progress(float(read[:,0].max()), text='Left')
        vumeter_right.progress(float(read[:,1].max()), text='Right')
        current_res = helpers.get_res_stats()
        for p, idx, lab in zip(res_progs, res_indexes, res_labs):
            p.progress(current_res[idx], text=lab)

        # Aggressively downsample the recorded data and display the live preview
        downsampled_rec_data.append(read[:,0])

        f = plt.figure()
        librosa.display.waveshow(np.vstack(downsampled_rec_data), sr=fs)
        live_preview.pyplot(f)
        plt.close()

        # amp_env = amp_env[::100]
        # for i in range(3):
        #    to_dec = scipy.signal.decimate(to_dec, q=10)


        if overflowed:
            print('Overflow')
            # raise Exception('Buffer overflow!')
        

else:
    st.header('⬛ Not Recording')
    if len(recorded_data):
        recorded_data = np.vstack(recorded_data)
        st.line_chart(recorded_data[:,0])

