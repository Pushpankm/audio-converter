# analytics_dashboard.py
import streamlit as st
import json

SECRET_ACCESS = "developer123"

query_params = st.experimental_get_query_params()
if query_params.get("analytics", [""])[0] != SECRET_ACCESS:
    st.stop()

st.set_page_config(page_title="Usage Analytics", layout="centered")
st.title("🔍 Custom Analytics Dashboard")

analytics_data = {
    "Choose Converter:": {
        "WAV to MP3 Converter": 10,
        "WAV to PCM Converter": 0
    },
    "Select Input Method:": {
        "🔗 Convert via URL": 8,
        "📁 Upload .wav files": 0,
        "📄 Upload CSV/Excel Fields Names Required =URLs + AWB": 2
    },
    "Enter WAV audio URL:": {
        " ": 8
    },
    "Enter filename to save as (without extension):": {
        " ": 8
    },
    "🎯 Convert and Play": 0,
    "Upload CSV or Excel file": 0
}

stats = {
    "Pageviews": 6,
    "Script runs": 10,
    "Time spent": "00:04:28",
    "Since": "16 May 2025, 11:02:19"
}

st.subheader("📊 Summary")
st.markdown(f"""
- **Pageviews:** `{stats['Pageviews']}`
- **Script Runs:** `{stats['Script runs']}`
- **Time Spent (total):** `{stats['Time spent']}`
- **Tracking Since:** `{stats['Since']}`
""")

st.divider()
st.subheader("🧠 Widget Interactions")

for widget, data in analytics_data.items():
    with st.expander(f"🔹 {widget}"):
        for key, count in data.items():
            st.markdown(f"- **{key}**: `{count}` times")

st.warning("🚧 This dashboard is only visible to you. Don't share your secret key!", icon="🔐")
