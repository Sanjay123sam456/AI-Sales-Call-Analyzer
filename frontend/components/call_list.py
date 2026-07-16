import hashlib
import json
import streamlit as st
from pathlib import Path


def score_color(s: int) -> str:
    return "#4CAF50" if s >= 80 else "#F59E0B" if s >= 60 else "#E74C3C"


def _file_hash(path: Path) -> str:
    if not path or not path.exists():
        return ""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_duplicates(all_calls: list) -> set:
    """Return set of call_ids that are duplicates (same audio hash, keep first)."""
    seen_hashes = {}
    duplicates  = set()
    for call in all_calls:
        ap = call.get("audio_path")
        if not ap:
            continue
        h = _file_hash(Path(str(ap)))
        if not h:
            continue
        if h in seen_hashes:
            duplicates.add(call["call_id"])
        else:
            seen_hashes[h] = call["call_id"]
    return duplicates


def _delete_call(call_id: str, base_dir: Path) -> None:
    """Delete evaluation, transcript and metadata — keep audio."""
    for folder, ext in [
        ("evaluations", ".json"),
        ("transcripts",  ".txt"),
        ("metadata",     "_meta.json"),
    ]:
        p = base_dir / "data" / folder / f"{call_id}{ext}"
        if p.exists():
            p.unlink()


def render_call_list(all_calls: list, base_dir: Path = None) -> None:
    st.session_state.setdefault("hidden_calls", set())

    visible    = [c for c in all_calls if c["call_id"] not in st.session_state.hidden_calls]
    duplicates = _find_duplicates(all_calls)

    if not visible:
        st.markdown("""
        <div style="text-align:center;padding:40px 0;font-family:Courier New,monospace">
            <div style="font-size:28px;margin-bottom:12px">📭</div>
            <div style="font-size:14px;color:#555;margin-bottom:6px">all calls hidden</div>
            <div style="font-size:12px;color:#333">refresh page to restore all calls</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Header
    st.markdown("""
    <div style="display:flex;padding:6px 8px;border-bottom:1px solid #333;margin-bottom:6px">
        <span style="width:90px;font-size:12px;color:#555;font-family:'Courier New',monospace">CALL</span>
        <span style="width:100px;font-size:12px;color:#555;font-family:'Courier New',monospace">ADVISOR</span>
        <span style="width:100px;font-size:12px;color:#555;font-family:'Courier New',monospace">CUSTOMER</span>
        <span style="width:60px;font-size:12px;color:#555;font-family:'Courier New',monospace">SCORE</span>
        <span style="width:90px;font-size:12px;color:#555;font-family:'Courier New',monospace">FLAGS</span>
        <span style="width:40px;font-size:12px;color:#555;font-family:'Courier New',monospace">LANG</span>
    </div>
    """, unsafe_allow_html=True)

    

    for call in visible:
        sc       = call["score"]
        col      = score_color(sc)
        fc       = call["flag_count"]
        is_sel   = st.session_state.selected_call == call["call_id"]
        is_dupe  = call["call_id"] in duplicates
        lang_col = "#F59E0B" if call.get("lang","en") == "hi" else "#555"
        flag_txt = f"{fc} flag{'s' if fc>1 else ''}" if fc else "clean"
        flag_col = "#E74C3C" if fc else "#4CAF50"
        bg       = "#1F2F1F" if is_sel else "#1a0a0a" if is_dupe else "transparent"

        # Columns: row | view btn | hide btn | delete btn (only for dupes)
        if is_dupe:
            c1, c2, c3, c4 = st.columns([6, 1, 1, 1])
        else:
            c1, c2, c3 = st.columns([6, 1, 1])
            c4 = None

        with c1:
            dupe_badge = (
                "<span style='font-size:10px;color:#E74C3C;background:#2e0808;"
                "padding:1px 6px;border-radius:3px;margin-left:6px'>⚠ dupe</span>"
                if is_dupe else ""
            )
            st.markdown(f"""
            <div style="display:flex;align-items:center;padding:6px 8px;
                        background:{bg};border-radius:3px;font-family:'Courier New',monospace">
                <span style="width:90px;font-size:13px;color:{col}">{call['call_id']}{dupe_badge}</span>
                <span style="width:100px;font-size:13px;color:#E8E8E8">{call['advisor']}</span>
                <span style="width:100px;font-size:13px;color:#E8E8E8">{call['customer']}</span>
                <span style="width:60px;font-size:15px;font-weight:700;color:{col}">{sc}</span>
                <span style="width:90px;font-size:13px;color:{flag_col}">{flag_txt}</span>
                <span style="width:40px;font-size:13px;color:{lang_col}">{call.get('lang','en')}</span>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            if st.button("→" if not is_sel else "✕", key=f"sel_{call['call_id']}"):
                if is_sel:
                    st.session_state.selected_call = None
                else:
                    st.session_state.selected_call = call["call_id"]
                    st.session_state.detail_tab = "overview"
                st.rerun()

        with c3:
            if st.button("hide", key=f"hide_{call['call_id']}"):
                st.session_state.hidden_calls.add(call["call_id"])
                if st.session_state.selected_call == call["call_id"]:
                    st.session_state.selected_call = None
                st.rerun()

        if c4 and is_dupe and base_dir:
            with c4:
                if st.button("🗑", key=f"del_{call['call_id']}", help="Delete duplicate permanently"):
                    _delete_call(call["call_id"], base_dir)
                    if st.session_state.selected_call == call["call_id"]:
                        st.session_state.selected_call = None
                    st.rerun()

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # Hidden count + restore
    hidden_count = len(st.session_state.hidden_calls)
    if hidden_count > 0:
        hc1, hc2 = st.columns([3, 1])
        with hc1:
            st.markdown(
                f"<div style='font-size:11px;color:#333;font-family:Courier New,monospace;"
                f"padding-top:6px'>{hidden_count} call{'s' if hidden_count>1 else ''} hidden</div>",
                unsafe_allow_html=True,
            )
        with hc2:
            if st.button("restore all", key="restore_hidden"):
                st.session_state.hidden_calls = set()
                st.rerun()

    # Command input
    st.markdown(
        "<div style='border-top:1px solid #222;padding-top:8px;"
        "font-size:13px;color:#4CAF50;font-family:Courier New,monospace'>❯</div>",
        unsafe_allow_html=True,
    )
    cmd = st.text_input(
        "cmd",
        placeholder="inspect call_002  ·  flags call_002  ·  scores call_001  ·  help",
        label_visibility="collapsed",
        key="terminal_cmd",
    )
    if cmd:
        _handle_command(cmd.strip().lower(), all_calls)


def _handle_command(cmd: str, all_calls: list) -> None:
    parts = cmd.split()
    verb  = parts[0] if parts else ""
    arg   = parts[1] if len(parts) > 1 else ""

    def find_call(hint):
        return next((c for c in all_calls if hint in c["call_id"]), None)

    if verb == "help":
        st.markdown(
            "<span style='color:#555;font-size:12px;font-family:Courier New,monospace'>"
            "commands: inspect [id] · scores [id] · flags [id] · transcript [id] · hide [id] · clear"
            "</span>", unsafe_allow_html=True)
    elif verb in ("inspect","scores","flags","transcript") and arg:
        match = find_call(arg)
        if match:
            st.session_state.hidden_calls.discard(match["call_id"])
            st.session_state.selected_call = match["call_id"]
            st.session_state.detail_tab = {
                "inspect":"overview","scores":"scores",
                "flags":"flags","transcript":"transcript"
            }[verb]
            st.rerun()
        else:
            st.markdown(f"<span style='color:#E74C3C;font-size:12px'>error: {arg} not found</span>",
                       unsafe_allow_html=True)
    elif verb == "hide" and arg:
        match = find_call(arg)
        if match:
            st.session_state.hidden_calls.add(match["call_id"])
            st.rerun()
    elif verb == "clear":
        st.session_state.selected_call = None
        st.session_state.hidden_calls  = set()
        st.rerun()
    else:
        st.markdown(f"<span style='color:#E74C3C;font-size:12px'>unknown: {cmd} — type help</span>",
                   unsafe_allow_html=True)