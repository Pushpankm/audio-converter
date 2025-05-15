import streamlit as st
from pydub import AudioSegment
from pydub.utils import which
import requests
import os
import zipfile
import pandas as pd

# Set ffmpeg and ffprobe binary paths
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")

st.set_page_config(page_title="Call Recording", page_icon="🎧")

st.title("🎧 Call Recording ")
st.caption("")

# Create output folder
os.makedirs("converted", exist_ok=True)

# Function to play audio
def play_audio(file_path):
    st.audio(file_path, format="audio/wav")

# GSM to PCM conversion
def convert_to_pcm(input_path, output_path):
    try:
        audio = AudioSegment.from_file(input_path, format="wav")
        audio.export(output_path, format="wav", codec="pcm_s16le")
        return True
    except Exception as e:
        st.error(f"❌ Conversion error: {e}")
        return False

# Download and convert from URL
def download_and_convert(url, filename):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None
        input_path = f"converted/{filename}_input.wav"
        output_path = f"converted/{filename}_output.wav"

        with open(input_path, "wb") as f:
            f.write(response.content)

        if convert_to_pcm(input_path, output_path):
            return output_path
        return None
    except Exception as e:
        st.error(f"❌ Download/Conversion error: {e}")
        return None

# Interface
option = st.radio("Select Input Method:", ["🔗 Convert via URL", "📁 Upload .wav files", "📄 Upload CSV/Excel Field Names=URLs + AWB"])

# === URL to PCM Conversion ===
if option == "🔗 Convert via URL":
    url = st.text_input("Enter WAV (GSM encoded) audio URL:")
    filename = st.text_input("Enter filename to save as (without extension):", value="Sample Name")

    if st.button("🎯 Convert and Play"):
        if url:
            st.info("Converting...")
            result = download_and_convert(url, filename)
            if result:
                st.success("✅ Converted Successfully!")
                play_audio(result)
                with open(result, "rb") as f:
                    st.download_button("⬇️ Download Converted PCM WAV", f, file_name=f"{filename}_pcm.wav")
        else:
            st.warning("⚠️ Please enter a valid URL.")

# === File Upload ===
elif option == "📁 Upload .wav files":
    uploaded_files = st.file_uploader("Upload one or more .wav files", type=["wav"], accept_multiple_files=True)

    if st.button("🎯 Convert Uploaded Files"):
        if uploaded_files:
            zip_filename = "converted_pcm_wav_files.zip"
            with zipfile.ZipFile(zip_filename, "w") as zipf:
                for file in uploaded_files:
                    temp_path = f"converted/{file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(file.read())

                    output_path = temp_path.replace(".wav", "_pcm.wav")
                    if convert_to_pcm(temp_path, output_path):
                        zipf.write(output_path, arcname=os.path.basename(output_path))
                        st.success(f"✅ Converted: {file.name}")
                        play_audio(output_path)
            with open(zip_filename, "rb") as f:
                st.download_button("⬇️ Download All Converted Files (ZIP)", f, file_name=zip_filename)
        else:
            st.warning("⚠️ Please upload files first.")

# === Excel/CSV Bulk Upload ===
elif option == "📄 Upload CSV/Excel (Fields Name  = URLs + AWB)":
    file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

    if st.button("🎯 Convert from Excel/CSV"):
        if file:
            try:
                if file.name.endswith(".csv"):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)

                # Detect columns
                url_col = None
                for col in df.columns:
                    if 'url' in col.lower() or 'recording' in col.lower():
                        url_col = col
                        break

                filename_col = None
                for col in df.columns:
                    if 'awb' in col.lower() or 'id' in col.lower() or 'name' in col.lower():
                        filename_col = col
                        break

                if url_col:
                    zip_filename = "converted_bulk_pcm_files.zip"
                    with zipfile.ZipFile(zip_filename, "w") as zipf:
                        for i, row in df.iterrows():
                            url = row[url_col]
                            name = str(row[filename_col]) if filename_col else f"file_{i+1}"
                            name = name.strip().replace(" ", "_").replace("/", "_")

                            st.write(f"🔄 Processing: {name}")
                            result = download_and_convert(url, name)
                            if result:
                                zipf.write(result, arcname=os.path.basename(result))
                                st.success(f"✅ Converted: {name}")
                            else:
                                st.error(f"❌ Failed: {name}")
                    with open(zip_filename, "rb") as f:
                        st.download_button("⬇️ Download All Converted Files (ZIP)", f, file_name=zip_filename)
                else:
                    st.error("❌ Couldn't find a valid URL column in file.")
            except Exception as e:
                st.error(f"❌ File processing error: {e}")
        else:
            st.warning("⚠️ Please upload a file.")