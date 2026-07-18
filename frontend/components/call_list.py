import hashlib
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

COLS = [1.4, 1.2, 0.7, 1.0, 0.5, 0.9, 0.6, 0.6]
CELL = "padding:9px 12px;font-family:Inter,sans-serif"
HEAD = f"{CELL};font-size:10px;font-weight:600;color:#697386;text-transform:uppercase;letter-spacing:.5px;background:#F6F9FC;border-bottom:1px solid #E3E8EF"


def score_color(s):
    return "#1EA672" if s >= 80 else "#D97706" if s >= 60 else "#E25950"

def _file_hash(path):
    if not path or not path.exists(): return ""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""): h.update(chunk)
    return h.hexdigest()

def _find_duplicates(all_calls):
    seen, dupes = {}, set()
    for call in all_calls:
        ap = call.get("audio_path")
        if not ap: continue
        h = _file_hash(Path(str(ap)))
        if not h: continue
        if h in seen: dupes.add(call["call_id"])
        else: seen[h] = call["call_id"]
    return dupes

def _delete_call_data_only(call_id, base_dir):
    for folder, ext in [
        ("evaluations", ".json"),
        ("transcripts", ".txt"),
        ("metadata", "_meta.json"),
        ("raw_transcripts", "_raw.json"),
    ]:
        p = base_dir / "data" / folder / f"{call_id}{ext}"
        if p.exists(): p.unlink()


def render_call_list(all_calls, base_dir=None):
    st.session_state.setdefault("hidden_calls", set())
    st.session_state.setdefault("confirm_delete", None)

    visible    = [c for c in all_calls if c["call_id"] not in st.session_state.hidden_calls]
    duplicates = _find_duplicates(all_calls)

    if not visible:
        st.markdown("<div style='text-align:center;padding:40px;font-family:Inter,sans-serif'>"
                    "<div style='font-size:13px;color:#697386'>All calls hidden</div></div>",
                    unsafe_allow_html=True)
        return

    # ── Header row (same COLS as data rows) ──────────────────────────────────
    h = st.columns(COLS)
    for col, label in zip(h[:5], ["Advisor","Customer","Score","Status","Lang"]):
        col.markdown(f"<div style='{HEAD}'>{label}</div>", unsafe_allow_html=True)
    for col in h[5:]:
        col.markdown(f"<div style='{HEAD}'></div>", unsafe_allow_html=True)

    # ── Data rows ─────────────────────────────────────────────────────────────
    for call in visible:
        sc      = call["score"]
        color   = score_color(sc)
        fc      = call["flag_count"]
        is_sel  = st.session_state.selected_call == call["call_id"]
        is_dupe = call["call_id"] in duplicates
        lc      = "#D97706" if call.get("lang","en") == "hi" else "#697386"
        ft      = f"{fc} flag{'s' if fc>1 else ''}" if fc else "✓ Clean"
        fc_col  = "#E25950" if fc else "#1EA672"
        fc_bg   = "#FFF1F0" if fc else "#ECFDF5"
        row_bg  = "#EEF0FF" if is_sel else "#FFF8EC" if is_dupe else "#fff"
        dupe_b  = "<span style='font-size:9px;background:#FFF8EC;color:#D97706;border:1px solid #FDE68A;padding:1px 4px;border-radius:8px;margin-left:4px'>dupe</span>" if is_dupe else ""

        c1,c2,c3,c4,c5,c6,c7,c8 = st.columns(COLS)

        c1.markdown(
            f"<div style='{CELL};background:{row_bg};border-bottom:1px solid #F6F9FC'>"
            f"<div style='font-size:13px;font-weight:500;color:#0A2540'>{call['advisor']}{dupe_b}</div>"
            f"<div style='font-size:11px;color:#B0B7C3'>{call['call_id']}</div></div>",
            unsafe_allow_html=True)
        c2.markdown(
            f"<div style='{CELL};background:{row_bg};border-bottom:1px solid #F6F9FC'>"
            f"<span style='font-size:13px;color:#697386'>{call['customer']}</span></div>",
            unsafe_allow_html=True)
        c3.markdown(
            f"<div style='{CELL};background:{row_bg};border-bottom:1px solid #F6F9FC'>"
            f"<span style='font-size:15px;font-weight:700;color:{color}'>{sc}</span></div>",
            unsafe_allow_html=True)
        c4.markdown(
            f"<div style='{CELL};background:{row_bg};border-bottom:1px solid #F6F9FC'>"
            f"<span style='display:inline-flex;padding:2px 8px;border-radius:20px;"
            f"background:{fc_bg};color:{fc_col};font-size:11px;font-weight:500'>{ft}</span></div>",
            unsafe_allow_html=True)
        c5.markdown(
            f"<div style='{CELL};background:{row_bg};border-bottom:1px solid #F6F9FC'>"
            f"<span style='font-size:11px;font-weight:500;color:{lc}'>{call.get('lang','en').upper()}</span></div>",
            unsafe_allow_html=True)

        with c6:
            if st.button("View →" if not is_sel else "Close",
                         key=f"sel_{call['call_id']}", use_container_width=True):
                st.session_state.selected_call = None if is_sel else call["call_id"]
                st.rerun()
        with c7:
            if st.button("Hide", key=f"hide_{call['call_id']}", use_container_width=True):
                st.session_state.hidden_calls.add(call["call_id"])
                if st.session_state.selected_call == call["call_id"]:
                    st.session_state.selected_call = None
                st.rerun()
        with c8:
            if st.button("DEL", key=f"del_{call['call_id']}", use_container_width=True):
                st.session_state.confirm_delete = call["call_id"]
                st.rerun()

    # JS: style DEL buttons red
    components.html("""<script>
    function redDel() {
        var btns = window.parent.document.querySelectorAll('button');
        for (var i=0;i<btns.length;i++){
            if(btns[i].innerText && btns[i].innerText.trim()==='DEL'){
                btns[i].style.setProperty('background','#FFF1F0','important');
                btns[i].style.setProperty('border-color','#FECACA','important');
                btns[i].style.setProperty('color','#E25950','important');
            }
        }
    }
    redDel();
    setTimeout(redDel,400);
    setTimeout(redDel,1200);
    setInterval(redDel,2000);
    </script>""", height=1, scrolling=False)

    # Confirm delete
    if st.session_state.confirm_delete:
        cid = st.session_state.confirm_delete
        st.markdown(
            f"<div style='background:#FFF1F0;border:1px solid #FECACA;border-radius:8px;"
            f"padding:12px 16px;margin-top:8px;font-family:Inter,sans-serif'>"
            f"<div style='font-size:13px;font-weight:600;color:#E25950;margin-bottom:4px'>Delete {cid}?</div>"
            f"<div style='font-size:12px;color:#697386;margin-bottom:10px'>"
            f"Deletes evaluation, transcript and metadata. Audio file is kept.</div></div>",
            unsafe_allow_html=True)
        d1, d2, _ = st.columns([1, 1, 3])
        with d1:
            if st.button("Confirm", type="primary", key="confirm_del_yes"):
                if base_dir: _delete_call_data_only(cid, base_dir)
                if st.session_state.selected_call == cid:
                    st.session_state.selected_call = None
                st.session_state.confirm_delete = None
                st.rerun()
        with d2:
            if st.button("Cancel", key="confirm_del_no"):
                st.session_state.confirm_delete = None
                st.rerun()

    # Hidden count
    hidden_count = len(st.session_state.hidden_calls)
    if hidden_count > 0:
        hc1, hc2 = st.columns([4, 1])
        with hc1:
            st.markdown(
                f"<div style='font-size:11px;color:#697386;padding:6px 0'>"
                f"{hidden_count} call{'s' if hidden_count>1 else ''} hidden</div>",
                unsafe_allow_html=True)
        with hc2:
            if st.button("Restore all", key="restore_hidden"):
                st.session_state.hidden_calls = set()
                st.rerun()