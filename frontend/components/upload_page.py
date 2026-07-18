import hashlib
import shutil
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path


def _file_hash(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""): h.update(chunk)
    return h.hexdigest()

def _bytes_hash(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()

def _find_existing(audio_dir: Path, file_hash: str):
    for ext in (".ogg", ".wav", ".mp3", ".m4a"):
        for ex in sorted(audio_dir.glob(f"call_*{ext}")):
            try:
                if _file_hash(ex) == file_hash:
                    return ex, ex.stem
            except Exception:
                continue
    return None, None


def render_upload_page(audio_dir: Path) -> None:
    st.session_state.setdefault("sample_selected", None)
    st.session_state.setdefault("show_samples", False)
    st.session_state.setdefault("preview_call", None)

    st.markdown("""
    <div style="font-family:Inter,sans-serif;margin-bottom:16px">
        <div style="font-size:18px;font-weight:700;color:#0A2540;margin-bottom:3px">Upload call recording</div>
        <div style="font-size:13px;color:#697386">Analyze a new sales call using AI transcription and GPT evaluation</div>
    </div>
    """, unsafe_allow_html=True)

    left_col, right_col = st.columns([1.4, 1])

    with left_col:
        st.markdown(
            "<div style='font-size:11px;font-weight:600;color:#697386;text-transform:uppercase;"
            "letter-spacing:.5px;margin-bottom:8px;font-family:Inter,sans-serif'>Audio File</div>",
            unsafe_allow_html=True)

        # Clean file uploader with no label text
        uploaded = st.file_uploader(
            "x",
            type=["ogg", "wav", "mp3", "m4a"],
            label_visibility="collapsed",
            key="file_uploader")

        if st.button("📂 Browse sample recordings"):
            st.session_state.show_samples = not st.session_state.show_samples
            st.rerun()

        # Determine audio source
        audio_source = audio_bytes = audio_name = None
        if uploaded:
            audio_bytes  = uploaded.read()
            audio_source = "upload"
            audio_name   = uploaded.name
        elif st.session_state.sample_selected:
            audio_source = "sample"
            audio_name   = Path(st.session_state.sample_selected).stem

        if audio_source:
            st.markdown(
                f"<div style='background:#EEF0FF;border:1px solid #C7C4FF;border-radius:8px;"
                f"padding:10px 14px;margin:10px 0;font-family:Inter,sans-serif'>"
                f"<div style='font-size:10px;font-weight:600;color:#635BFF;text-transform:uppercase;"
                f"letter-spacing:.5px;margin-bottom:3px'>✓ Ready</div>"
                f"<div style='font-size:13px;font-weight:600;color:#0A2540;margin-bottom:2px'>{audio_name}</div>"
                f"<div style='font-size:12px;color:#697386'>Select language and click "
                f"<b style='color:#635BFF'>Analyze Call</b></div></div>",
                unsafe_allow_html=True)

        st.markdown(
            "<div style='font-size:11px;font-weight:600;color:#697386;text-transform:uppercase;"
            "letter-spacing:.5px;margin:14px 0 10px;font-family:Inter,sans-serif'>Language</div>",
            unsafe_allow_html=True)

        lang = st.radio("lang_select",
            ["Auto-detect", "English", "Hindi", "Hinglish"],
            horizontal=True, label_visibility="collapsed")
        lang_map = {"Auto-detect":"Auto","English":"English","Hindi":"Hindi","Hinglish":"Hinglish"}

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        run_btn = st.button("Analyze Call →", type="primary", disabled=(audio_source is None))

    with right_col:
        if st.session_state.show_samples:
            sample_files = sorted(audio_dir.glob("call_*.ogg")) if audio_dir.exists() else []
            st.markdown(
                "<div style='font-size:11px;font-weight:600;color:#697386;text-transform:uppercase;"
                "letter-spacing:.5px;margin-bottom:4px;font-family:Inter,sans-serif'>Sample Recordings</div>"
                "<div style='font-size:12px;color:#B0B7C3;margin-bottom:12px'>"
                "Click ▶ Play to preview · Click Use to select</div>",
                unsafe_allow_html=True)

            if not sample_files:
                st.markdown(
                    "<div style='font-size:13px;color:#697386;padding:16px;text-align:center;"
                    "background:#F6F9FC;border:1px solid #E3E8EF;border-radius:8px'>"
                    "No samples found in data/audio/</div>", unsafe_allow_html=True)
            else:
                for path in sample_files[:7]:
                    name   = path.stem
                    is_sel = st.session_state.sample_selected == str(path)
                    is_prev = st.session_state.get("preview_call") == name
                    rc1, rc2, rc3 = st.columns([2.5, 1, 1])
                    with rc1:
                        st.markdown(
                            f"<div style='padding:8px 10px;background:{'#EEF0FF' if is_sel else '#F6F9FC'};"
                            f"border:1px solid {'#635BFF' if is_sel else '#E3E8EF'};border-radius:6px'>"
                            f"<div style='font-size:12px;font-weight:600;color:{'#635BFF' if is_sel else '#0A2540'}'>{'✓ ' if is_sel else ''}{name}</div>"
                            f"<div style='font-size:10px;color:#B0B7C3'>{'▶ Now previewing' if is_prev else 'Click ▶ to preview'}</div>"
                            f"</div>", unsafe_allow_html=True)
                    with rc2:
                        if st.button("▶ Play", key=f"prev_{name}", use_container_width=True):
                            st.session_state.preview_call = name
                            st.rerun()
                    with rc3:
                        if st.button("✕" if is_sel else "Use", key=f"sel_{name}", use_container_width=True):
                            st.session_state.sample_selected = None if is_sel else str(path)
                            st.rerun()

                preview_name = st.session_state.get("preview_call")
                if preview_name:
                    preview_path = next((f for f in sample_files if f.stem == preview_name), None)
                    if preview_path and preview_path.exists():
                        st.markdown(
                            f"<div style='margin-top:10px;padding:10px;background:#F6F9FC;"
                            f"border:1px solid #E3E8EF;border-radius:8px'>"
                            f"<div style='font-size:10px;font-weight:600;color:#697386;margin-bottom:6px'>"
                            f"▶ Now previewing: {preview_name}</div>",
                            unsafe_allow_html=True)
                        with open(preview_path, "rb") as f:
                            st.audio(f.read(), format="audio/ogg")
                        st.markdown("</div>", unsafe_allow_html=True)

    if run_btn and audio_source:
        audio_dir.mkdir(parents=True, exist_ok=True)

        file_hash = _bytes_hash(audio_bytes) if audio_source == "upload" \
                    else _file_hash(Path(st.session_state.sample_selected))

        existing_audio, existing_id = _find_existing(audio_dir, file_hash)

        if existing_audio:
            eval_path = audio_dir.parent / "evaluations" / f"{existing_id}.json"
            if eval_path.exists():
                import json
                with open(eval_path) as f: ev = json.load(f)
                score = int(ev.get("overall_score", 0) * 10)
                st.markdown(f"""
                <div style="background:#ECFDF5;border:1px solid #D1FAE5;border-radius:8px;
                            padding:14px;margin-top:10px;font-family:Inter,sans-serif">
                    <div style="font-size:11px;font-weight:600;color:#1EA672;margin-bottom:5px">✓ Already in overview</div>
                    <div style="font-size:13px;color:#0A2540">Already analyzed as <b>{existing_id}</b> · Score: <b style="color:#1EA672">{score}/100</b> · No tokens used</div>
                </div>""", unsafe_allow_html=True)
                st.session_state.sample_selected = None
                if st.button("View in overview →"):
                    st.session_state.page = "overview"
                    st.session_state.selected_call = existing_id
                    st.session_state.hidden_calls.discard(existing_id)
                    st.rerun()
                return
            else:
                call_id   = existing_id
                save_path = existing_audio
        else:
            existing_ids = sorted([
                int(p.stem.split("_")[1])
                for p in audio_dir.glob("call_*.ogg")
                if p.stem.split("_")[1].isdigit()
            ])
            next_num = max(existing_ids) + 1 if existing_ids else 1
            call_id  = f"call_{next_num:03d}"
            if audio_source == "upload":
                save_path = audio_dir / f"{call_id}{Path(audio_name).suffix}"
                with open(save_path, "wb") as f: f.write(audio_bytes)
            else:
                src = Path(st.session_state.sample_selected)
                save_path = audio_dir / f"{call_id}{src.suffix}"
                if src.resolve() != save_path.resolve():
                    shutil.copy(src, save_path)
                else:
                    save_path = src

        from pipeline import run_pipeline
        with st.status("Analyzing call...", expanded=True) as status:
            st.write("🎙️ Transcribing audio via Deepgram...")
            try:
                evaluation = run_pipeline(save_path, language=lang_map[lang])
                st.write("🔍 Identifying speakers...")
                st.write("📝 Building transcript...")
                st.write("🤖 Evaluating with GPT...")
                status.update(label="✓ Analysis complete", state="complete")
                score = int(evaluation.get("overall_score", 0) * 10)
                st.success(f"✓ {call_id} · Score: {score}/100")
                st.session_state.sample_selected = None
                if st.button("View results →"):
                    st.session_state.page = "overview"
                    st.session_state.selected_call = call_id
                    st.rerun()
            except Exception as e:
                status.update(label="Analysis failed", state="error")
                st.error(str(e))