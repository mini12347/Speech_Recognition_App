import streamlit as st
import requests
import tempfile
import os
from datetime import datetime

def transcribe_with_deepgram(audio_file_path, api_key, language="en-US"):
    if not api_key:
        return "❌ Deepgram API key not configured"
    
    try:
        url = "https://api.deepgram.com/v1/listen"
        headers = {"Authorization": f"Token {api_key}"}
        params = {"language": language, "punctuate": "true"}

        with open(audio_file_path, 'rb') as audio_file:
            response = requests.post(url, headers=headers, params=params, data=audio_file, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
            return transcript.strip() if transcript else "No speech detected"
        else:
            return f"❌ Deepgram Error: {response.status_code}"
            
    except Exception as e:
        return f"❌ Transcription error: {str(e)}"

def transcribe_with_google_cloud(audio_file_path, api_key, language="en-US"):
    if not api_key:
        return "❌ Google Cloud API key not configured"
    
    try:
        import base64
        with open(audio_file_path, 'rb') as audio_file:
            audio_content = audio_file.read()

        audio_b64 = base64.b64encode(audio_content).decode('utf-8')
        url = "https://speech.googleapis.com/v1/speech:recognize"
        headers = {"Content-Type": "application/json", "X-Goog-Api-Key": api_key}
        data = {
            "config": {
                "encoding": "LINEAR16",
                "sampleRateHertz": 44100,
                "languageCode": language,
                "enableAutomaticPunctuation": True
            },
            "audio": {"content": audio_b64}
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'results' in result and result['results']:
                transcript = result['results'][0]['alternatives'][0]['transcript']
                return transcript.strip()
            return "No speech detected"
        return f"❌ Google Cloud Error: {response.status_code}"
            
    except Exception as e:
        return f"❌ Transcription error: {str(e)}"

def main():
    st.set_page_config(page_title="Speech Recognition", page_icon="🎙️", layout="wide")
    st.title("🎙️ Speech Recognition App")
    
    if "transcription" not in st.session_state:
        st.session_state.transcription = ""
    

    st.sidebar.header("🔑 Configuration API")
    
    deepgram_key = st.sidebar.text_input(
        "Deepgram API Key",
        type="password",
        placeholder="Entrez votre clé Deepgram (dg_...)",
        help="Obtenez une clé sur https://deepgram.com/"
    )
    
    google_key = st.sidebar.text_input(
        "Google Cloud API Key", 
        type="password",
        placeholder="Entrez votre clé Google Cloud",
        help="Obtenez une clé sur https://cloud.google.com/"
    )
  
    st.sidebar.header("🔧 Statut des Services")
    if deepgram_key:
        st.sidebar.success("✅ Deepgram: Configuré")
    else:
        st.sidebar.warning("⚠️ Deepgram: Non configuré")
        
    if google_key:
        st.sidebar.success("✅ Google Cloud: Configuré")
    else:
        st.sidebar.warning("⚠️ Google Cloud: Non configuré")
    
    # Interface principale avec onglets
    tab1, tab2 = st.tabs(["🎤 Enregistrement Vocal", "📁 Fichier Audio"])
    
    with tab1:
        st.header("🎤 Enregistrement Vocal")
        st.markdown("Enregistrez votre voix directement depuis le navigateur")
        
        audio_bytes = st.audio_input("Cliquez pour enregistrer", key="browser_recording")
        
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            
            col1, col2 = st.columns(2)
            with col1:
                language = st.selectbox(
                    "Langue:",
                    ["en-US", "fr-FR", "es-ES", "de-DE", "ar-SA", "hi-IN", "ja-JP", "ko-KR", "zh-CN"],
                    key="record_lang"
                )
            
            with col2:
                service = st.radio(
                    "Service:",
                    ["Deepgram", "Google Cloud"],
                    horizontal=True,
                    key="record_service"
                )
            
            if st.button("🚀 Transcrire l'enregistrement", use_container_width=True):
                if (service == "Deepgram" and not deepgram_key) or (service == "Google Cloud" and not google_key):
                    st.error("❌ Clé API manquante pour le service sélectionné")
                else:
                    with st.spinner("Transcription en cours..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                            tmp_file.write(audio_bytes.getvalue())
                            tmp_path = tmp_file.name
                        
                        if service == "Deepgram":
                            result = transcribe_with_deepgram(tmp_path, deepgram_key, language)
                        else:
                            result = transcribe_with_google_cloud(tmp_path, google_key, language)
                        
                        os.unlink(tmp_path)
                        
                        if result and not any(error in result for error in ["❌", "not configured", "No speech"]):
                            st.session_state.transcription += " " + result.strip()
                            st.success("✅ Transcription ajoutée !")
                            st.balloons()
                        else:
                            st.error(f"{result}")
    
    with tab2:
        st.header("📁 Fichier Audio")
        st.markdown("Téléchargez un fichier audio existant")
        
        uploaded_file = st.file_uploader(
            "Choisissez un fichier audio",
            type=['wav', 'mp3', 'm4a', 'ogg'],
            accept_multiple_files=False
        )
        
        if uploaded_file is not None:
            st.audio(uploaded_file, format=uploaded_file.type)
            
            col1, col2 = st.columns(2)
            with col1:
                language = st.selectbox(
                    "Langue:",
                    ["en-US", "fr-FR", "es-ES", "de-DE", "ar-SA", "hi-IN", "ja-JP", "ko-KR", "zh-CN"],
                    key="upload_lang"
                )
            
            with col2:
                service = st.radio(
                    "Service:",
                    ["Deepgram", "Google Cloud"],
                    horizontal=True,
                    key="upload_service"
                )
            
            if st.button("🚀 Transcrire le fichier", use_container_width=True):
                if (service == "Deepgram" and not deepgram_key) or (service == "Google Cloud" and not google_key):
                    st.error("❌ Clé API manquante pour le service sélectionné")
                else:
                    with st.spinner("Transcription en cours..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        
                        if service == "Deepgram":
                            result = transcribe_with_deepgram(tmp_path, deepgram_key, language)
                        else:
                            result = transcribe_with_google_cloud(tmp_path, google_key, language)
                        
                        os.unlink(tmp_path)
                        
                        if result and not any(error in result for error in ["❌", "not configured", "No speech"]):
                            st.session_state.transcription += " " + result.strip()
                            st.success("✅ Transcription ajoutée !")
                            st.balloons()
                        else:
                            st.error(f"{result}")
    
    st.header("📝 Résultats de Transcription")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Tout effacer", use_container_width=True):
            st.session_state.transcription = ""
            st.rerun()
    
    with col2:
        if st.button("💾 Sauvegarder", use_container_width=True):
            if st.session_state.transcription.strip():
                filename = f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(st.session_state.transcription.strip())
                st.success(f"✅ Sauvegardé sous {filename}")
            else:
                st.warning("⚠️ Aucune transcription à sauvegarder")
    
    with col3:
        if st.session_state.transcription.strip():
            st.download_button(
                label="📥 Télécharger",
                data=st.session_state.transcription,
                file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    st.text_area(
        "Transcription actuelle:",
        st.session_state.transcription,
        height=200,
        placeholder="Vos transcriptions apparaîtront ici...",
        key="transcript_display"
    )
    
    with st.expander("ℹ️ Instructions"):
        st.markdown("""
        **Comment utiliser:**
        1. **Enregistrement Vocal**: Utilisez l'enregistreur du navigateur
        2. **Fichier Audio**: Téléchargez un fichier existant
        
        **Configuration API:**
        - **Deepgram**: Clé gratuite sur [deepgram.com](https://deepgram.com)
        - **Google Cloud**: Clé sur [Google Cloud Console](https://console.cloud.google.com)
        
        **Formats supportés:** WAV, MP3, M4A, OGG
        """)

if __name__ == "__main__":
    main()
