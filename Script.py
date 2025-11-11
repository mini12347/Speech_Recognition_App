import streamlit as st
import speech_recognition as sr
import pyaudio
import wave
import os
import requests
import tempfile
import json

def record_audio_pyaudio(filename="recorded.wav", record_seconds=5, rate=44100, chunk=1024):
    try:
        st.info(f"Recording for {record_seconds} seconds using PyAudio...")
        audio_format = pyaudio.paInt16
        channels = 1
        p = pyaudio.PyAudio()
        stream = p.open(format=audio_format,
                        channels=channels,
                        rate=rate,
                        input=True,
                        frames_per_buffer=chunk)
        frames = []

        for i in range(0, int(rate / chunk * record_seconds)):
            data = stream.read(chunk)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(audio_format))
            wf.setframerate(rate)
            wf.writeframes(b''.join(frames))

        st.success(f"Recording saved as {filename}")
        return filename
    except Exception as e:
        st.error(f"Error recording audio: {e}")
        return None

def transcribe_with_deepgram(audio_file_path, api_key, language="en-US"):
    try:
        url = "https://api.deepgram.com/v1/listen"

        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "audio/wav"
        }

        params = {
            "model": "nova-2",
            "language": language,
            "smart_format": "true",
            "punctuate": "true",
            "diarize": "false"
        }

        with open(audio_file_path, 'rb') as audio_file:
            audio_data = audio_file.read()

        response = requests.post(
            url, 
            headers=headers, 
            params=params, 
            data=audio_data, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            # Extract transcript from response
            transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
            return transcript.strip()
        else:
            error_msg = f"Deepgram API Error {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f": {error_detail.get('err_code', 'Unknown error')}"
            except:
                error_msg += f": {response.text}"
            return error_msg
            
    except Exception as e:
        return f"Deepgram transcription error: {str(e)}"

def transcribe_audio_data_deepgram(audio_data, api_key, language="en-US"):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_audio.write(audio_data.get_wav_data())
            temp_audio_path = temp_audio.name
        
        result = transcribe_with_deepgram(temp_audio_path, api_key, language)
        os.unlink(temp_audio_path)
        
        return result
        
    except Exception as e:
        return f"Deepgram transcription error: {str(e)}"

def transcribe_with_google(audio_file, language="en-US"):
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language=language)
            return text
    except sr.UnknownValueError:
        return "Google could not understand audio."
    except sr.RequestError as e:
        return f"Google service error: {e}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    st.title("🎙️ Speech Recognition App")
    
    st.sidebar.header("🔑 API Configuration")
    
    api_key = st.sidebar.text_input(
        "Deepgram API Key (optional):", 
        type="password",
        placeholder="Enter key starting with dg_...",
        help="Get free API key from https://deepgram.com/"
    )
    
    if api_key:
        if api_key.startswith("dg_"):
            st.sidebar.success("✅ Deepgram API key entered")
        else:
            st.sidebar.warning("⚠️ Deepgram keys usually start with 'dg_'")
    else:
        st.sidebar.info("ℹ️ Using Google Speech Recognition (free)")
    
    if api_key and st.sidebar.button("Test Deepgram Connection"):
        with st.sidebar:
            with st.spinner("Testing connection..."):
                # Create a minimal silent WAV file for testing
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    with wave.open(temp_file.name, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(16000)
                        wf.writeframes(b'\x00' * 32000) 
                    
                    result = transcribe_with_deepgram(temp_file.name, api_key)
                    os.unlink(temp_file.name)
                    
                    if "API Error" in result:
                        st.error(f"❌ Connection failed: {result}")
                    elif "transcription error" in result:
                        st.error(f"❌ Error: {result}")
                    else:
                        st.success("✅ Deepgram connection successful!")

  
    st.header("🎤 Speech Recognition")
    
    if api_key:
        api_choice = st.radio(
            "Choose recognition method:",
            ["Google Speech Recognition", "Deepgram", "Record First (PyAudio)"],
            horizontal=True
        )
    else:
        api_choice = st.radio(
            "Choose recognition method:",
            ["Google Speech Recognition", "Record First (PyAudio)"],
            horizontal=True
        )
        st.info("💡 Get a free Deepgram API key from https://deepgram.com/ for better accuracy")
    
    language = st.selectbox(
        "Select language:", 
        ["en-US", "fr-FR", "es-ES", "de-DE", "ar-SA", "hi-IN", "ja-JP", "ko-KR", "zh-CN"]
    )
    
    record_seconds = st.slider("Recording duration (seconds)", 3, 15, 5)

    if "transcription" not in st.session_state:
        st.session_state.transcription = ""

    if st.button("🎤 Start Recording", type="primary", use_container_width=True):
        r = sr.Recognizer()
        text = ""
        
        try:
            if api_choice == "Record First (PyAudio)":
                audio_file = record_audio_pyaudio(record_seconds=record_seconds)
                if audio_file:
                    if api_key:
                        trans_method = st.radio(
                            "Transcribe with:",
                            ["Google", "Deepgram"],
                            horizontal=True,
                            key="post_record"
                        )
                        if trans_method == "Google":
                            text = transcribe_with_google(audio_file, language)
                        else:
                            text = transcribe_with_deepgram(audio_file, api_key, language)
                    else:
                        text = transcribe_with_google(audio_file, language)
                    
                   
                    if os.path.exists(audio_file):
                        os.remove(audio_file)
                        
            else: 
                with sr.Microphone() as source:
                    st.info("🎤 Speak now...")
                    r.adjust_for_ambient_noise(source, duration=0.5)
                    audio_text = r.listen(source, timeout=10, phrase_time_limit=record_seconds)
                    st.info("📝 Transcribing...")
                    
                    if api_choice == "Google Speech Recognition":
                        try:
                            text = r.recognize_google(audio_text, language=language)
                        except sr.UnknownValueError:
                            text = "Google could not understand audio."
                        except sr.RequestError as e:
                            text = f"Google service error: {e}"
                    else:
                        text = transcribe_audio_data_deepgram(audio_text, api_key, language)
                        
        except sr.WaitTimeoutError:
            text = "⏰ No speech detected within the timeout period."
        except Exception as e:
            text = f"❌ Error: {str(e)}"
        
    
        if text and not any(error_msg in text for error_msg in [
            "Error", "could not understand", "service error", "API Error", "transcription error"
        ]):
            st.session_state.transcription += " " + text.strip()
            st.success("✅ Transcription added!")
            st.balloons()
        elif text:
            st.warning(text)

    st.header("📝 Transcription")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.transcription = ""
            st.rerun()
    
    with col2:
        if st.button("💾 Save to File", use_container_width=True):
            if st.session_state.transcription.strip():
                filename = "transcription.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(st.session_state.transcription.strip())
                st.success(f"✅ Saved to {filename}")
            else:
                st.warning("⚠️ No transcription to save")
    
    with col3:
        if st.session_state.transcription.strip():
            st.download_button(
                label="📥 Download",
                data=st.session_state.transcription,
                file_name="transcription.txt",
                mime="text/plain",
                use_container_width=True
            )


    st.text_area(
        "Current Transcription:", 
        st.session_state.transcription, 
        height=200,
        key="transcript_display",
        placeholder="Your transcription will appear here..."
    )
    with st.expander("ℹ️ Instructions & Tips"):
        st.markdown("""
        **How to use:**
        - **Google Speech Recognition**: Free, requires internet
        - **Deepgram**: More accurate, requires API key
        - **Record First**: Record audio first, then choose transcription method
        
        **Tips for better results:**
        - Speak clearly and at a normal pace
        - Reduce background noise
        - Ensure microphone access is granted
        - Use Deepgram for better accuracy (free tier available)
        
        **Get Deepgram API Key:**
        1. Visit [https://deepgram.com/](https://deepgram.com/)
        2. Sign up for free
        3. Go to API section in dashboard
        4. Create new API key
        5. Copy key (starts with `dg_`)
        6. Paste in sidebar above
        """)

if __name__ == "__main__":
    main()