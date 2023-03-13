import streamlit as st
import sounddevice as sd
import numpy as np
import helpers
from pathlib import Path
import librosa
from matplotlib import pyplot as plt
import soundfile as sf

st.title('Vinyl Recorder')

# Toggle our controls enabled/disabled
if 'stream' not in st.session_state:
    controls_disabled = False
else:
    controls_disabled = st.session_state['stream'].active

# Set the device and sample rate
cols = st.columns(3)
with cols[0]:
    # Set the device
    devices = sd.query_devices()
    sel_dev = st.selectbox('Choose sound device:', options=devices, disabled=controls_disabled,
                           format_func=lambda d: f"{d['name']} ({d['max_input_channels']}ch / {d['default_samplerate']}Hz)")
    sd.default.device = sel_dev['index']

with cols[1]:
    # Set the sample rate
    fs = st.number_input('Sample rate:', min_value=1000, max_value=48000, disabled=controls_disabled,
                         value=int(sel_dev['default_samplerate']), step=1000)
    # fs = st.radio('Sample rate:', options=[44100, 48000], horizontal=True)

with cols[2]:
    n_chan = st.number_input('Channels:', min_value=1, max_value=2, disabled=controls_disabled,
                             value=int(sel_dev['max_input_channels']), step=1)
    # choose the number of channels
    # chan_opts = {2: 'Stereo', 1:'Mono'}
    # n_chan = st.radio('Channels:', options=chan_opts.keys(), format_func=lambda k: chan_opts[k])

# get the file name to save to
file_name = st.text_input('File name to record:', disabled=controls_disabled)
recordings_dir = Path('./recordings/')
recordings_dir.mkdir(parents=True, exist_ok=True)
file_loc = recordings_dir / file_name
if file_loc.exists():
    st.warning(f'{file_name} exists and will be overwritten.')

# get the recording duration
cols = st.columns(2)
with cols[0]:
    mins = st.number_input('Minutes', min_value=0, max_value=60, step=1,
                           disabled=controls_disabled)
with cols[1]:
    secs = st.number_input('Seconds', value=5, min_value=0, max_value=60, step=1,
                           disabled=controls_disabled)
duration = mins*60 + secs
frames = duration * fs

live_prev_cols = st.columns(2)
# enable to disable live previoew
live_prev_enabled = live_prev_cols[0].checkbox('Enable live preview',
                                               value=False, disabled=controls_disabled)

# initialize the stream and store it in the session state
if 'stream' not in st.session_state:
    st.session_state['stream'] = sd.InputStream(samplerate=fs, channels=n_chan,
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
if live_prev_enabled:
    update_interval = live_prev_cols[1].slider('Live Update interval (ms)', min_value=100, max_value=10000,
                                value=250, step=100, disabled=controls_disabled)
    frames_to_read = int(update_interval / 1000.0 * fs)
else:
    # update_interval = 500
    frames_to_read = int(500 / 1000.0 * fs)
    # frames_to_read = stream.blocksize

if 'recorded_data' not in st.session_state:
    st.session_state['recorded_data'] = []
recorded_data = st.session_state['recorded_data']


status_header = st.empty()
if stream.active:
    status_header.header('🔴 Recording...')
    
    # Set up progress bars
    res_cols = st.columns(3)
    res_labs = ['CPU:', 'Mem:', 'HDD:']
    res_indexes = ['cpu','mem','hdd']
    current_res = helpers.get_res_stats()
    res_progs = [c.progress(current_res[res_t], text=lab) for c, res_t, lab in zip(res_cols, res_indexes, res_labs)]

    vu_labels = (['Input'] if n_chan == 1 else ['Left','Right'])
    vumeters = [st.progress(0.0, text=t) for t in vu_labels]

    rec_prog = st.empty()

    downsampled_rec_data = []
    n_frames_rec = 0
    live_preview = st.empty()
    with sf.SoundFile(str(file_loc), 'w', samplerate=fs, channels=n_chan, subtype='PCM_32') as file:
        while n_frames_rec <= frames:
            # Calculate how long to read for (and how long to block for)
            # based on the requested update frequency

            read, overflowed = stream.read(frames_to_read)
            n_frames_rec += frames_to_read
            file.write(read)

            # read = read if n_chan == 2 else read[:, None]
            # print(read.shape)
            # Update vumeters and resource usage statistics
            for ch, vu_label, vu in zip(range(n_chan), vu_labels, vumeters):
                vu.progress(float(read[:,ch].max()), text=vu_label)
            current_res = helpers.get_res_stats()
            for p, idx, lab in zip(res_progs, res_indexes, res_labs):
                p.progress(current_res[idx], text=lab)
            rec_prog_val = (float(n_frames_rec) / frames) if n_frames_rec <= frames else 1.0
            rec_prog.progress(rec_prog_val, 
                            text=f'Recorded {n_frames_rec/fs:.2f}s of {duration:.2f}s')

            if live_prev_enabled:
                # Aggressively downsample the recorded data and display the live preview
                downsampled_rec_data.append(read)
                print(len(downsampled_rec_data))
                drd = np.vstack(downsampled_rec_data).flatten()
                print(drd.shape)
                f = plt.figure()
                librosa.display.waveshow(drd, sr=fs)
                live_preview.pyplot(f)
                plt.close()

            if overflowed:
                pass
                # raise Exception('Buffer overflow!')

        stream.stop()
        status_header.header('✅ Recording Complete!')


else:
    status_header.header('⬛ Ready to Record')
    if len(recorded_data):
        recorded_data = np.vstack(recorded_data)
        st.line_chart(recorded_data[:,0])

