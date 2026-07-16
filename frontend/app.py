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
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.session_state.setdefault("page", "overview")
st.session_state.setdefault("selected_call", None)
st.session_state.setdefault("hidden_calls", set())
st.session_state.setdefault("search_key", 0)

st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }
.block-container { padding: 1.5rem 4rem 2rem 4rem !important; max-width: 1300px !important; margin: 0 auto !important; }
.stApp { background: #0D0D0D !important; }
body   { background: #0D0D0D !important; }
body::-webkit-scrollbar { display: none !important; }
body { -ms-overflow-style: none !important; scrollbar-width: none !important; }
audio::-webkit-media-controls-download-button { display: none !important; }
audio { width: 100%; border-radius: 6px; margin-top: 4px; }
.stButton > button { background: transparent !important; border: 1px solid #333 !important; color: #4CAF50 !important; font-family: 'Courier New', monospace !important; font-size: 13px !important; padding: 5px 14px !important; border-radius: 3px !important; }
.stButton > button:hover { background: #1F2F1F !important; border-color: #4CAF50 !important; }
.stButton > button[kind="primary"] { border-color: #4CAF50 !important; background: #0a1a0a !important; }
.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid #333 !important; gap: 0 !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #555 !important; font-family: 'Courier New', monospace !important; font-size: 13px !important; padding: 5px 14px !important; }
.stTabs [aria-selected="true"] { color: #4CAF50 !important; border-bottom: 2px solid #4CAF50 !important; background: transparent !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 8px 0 !important; background: transparent !important; }
.stTextInput input { background: #0D0D0D !important; border: 1px solid #333 !important; color: #E8E8E8 !important; font-family: 'Courier New', monospace !important; font-size: 13px !important; border-radius: 3px !important; padding: 6px 10px !important; }
.stTextInput input::placeholder { color: #444 !important; }
.stRadio label { color: #666 !important; font-size: 13px !important; font-family: 'Courier New', monospace !important; }
[data-testid="stFileUploader"] { background: #111 !important; border: 1px dashed #333 !important; border-radius: 6px !important; }
[data-testid="column"] { padding: 0 6px !important; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0D0D0D; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
hr { border-color: #222 !important; }
</style>
""", unsafe_allow_html=True)

BASE_DIR       = ROOT
EVALUATION_DIR = BASE_DIR / "data" / "evaluations"
TRANSCRIPT_DIR = BASE_DIR / "data" / "transcripts"
AUDIO_DIR      = BASE_DIR / "data" / "audio"
META_DIR       = BASE_DIR / "data" / "metadata"

# Hindi → English transliteration map for search
HINDI_TO_EN = {
    "अमन": "aman", "रोहित": "rohit", "नेहा": "neha",
    "प्रिया": "priya", "राहुल": "rahul", "अनिता": "anita",
    "सुरेश": "suresh", "दीपा": "deepa", "रयान": "ryan",
    "एमा": "emma", "डेविड": "david", "एमिली": "emily",
    "काजल": "kajal", "पूजा": "pooja", "विकास": "vikas",
    "संजय": "sanjay", "रमेश": "ramesh", "सुनीता": "sunita",
}

def transliterate(name: str) -> str:
    """Return English equivalent if Hindi name, else original."""
    return HINDI_TO_EN.get(name, name)

def extract_names(tp):
    if not tp.exists(): return "—", "—"
    text = tp.read_text(encoding="utf-8")
    a = re.search(r"Advisor\s*\(([^)]+)\):", text)
    c = re.search(r"Customer\s*\(([^)]+)\):", text)
    return (a.group(1).strip() if a else "—"), (c.group(1).strip() if c else "—")

def find_audio(call_id):
    for ext in (".ogg", ".wav", ".mp3", ".m4a"):
        p = AUDIO_DIR / f"{call_id}{ext}"
        if p.exists(): return p
    return None

def get_lang(call_id):
    meta = META_DIR / f"{call_id}_meta.json"
    if meta.exists():
        with open(meta) as f:
            return json.load(f).get("detected_language", "en")
    return "en"

def load_all_calls():
    if not EVALUATION_DIR.exists(): return []
    calls = []
    for cf in sorted(EVALUATION_DIR.glob("*.json")):
        try:
            with open(cf, encoding="utf-8") as f:
                ev = json.load(f)
            tp = TRANSCRIPT_DIR / f"{cf.stem}.txt"
            adv, cust = extract_names(tp)
            calls.append({
                "call_id":          cf.stem,
                "transcript_path":  tp,
                "audio_path":       find_audio(cf.stem),
                "evaluation":       ev,
                "advisor":          adv,
                "customer":         cust,
                "advisor_en":       transliterate(adv).lower(),
                "customer_en":      transliterate(cust).lower(),
                "score":            int(ev.get("overall_score", 0) * 10),
                "flag_count":       len(ev.get("red_flags", [])),
                "lang":             get_lang(cf.stem),
            })
        except Exception:
            continue
    return calls

all_calls = load_all_calls()
render_nav(all_calls)
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

if st.session_state.page == "upload":
    render_upload_page(AUDIO_DIR)
else:
    if not all_calls:
        st.markdown("""
        <div style="text-align:center;padding:80px 0;font-family:Courier New,monospace">
            <div style="font-size:32px;margin-bottom:16px">📭</div>
            <div style="font-size:15px;color:#555;margin-bottom:8px">no calls analyzed yet</div>
            <div style="font-size:13px;color:#333">
                → go to <span style="color:#4CAF50">[ upload_call ]</span>
                to analyze your first recording
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        s1, s2 = st.columns([4, 1])
        with s1:
            search = st.text_input(
                "search",
                placeholder="⌕  search by advisor or customer name...",
                label_visibility="collapsed",
                key=f"search_{st.session_state.search_key}",
            )
        with s2:
            if st.button("↺ reset view", use_container_width=True):
                st.session_state.selected_call = None
                st.session_state.hidden_calls  = set()
                st.session_state.search_key   += 1
                st.rerun()

        query = search.strip().lower()

        def matches(c):
            if not query: return True
            return (
                query in c["advisor"].lower()
                or query in c["customer"].lower()
                or query in c["call_id"].lower()
                or query in c["advisor_en"]
                or query in c["customer_en"]
            )

        filtered = [c for c in all_calls if matches(c)]

        if query and not filtered:
            st.markdown(
                f"<div style='color:#555;font-size:13px;padding:20px 0;"
                f"font-family:Courier New,monospace'>"
                f"no results for '<span style='color:#E8E8E8'>{search}</span>' "
                f"— click ↺ reset view to clear</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            if st.session_state.selected_call:
                left, right = st.columns([1.1, 1])
            else:
                left  = st.container()
                right = None

            with left:
                render_call_list(filtered, BASE_DIR)

            if right and st.session_state.selected_call:
                with right:
                    sel = next(
                        (c for c in all_calls if c["call_id"] == st.session_state.selected_call),
                        None,
                    )
                    if sel:
                        render_detail_panel(sel, sel["transcript_path"])