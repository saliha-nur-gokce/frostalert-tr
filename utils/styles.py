import streamlit as st


def inject_global_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main, .stApp {
    background-color: #0a0a0a !important;
}
.block-container {
    background-color: #0a0a0a !important;
}
[data-testid="stSidebar"] {
    background-color: #111111 !important;
    border-right: 1px solid #2a2a2a !important;
}
[data-testid="stSidebar"] * {
    color: #cccccc !important;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background-color: #161616 !important;
    border-left: 3px solid #7ec8e3 !important;
}
[data-testid="stSidebarNavLink"][aria-current="page"] * {
    color: #7ec8e3 !important;
}
h1 { color: #7ec8e3 !important; font-weight: 700 !important; }
h2 { color: #b3e5fc !important; font-weight: 600 !important; }
h3 { color: #b3e5fc !important; font-weight: 500 !important; }
p, li { color: #e8f4f8 !important; }
[data-testid="stMarkdownContainer"] p { color: #e8f4f8 !important; }
[data-testid="stCaptionContainer"] { color: #8ab4cc !important; }
[data-testid="stSelectbox"] > div > div {
    background-color: #161616 !important;
    border: 1px solid #2a2a2a !important;
    color: #e8f4f8 !important;
}
[data-testid="stRadio"] label { color: #e8f4f8 !important; }
[data-testid="stMetricValue"] { color: #7ec8e3 !important; }
[data-testid="stMetricLabel"] { color: #8ab4cc !important; }
[data-testid="stMetric"] {
    background-color: #161616 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}
[data-testid="stAlert"] {
    background-color: #161616 !important;
    border-color: #2a2a2a !important;
    color: #e8f4f8 !important;
}
hr { border-color: #2a2a2a !important; }
[data-testid="stDataFrame"] {
    border: 1px solid #2a2a2a !important;
    border-radius: 6px !important;
}
.dvn-scroller { background-color: #161616 !important; }
[data-testid="stSpinner"] { color: #7ec8e3 !important; }
[data-testid="stHeader"] {
    background: #0a0a0a !important;
    border-bottom: 1px solid #2a2a2a !important;
}
[data-testid="stDecoration"] { display: none !important; }

/* Fix white dropdown popup */
[data-baseweb="popover"],
[data-baseweb="menu"],
[data-baseweb="select"] ul,
[role="listbox"],
[role="option"] {
    background-color: #161616 !important;
    color: #e8f4f8 !important;
    border: 1px solid #2a2a2a !important;
}
[role="option"]:hover,
[aria-selected="true"] {
    background-color: #222222 !important;
}
</style>
""", unsafe_allow_html=True)
