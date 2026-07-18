import re
import sys
import json
import streamlit as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from components.terminal_nav  import render_nav
from components.call_list     import render_call_list
from components.detail_panel  import render_detail_panel
from components.upload_page   import render_upload_page

st.set_page_config(
    page_title="SalesCallIQ",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.session_state.setdefault("page", "overview")
st.session_state.setdefault("selected_call", None)
st.session_state.setdefault("hidden_calls", set())
st.session_state.setdefault("search_key", 0)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }

html, body { background-color: #D8DEE9 !important; }
.stApp { background-color: #D8DEE9 !important; }

.block-container {
    padding: 1rem 1.5rem 1.5rem 1.5rem !important;
    max-width: 1240px !important;
    margin: 1rem auto !important;
    background: #F6F9FC !important;
    border-radius: 12px !important;
    border: 1px solid #E3E8EF !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07) !important;
}

*, *::before, *::after { font-family: 'Inter', sans-serif !important; }

/* Restore Material icon font for Streamlit icons */
[data-testid='stIconMaterial'] {
    font-family: 'Material Symbols Outlined', 'Material Icons' !important;
}

/* Hide upload icon inside file uploader — fixes 'uploadUpload' bug */
[data-testid='stFileUploaderDropzone'] [data-testid='stIconMaterial'] {
    display: none !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #fff !important;
    border: 1px solid #E3E8EF !important;
    color: #697386 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 6px 14px !important;
    border-radius: 6px !important;
    transition: all 0.15s !important;
    white-space: nowrap !important;
}
.stButton > button:hover {
    background: #F6F9FC !important;
    border-color: #C8D0DC !important;
    color: #0A2540 !important;
}
.stButton > button[kind="primary"] {
    background: #635BFF !important;
    color: #fff !important;
    border-color: #635BFF !important;
}
.stButton > button[kind="primary"]:hover { background: #5146E5 !important; }

/* Delete button — only in 8th column of call rows */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(8) .stButton > button {
    background: #FFF1F0 !important;
    border: 1px solid #FECACA !important;
    color: #E25950 !important;
}
[data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(8) .stButton > button:hover {
    background: #FEE2E2 !important;
    border-color: #E25950 !important;
    color: #B91C1C !important;
}

/* ── File uploader — clean white ── */
[data-testid="stFileUploaderDropzone"] {
    background: #fff !important;
}

/* Fix invisible instruction text in file uploader */
[data-testid="stFileUploaderDropzoneInstructions"] span {
    color: #697386 !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: #fff !important;
    border: 1px solid #635BFF !important;
    color: #635BFF !important;
    border-radius: 6px !important;
}
[data-testid="stFileUploaderDropzone"] button::before,
[data-testid="stFileUploaderDropzone"] button::after {
    content: none !important;
}



/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #E3E8EF !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #697386 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 14px !important;
    border-radius: 0 !important;
}
.stTabs [data-baseweb="tab"] p,
.stTabs [data-baseweb="tab"] span { color: #697386 !important; font-size: 13px !important; }
.stTabs [aria-selected="true"] { color: #635BFF !important; border-bottom: 2px solid #635BFF !important; }
.stTabs [aria-selected="true"] p,
.stTabs [aria-selected="true"] span { color: #635BFF !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 10px 0 !important; }

/* ── Text input ── */
.stTextInput input {
    background: #fff !important;
    border: 1px solid #E3E8EF !important;
    border-radius: 6px !important;
    color: #0A2540 !important;
    font-size: 13px !important;
    padding: 8px 12px !important;
}
.stTextInput input:focus {
    border-color: #635BFF !important;
    box-shadow: 0 0 0 3px rgba(99,91,255,0.1) !important;
}
.stTextInput input::placeholder { color: #B0B7C3 !important; }

/* ── Radio ── */
.stRadio label { color: #0A2540 !important; font-size: 13px !important; font-weight: 500 !important; }
.stRadio span  { color: #0A2540 !important; font-size: 13px !important; }
.stRadio > div { flex-direction: row !important; gap: 20px !important; flex-wrap: wrap !important; }

/* ── Selectbox ── */
.stSelectbox > div > div {
    background: #fff !important;
    border: 1px solid #E3E8EF !important;
    border-radius: 6px !important;
    color: #0A2540 !important;
}

/* ── Audio ── */
audio::-webkit-media-controls-download-button { display: none !important; }
audio { width: 100%; border-radius: 6px; border: 1px solid #E3E8EF; }

/* ── TWO BOX LAYOUT ──
   #1 = nav (terminal_nav)
   #2 = search + reset
   #3 = left box + right box
*/
[data-testid="stHorizontalBlock"]:nth-of-type(3) {
    gap: 16px !important;
    align-items: stretch !important;
}
/* LEFT BOX */
[data-testid="stHorizontalBlock"]:nth-of-type(3) > [data-testid="column"]:first-child {
    background: #fff !important;
    border: 1px solid #E3E8EF !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    padding: 0 !important;
}
/* RIGHT BOX — separate card, scrolls independently */
[data-testid="stHorizontalBlock"]:nth-of-type(3) > [data-testid="column"]:last-child {
    background: #fff !important;
    border: 1px solid #E3E8EF !important;
    border-radius: 10px !important;
    padding: 20px 16px !important;
    max-height: calc(100vh - 210px) !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    scrollbar-width: thin !important;
    scrollbar-color: #E3E8EF #fff !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
}

[data-testid="column"] { padding: 0 4px !important; }

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #F6F9FC; }
::-webkit-scrollbar-thumb { background: #E3E8EF; border-radius: 2px; }
hr { border-color: #E3E8EF !important; margin: 6px 0 !important; }
[data-testid="stStatusWidget"] {
    background: #fff !important;
    border: 1px solid #E3E8EF !important;
    border-radius: 8px !important;
}
p, label { color: #0A2540 !important; }


</style>
""", unsafe_allow_html=True)

BASE_DIR       = ROOT
EVALUATION_DIR = BASE_DIR / "data" / "evaluations"
TRANSCRIPT_DIR = BASE_DIR / "data" / "transcripts"
AUDIO_DIR      = BASE_DIR / "data" / "audio"
META_DIR       = BASE_DIR / "data" / "metadata"

HINDI_TO_EN = {
    "अमन":"aman","रोहित":"rohit","नेहा":"neha","प्रिया":"priya",
    "राहुल":"rahul","अनिता":"anita","सुरेश":"suresh","संजय":"sanjay",
}
def transliterate(name): return HINDI_TO_EN.get(name, name)

def extract_names(tp):
    if not tp.exists(): return "—","—"
    text = tp.read_text(encoding="utf-8")
    a = re.search(r"Advisor\s*\(([^)]+)\):", text)
    c = re.search(r"Customer\s*\(([^)]+)\):", text)
    return (a.group(1).strip() if a else "—"),(c.group(1).strip() if c else "—")

def find_audio(call_id):
    for ext in (".ogg",".wav",".mp3",".m4a"):
        p = AUDIO_DIR / f"{call_id}{ext}"
        if p.exists(): return p
    return None

def get_lang(call_id):
    meta = META_DIR / f"{call_id}_meta.json"
    if meta.exists():
        with open(meta) as f: return json.load(f).get("detected_language","en")
    return "en"

def load_all_calls():
    if not EVALUATION_DIR.exists(): return []
    calls = []
    for cf in sorted(EVALUATION_DIR.glob("*.json")):
        try:
            with open(cf, encoding="utf-8") as f: ev = json.load(f)
            tp = TRANSCRIPT_DIR / f"{cf.stem}.txt"
            adv, cust = extract_names(tp)
            calls.append({
                "call_id": cf.stem, "transcript_path": tp,
                "audio_path": find_audio(cf.stem), "evaluation": ev,
                "advisor": adv, "customer": cust,
                "advisor_en": transliterate(adv).lower(),
                "customer_en": transliterate(cust).lower(),
                "score": int(ev.get("overall_score",0)*10),
                "flag_count": len(ev.get("red_flags",[])),
                "lang": get_lang(cf.stem),
            })
        except Exception: continue
    return calls

all_calls = load_all_calls()

# stHorizontalBlock #1
render_nav(all_calls)

if st.session_state.page == "upload":
    render_upload_page(AUDIO_DIR)
else:
    if not all_calls:
        st.markdown("""
        <div style="text-align:center;padding:60px 0;font-family:Inter,sans-serif">
            <div style="font-size:28px;margin-bottom:10px">📭</div>
            <div style="font-size:15px;font-weight:600;color:#0A2540;margin-bottom:5px">No calls yet</div>
            <div style="font-size:13px;color:#697386">Click <span style="color:#635BFF;font-weight:500">Upload Call</span> to analyze your first recording</div>
        </div>""", unsafe_allow_html=True)
    else:
        # stHorizontalBlock #2
        s1, s2 = st.columns([5, 1])
        with s1:
            search = st.text_input(
                "search",
                placeholder="Search by advisor or customer name...",
                label_visibility="collapsed",
                key=f"search_{st.session_state.search_key}")
        with s2:
            if st.button("↺ Reset", use_container_width=True):
                st.session_state.selected_call = None
                st.session_state.hidden_calls  = set()
                st.session_state.search_key   += 1
                st.rerun()

        query = search.strip().lower()
        def matches(c):
            if not query: return True
            return (query in c["advisor"].lower()
                    or query in c["customer"].lower()
                    or query in c["call_id"].lower()
                    or query in c["advisor_en"]
                    or query in c["customer_en"])

        filtered = [c for c in all_calls if matches(c)]
        sel = next((c for c in all_calls if c["call_id"]==st.session_state.selected_call), None) \
              if st.session_state.selected_call else None

        if query and not filtered:
            st.markdown(
                f"<div style='color:#697386;font-size:13px;padding:12px 0'>"
                f"No results for '<b>{search}</b>' — clear the search box to see all calls</div>",
                unsafe_allow_html=True)
        else:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

            if sel:
                # stHorizontalBlock #3 — two separate white boxes
                left, right = st.columns([1.15, 1])
                with left:
                    render_call_list(filtered, BASE_DIR)
                with right:
                    render_detail_panel(sel, sel["transcript_path"])
            else:
                # stHorizontalBlock #3 — single wide box
                left, _ = st.columns([1, 0.001])
                with left:
                    render_call_list(filtered, BASE_DIR)