import streamlit as st

st.set_page_config(
    page_title="FrostAlert-TR",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("FrostAlert-TR")
st.markdown(
    "Province-level frost forecast → agricultural price risk signals for Turkey's 81 provinces."
)

st.markdown("""
Use the sidebar to navigate between pages:

- **Risk Map** — Choropleth risk scores by province for a selected crop
- **Product Detail** — Historical event study and sensitivity analysis
- **Methodology** — Risk score formula, data sources, and limitations
""")
