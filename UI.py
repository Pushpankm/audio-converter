import streamlit as st
from pydub import AudioSegment
from pydub.utils import which
import requests
import os
import zipfile
import pandas as pd

# Setup ffmpeg paths
AudioSegment.converter = which("ffmpeg")
AudioSegment.ffprobe = which("ffprobe")

st.set_page_config(page_title="GSM WAV to PCM WAV Converter", page_icon="🎧")
st.title("🎧 Call Recordings")

os.makedirs("converted", exist_ok=True)

def convert_to_pcm(input_path, output_path):
    try:
        audio = AudioSegment.from_file(input_path, format="wav")
        audio.export(output_path, format="wav", codec="pcm_s16le")
        return True
    except Exception as e:
        return str(e)

def download_and_convert(url, filename):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None, f"HTTP Error {response.status_code}"
        input_path = f"converted/{filename}_input.wav"
        output_path = f"converted/{filename}_output.wav"

        with open(input_path, "wb") as f:
            f.write(response.content)

        result = convert_to_pcm(input_path, output_path)
        if result is True:
            return output_path, None
        else:
            return None, result
    except Exception as e:
        return None, str(e)

option = st.radio("Select Input Method:", [
    "🔗 Convert via URL",
    "📁 Upload .wav files",
    "📄 Upload CSV/Excel Fields Names Required =URLs + AWB"
])

if option == "🔗 Convert via URL":
    url = st.text_input("Enter WAV (GSM encoded) audio URL:")
    filename = st.text_input("Enter filename to save as (without extension):", value="")

    if st.button("🎯 Convert and Play"):
        if url:
            st.info("Converting...")
            result, error = download_and_convert(url, filename)
            if result:
                st.success("✅ Converted Successfully!")
                st.audio(result, format="audio/wav")
                with open(result, "rb") as f:
                    st.download_button("⬇️ Download Converted PCM WAV", f, file_name=f"{filename}_pcm.wav")
            else:
                st.error(f"❌ Conversion failed: {error}")
        else:
            st.warning("⚠️ Please enter a valid URL.")

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
                    res = convert_to_pcm(temp_path, output_path)
                    if res is True:
                        zipf.write(output_path, arcname=os.path.basename(output_path))
                        st.success(f"✅ Converted: {file.name}")
                        st.audio(output_path, format="audio/wav")
                    else:
                        st.error(f"❌ Conversion failed for {file.name}: {res}")
            with open(zip_filename, "rb") as f:
                st.download_button("⬇️ Download All Converted Files (ZIP)", f, file_name=zip_filename)
        else:
            st.warning("⚠️ Please upload files first.")

elif option == "📄 Upload CSV/Excel Fields Names Required =URLs + AWB":
    file = st.file_uploader("Upload CSV or Excel file", type=["csv", "xlsx"])

    if file:
        try:
            if file.name.endswith(".csv"):
                df = pd.read_csv(file, encoding="latin1", engine="python")
            else:
                df = pd.read_excel(file)
        except Exception as e:
            st.error(f"❌ Error reading file: {e}")
            st.stop()

        # Detect columns
        url_col = None
        awb_col = None
        for col in df.columns:
            if 'url' in col.lower():
                url_col = col
            if 'awb' in col.lower():
                awb_col = col

        if not url_col:
            st.error("❌ Couldn't find URL column in file.")
            st.stop()

        if st.button("🎯 Start Conversion"):
            total = len(df)
            success_files = []
            error_files = []

            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, row in df.iterrows():
                status_text.text(f"Processing {i+1} of {total}")
                progress_bar.progress((i + 1) / total)

                url = row[url_col]
                name = str(row[awb_col]) if awb_col else f"file_{i+1}"
                name = name.strip().replace(" ", "_").replace("/", "_")

                if not isinstance(url, str) or not url.startswith("http"):
                    error_files.append((name, "Invalid URL"))
                    continue

                result, error = download_and_convert(url, name)
                if result:
                    success_files.append(name)
                else:
                    error_files.append((name, error))

            st.success(f"✅ Conversion Completed: {len(success_files)} of {total} files successfully converted.")

            with st.expander("Show Detailed Conversion Report"):
                st.write(f"### Successfully converted files ({len(success_files)})")
                for f in success_files:
                    st.write(f"- {f}")

                st.write(f"### Files with errors ({len(error_files)})")
                for f, err in error_files:
                    st.write(f"- {f} : {err}")

            if len(success_files) > 0:
                zip_filename = "converted_files.zip"
                with zipfile.ZipFile(zip_filename, "w") as zipf:
                    for f in success_files:
                        file_path = f"converted/{f}_output.wav"
                        if os.path.exists(file_path):
                            zipf.write(file_path, arcname=os.path.basename(file_path))
                with open(zip_filename, "rb") as fzip:
                    st.download_button("⬇️ Download All Converted Files (ZIP)", fzip, file_name=zip_filename)
    else:
        st.warning("⚠️ Please upload a file.")
