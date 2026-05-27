import streamlit as st

st.set_page_config(
    page_title="FrostAlert-TR",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.styles import inject_global_css
inject_global_css()

st.markdown("""
<style>
.block-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
}
[data-testid="stMainBlockContainer"] {
    padding: 0 !important;
    background-color: #000 !important;
}
[data-testid="stDecoration"] {
    display: none !important;
}
[data-testid="stHeader"] {
    background: #000 !important;
    border-bottom: none !important;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_frost_image():
    from pathlib import Path
    import base64
    for ext in ["jpg", "jpeg", "png", "webp"]:
        p = Path(__file__).parent / "images" / f"frost_image_small.{ext}"
        if p.exists():
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"data:image/{ext};base64,{b64}"
    return ""

frost_src = load_frost_image()

st.markdown(f"""
<div style="
    background:#000;
    min-height:100vh;
    margin:-1rem -1rem 0 -1rem;
    padding:0;
    position:relative;
    overflow:hidden;
">

<!-- Frost image right side -->
{"" if not frost_src else f'''
<div style="
    position:absolute;
    right:0;top:0;bottom:0;
    width:50%;
    background:url({frost_src}) center/cover no-repeat;
    opacity:0.45;
">
</div>
<div style="
    position:absolute;
    right:0;top:0;bottom:0;
    width:55%;
    background:linear-gradient(to right, #000 0%, transparent 40%);
">
</div>
'''}

<!-- Content -->
<div style="
    position:relative;
    z-index:2;
    padding:60px 56px;
    min-height:100vh;
    display:flex;
    flex-direction:column;
    justify-content:center;
    max-width:620px;
">

<div style="
    display:inline-block;
    border:1px solid #555;
    color:#555;
    font-size:0.7em;
    font-weight:600;
    letter-spacing:2px;
    padding:4px 12px;
    border-radius:20px;
    margin-bottom:28px;
">SDG 2 · SDG 13 · CSSM 550 · KOÇ ÜNİVERSİTESİ · 2026</div>

<div style="
    color:#ffffff;
    font-size:3.8em;
    font-weight:900;
    line-height:1.05;
    margin:0 0 20px 0;
    letter-spacing:-1.5px;
    font-family:inherit;
">FROST ALERT<br><span style="color:#7ec8e3">TR</span></div>

<p style="
    color:#cccccc;
    font-size:1.15em;
    font-weight:400;
    line-height:1.65;
    margin:0 0 40px 0;
    max-width:500px;
">Province-level frost forecasts translated into
agricultural price risk signals for Turkey's
81 provinces — before a frost event occurs.</p>

<div style="
    border-left:3px solid #ffd944;
    padding:12px 16px;
    margin-bottom:48px;
    background:rgba(255,217,68,0.06);
">
<div style="color:#ffd944;font-size:0.78em;font-weight:600;letter-spacing:1px;
margin-bottom:6px">2025 FROST CRİSİS</div>
<div style="color:#ccc;font-size:0.88em;line-height:1.5">
65 provinces · 16 fruit product groups<br>
<b style="color:#fff">TL 46.5 billion</b> in TARSİM + government disbursements<br>
based on ex-post damage assessment
</div>
</div>

<div style="margin-top:44px">
<div style="position:relative;display:flex;justify-content:space-between;align-items:flex-start;padding:0 8px">
<div style="position:absolute;top:7px;left:8px;right:8px;height:2px;background:linear-gradient(to right,#7ec8e3,#7ec8e3,#7ec8e3,#ffd944);z-index:0"></div>
<div style="display:flex;flex-direction:column;align-items:center;gap:12px;z-index:1">
<div style="width:16px;height:16px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#b3e8f8,#4fc3f7);box-shadow:0 0 8px rgba(79,195,247,0.7)"></div>
<div style="text-align:center"><div style="color:#7ec8e3;font-weight:700;font-size:1.4em">81</div><div style="color:#555;font-size:0.78em;margin-top:2px">provinces</div></div>
</div>
<div style="display:flex;flex-direction:column;align-items:center;gap:12px;z-index:1">
<div style="width:16px;height:16px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#b3e8f8,#4fc3f7);box-shadow:0 0 8px rgba(79,195,247,0.7)"></div>
<div style="text-align:center"><div style="color:#7ec8e3;font-weight:700;font-size:1.4em">17</div><div style="color:#555;font-size:0.78em;margin-top:2px">crops</div></div>
</div>
<div style="display:flex;flex-direction:column;align-items:center;gap:12px;z-index:1">
<div style="width:16px;height:16px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#b3e8f8,#4fc3f7);box-shadow:0 0 8px rgba(79,195,247,0.7)"></div>
<div style="text-align:center"><div style="color:#7ec8e3;font-weight:700;font-size:1.4em">16d</div><div style="color:#555;font-size:0.78em;margin-top:2px">forecast</div></div>
</div>
<div style="display:flex;flex-direction:column;align-items:center;gap:12px;z-index:1">
<div style="width:16px;height:16px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#ffe88a,#ffd944);box-shadow:0 0 8px rgba(255,217,68,0.7)"></div>
<div style="text-align:center"><div style="color:#ffd944;font-weight:700;font-size:1.4em">E×S×P</div><div style="color:#555;font-size:0.78em;margin-top:2px">risk score</div></div>
</div>
</div>
</div>

<div style="margin-top:48px;color:#555;font-size:0.78em">
← Use the sidebar to navigate
</div>

</div>
</div>
""", unsafe_allow_html=True)
