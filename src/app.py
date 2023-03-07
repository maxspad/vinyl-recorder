import streamlit as st
import sounddevice as sd
import numpy as np
import queue
import sys

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

# stream callback that runs on a different thread
q = queue.Queue()
def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(indata.copy())
    # print('qlen', q.qsize())

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
st.write(f"Current stream status: {'active' if stream.active else 'inactive'}")

if 'recorded_data' not in st.session_state:
    st.session_state['recorded_data'] = []
recorded_data = st.session_state['recorded_data']

if stream.active:
    st.header('🔴 Recording...')
    mean_placeholder = st.empty()
    while True:
        avail_frames = stream.read_available
        frames_to_read = int(update_interval / 1000.0 * fs)
        print(frames_to_read)
        read, overflowed = stream.read(frames_to_read)
        mean_placeholder.write(f'{np.mean(read)}, frames: {avail_frames}')
        if overflowed:
            raise Exception('Overflowed!')
        recorded_data.append(read)
        # sd.sleep(update_interval)

else:
    st.header('⬛ Not Recording')
    if len(recorded_data):
        recorded_data = np.vstack(recorded_data)
        st.line_chart(recorded_data[:,0])

