import streamlit as st
import sounddevice as sd
from matplotlib import pyplot as plt
import time

st.write('Hello world!')
st.write(sd.query_devices())
sd.default.device = 'pulse'
st.write(sd.query_devices())

clicked = st.button('Click me to record audio')
if clicked:
    duration = 5 # seconds
    fs = 44100 # Hz
    channels = 2 # stereo
    rec = sd.rec(int(duration * fs), samplerate=fs, channels=channels)
    prog = st.progress(0.0, text='Recording')
    for i in range(duration):
        prog.progress((i+1)/float(duration))
        time.sleep(1.0)
    sd.wait()

    f = plt.figure()
    plt.plot(rec[:,0])
    st.pyplot(f)

    st.audio(rec.T, sample_rate=fs)