import hashlib
import shutil
import streamlit as st
from pathlib import Path


def _file_hash(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _bytes_hash(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _find_duplicate(audio_dir: Path, file_hash: str) -> Path | None:
    for ext in (".ogg", ".wav", ".mp3", ".m4a"):
        for existing in audio_dir.glob(f"call_*{ext}"):
            try:
                if _file_hash(existing) == file_hash:
                    return existing
            except Exception:
                continue
    return None


def render_upload_page(audio_dir: Path) -> None:
    st.session_state.setdefault("sample_selected", None)
    st.session_state.setdefault("show_samples", False)

    st.markdown("""
    <div style="font-size:13px;color:#4CAF50;margin-bottom:2px;font-family:Courier New,monospace">
        upload_call — analyze new recording
    </div>
    <div style="font-size:11px;color:#333;border-bottom:1px solid #222;
                padding-bottom:8px;margin-bottom:16px;font-family:Courier New,monospace">
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "<div style='font-size:12px;color:#555;margin-bottom:8px;"
        "font-family:Courier New,monospace'>SELECT AUDIO FILE</div>",
        unsafe_allow_html=True,
    )

    up_col, samp_col, _ = st.columns([2, 2, 3])

    with up_col:
        uploaded = st.file_uploader(
            "audio", type=["ogg","wav","mp3","m4a"],
            label_visibility="collapsed",
            key="file_uploader",
        )

    with samp_col:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("📂 sample recordings", use_container_width=True):
            st.session_state.show_samples = not st.session_state.show_samples
            st.rerun()

    # Determine audio source BEFORE sample panel
    audio_source = None
    audio_bytes  = None
    audio_name   = None

    if uploaded:
        audio_bytes  = uploaded.read()
        audio_source = "upload"
        audio_name   = uploaded.name
    elif st.session_state.sample_selected:
        audio_source = "sample"
        audio_name   = Path(st.session_state.sample_selected).stem

    # Instruction box + run pipeline at TOP — always visible
    if audio_source:
        st.markdown(
            f"<div style='background:#0a1a0a;border:1px solid #1a3d1e;border-radius:5px;"
            f"padding:12px 16px;margin:10px 0;font-family:Courier New,monospace'>"
            f"<span style='color:#4CAF50;font-size:14px'>✓ {audio_name} selected</span><br>"
            f"<span style='color:#555;font-size:12px'>choose language below and press "
            f"<span style='color:#4CAF50'>❯ run pipeline</span></span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div style='font-size:12px;color:#555;margin:8px 0 6px;"
            "font-family:Courier New,monospace'>SELECT LANGUAGE</div>",
            unsafe_allow_html=True,
        )
        lang = st.radio(
            "lang", ["auto-detect","english","hindi","hinglish"],
            horizontal=True, label_visibility="collapsed",
        )
        lang_map = {
            "auto-detect":"Auto","english":"English",
            "hindi":"Hindi","hinglish":"Hinglish",
        }
        run_btn = st.button("❯ run pipeline", type="primary")
    else:
        lang     = "auto-detect"
        lang_map = {"auto-detect":"Auto","english":"English","hindi":"Hindi","hinglish":"Hinglish"}
        run_btn  = False

    # Sample panel
    if st.session_state.show_samples:
        sample_files = sorted(audio_dir.glob("call_*.ogg")) if audio_dir.exists() else []
        if not sample_files:
            st.markdown(
                "<div style='color:#555;font-size:13px;font-family:Courier New,monospace;"
                "padding:8px 0'>no sample recordings found</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='background:#0a0a0a;border:1px solid #222;border-radius:8px;"
                "padding:14px;margin-top:10px'>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='font-size:12px;color:#555;margin-bottom:10px;"
                "font-family:Courier New,monospace'>▸ listen and select one sample — only one plays at a time</div>",
                unsafe_allow_html=True,
            )

            sample_names = [f.stem for f in sample_files[:6]]

            # Single dropdown + single audio player
            sel_idx = st.selectbox(
                "Pick a sample to preview",
                range(len(sample_names)),
                format_func=lambda i: sample_names[i],
                label_visibility="collapsed",
                key="preview_idx",
            )
            preview_path = sample_files[sel_idx]
            with open(preview_path, "rb") as f:
                st.audio(f.read(), format="audio/ogg")

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            # Select buttons — selected one always glows green
            cols = st.columns(len(sample_names))
            for i, (col, name, path) in enumerate(zip(cols, sample_names, sample_files[:6])):
                with col:
                    is_sel = st.session_state.sample_selected == str(path)
                    if is_sel:
                        # Always glowing green when selected
                        st.markdown(
                            f"<div style='background:#0a1a0a;border:2px solid #4CAF50;"
                            f"border-radius:3px;padding:6px;text-align:center;"
                            f"color:#4CAF50;font-size:12px;font-family:Courier New,monospace;"
                            f"box-shadow:0 0 8px rgba(76,175,80,0.4)'>✓ {name}</div>",
                            unsafe_allow_html=True,
                        )
                        # Small deselect button below
                        if st.button("✕", key=f"desel_{name}", use_container_width=True,
                                     help="Deselect"):
                            st.session_state.sample_selected = None
                            st.rerun()
                    else:
                        if st.button(name, key=f"sel_{name}", use_container_width=True):
                            st.session_state.sample_selected = str(path)
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # Pipeline execution
    if run_btn and audio_source:
        audio_dir.mkdir(parents=True, exist_ok=True)

        if audio_source == "upload":
            file_hash = _bytes_hash(audio_bytes)
            duplicate = _find_duplicate(audio_dir, file_hash)
        else:
            src_path  = Path(st.session_state.sample_selected)
            file_hash = _file_hash(src_path)
            duplicate = _find_duplicate(audio_dir, file_hash)

        if duplicate:
            existing_id = duplicate.stem
            eval_path   = audio_dir.parent / "evaluations" / f"{existing_id}.json"
            if eval_path.exists():
                import json
                with open(eval_path) as f:
                    ev = json.load(f)
                score = int(ev.get("overall_score", 0) * 10)
                st.markdown(f"""
                <div style="background:#0a1a0a;border:1px solid #1a3d1e;border-radius:6px;
                            padding:14px;margin-top:8px;font-family:Courier New,monospace">
                    <div style="color:#4CAF50;font-size:14px;margin-bottom:6px">
                        ⚡ duplicate detected — loading existing analysis instantly
                    </div>
                    <div style="color:#555;font-size:13px;margin-bottom:4px">
                        already analyzed as <span style="color:#E8E8E8">{existing_id}</span>
                    </div>
                    <div style="color:#555;font-size:13px">
                        score: <span style="color:#4CAF50;font-weight:700">{score}/100</span>
                        &nbsp;·&nbsp; zero tokens used ✓
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.session_state.sample_selected = None
                if st.button("❯ view existing analysis"):
                    st.session_state.page = "overview"
                    st.session_state.selected_call = existing_id
                    if existing_id in st.session_state.get("hidden_calls", set()):
                        st.session_state.hidden_calls.discard(existing_id)
                    st.rerun()
                return

        existing  = sorted(audio_dir.glob("call_*.ogg"))
        call_id   = f"call_{len(existing)+1:03d}"

        if audio_source == "upload":
            suffix    = Path(audio_name).suffix
            save_path = audio_dir / f"{call_id}{suffix}"
            with open(save_path, "wb") as f:
                f.write(audio_bytes)
        else:
            src       = Path(st.session_state.sample_selected)
            save_path = audio_dir / f"{call_id}{src.suffix}"
            shutil.copy(src, save_path)

        from pipeline import run_pipeline
        with st.status("❯ pipeline running...", expanded=True) as status:
            st.write("🎙️ Transcribing audio via Deepgram...")
            try:
                evaluation = run_pipeline(save_path, language=lang_map[lang])
                st.write("🔍 Identifying speakers...")
                st.write("📝 Building transcript...")
                st.write("🤖 Evaluating with GPT...")
                status.update(label="✓ pipeline complete", state="complete")
                score = int(evaluation.get("overall_score", 0) * 10)
                st.markdown(
                    f"<div style='color:#4CAF50;font-size:13px;font-family:Courier New,monospace'>"
                    f"✓ {call_id} analyzed · score: <b>{score}/100</b></div>",
                    unsafe_allow_html=True,
                )
                st.session_state.sample_selected = None
                if st.button("❯ view in overview"):
                    st.session_state.page = "overview"
                    st.session_state.selected_call = call_id
                    st.rerun()
            except Exception as e:
                status.update(label="✕ pipeline failed", state="error")
                st.error(str(e))