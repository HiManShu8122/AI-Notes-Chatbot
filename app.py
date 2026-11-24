"""AI Notes Chatbot — Ask questions about your PDFs, Docs, and text files."""

import os
import base64
from pathlib import Path
from typing import List, Tuple

import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # loads .env if present

# ─── Imports ───────────────────────────────────────────────────────────────────
from utils.parser import parse_document, preview_text
from utils.vectorstore import KnowledgeBase


# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Notes AI Chatbot",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Chat message bubbles */
    .chat-user {
        background: linear-gradient(135deg, #1a73e8, #0d47a1);
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 12px 16px;
        margin-bottom: 8px;
        max-width: 80%;
        align-self: flex-end;
        box-shadow: 0 2px 8px rgba(26,115,232,0.3);
    }
    .chat-bot {
        background: #f0f2f5;
        color: #1d1d1d;
        border-radius: 18px 18px 18px 4px;
        padding: 12px 16px;
        margin-bottom: 8px;
        max-width: 80%;
        align-self: flex-start;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .chat-source {
        background: #fffbe6;
        border-left: 3px solid #faad14;
        border-radius: 6px;
        padding: 8px 12px;
        margin-top: 6px;
        font-size: 0.85em;
        color: #595959;
    }
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #cbd5e1 !important;
    }
    /* Make file uploader look nicer */
    .stFileUploader { border: 2px dashed #3b82f6; border-radius: 12px; padding: 20px; }
    /* Hide streamlit footer */
    #footer { display: none; }
    /* Section headers */
    h2, h3 { color: #e2e8f0 !important; }
    h4 { color: #94a3b8 !important; }
</style>
""", unsafe_allow_html=True)


# ─── State helpers ────────────────────────────────────────────────────────────
def _get_kb_name(filename: str) -> str:
    """Safe collection name derived from filename."""
    safe = Path(filename).stem.replace(" ", "_").replace("-", "_")
    return f"kb_{safe}"


@st.cache_resource
def _new_knowledge_base(name: str) -> KnowledgeBase:
    return KnowledgeBase(name)


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("📚 Notes AI")
    st.markdown("**Ask anything about your documents.** Upload PDFs, Word docs, or text files — then chat!")
    st.divider()

    # --- API Key & Settings ---
    with st.expander("⚙️  Settings", expanded=False):
        current_key = os.getenv("OPENAI_API_KEY", "")
        new_key = st.text_input(
            "OpenAI API Key",
            value=current_key,
            type="password",
            help="Get yours at https://platform.openai.com/api-keys",
        )
        if new_key and new_key != current_key:
            os.environ["OPENAI_API_KEY"] = new_key
            st.session_state["api_key_set"] = True
            st.success("✅ Key saved (session only)")
            st.rerun()

        if "chat_model" not in st.session_state:
            st.session_state.chat_model = "gpt-4o-mini"
        selected_model = st.selectbox(
            "Chat Model",
            ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
            index=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"].index(st.session_state.chat_model),
            help="gpt-4o-mini is fast & cheap; gpt-4o is more capable.",
        )
        if selected_model != st.session_state.chat_model:
            st.session_state.chat_model = selected_model
            st.rerun()

        if "chunk_size" not in st.session_state:
            st.session_state.chunk_size = 800
        cs = st.slider("Chunk Size", min_value=400, max_value=2000, value=st.session_state.chunk_size, step=100,
                       help="Larger chunks = fewer, longer context pieces.")
        if cs != st.session_state.chunk_size:
            st.session_state.chunk_size = cs
            st.info("💡 Re-upload files to apply the new chunk size.")

    st.divider()

    # --- Uploaded documents ---
    st.header("📂 My Documents")

    kb_stats = KnowledgeBase.stats()
    if kb_stats:
        for name, count in kb_stats.items():
            display_name = name.replace("kb_", "").replace("_", " ")
            st.markdown(f"**{display_name}** — {count} chunks")
    else:
        st.caption("No documents uploaded yet.")

    st.divider()

    # --- Clear all ---
    if kb_stats and st.button("🗑️  Clear All Documents", type="primary", use_container_width=True):
        KnowledgeBase.clear_all()
        for key in list(st.session_state.keys()):
            if key.startswith("kb_"):
                del st.session_state[key]
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN AREA — TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab_upload, tab_chat = st.tabs(["📤 Upload Documents", "💬 Chat"])


# ── Tab 1: Upload ──────────────────────────────────────────────────────────────
with tab_upload:
    st.markdown("""
    ### Upload your notes
    Drag & drop **PDF**, **DOCX**, **TXT**, or **MD** files below.
    Each file becomes its own searchable knowledge base.
    """)

    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
        label="📁 Upload Files",
    )

    if uploaded_files:
        for uploaded in uploaded_files:
            raw = uploaded.read()
            kb_name = _get_kb_name(uploaded.name)

            if kb_name in st.session_state:
                st.info(f"ℹ️  Re-uploading *{uploaded.name}* (will replace existing data)")

            with st.spinner(f"Processing *{uploaded.name}* …"):
                try:
                    chunks = parse_document(raw, uploaded.name, chunk_size=st.session_state.chunk_size)
                except Exception as e:
                    st.error(f"❌ Failed to parse {uploaded.name}: {e}")
                    continue

                kb = _new_knowledge_base(kb_name)
                added = kb.add_texts(chunks, {"original_file": uploaded.name})

                st.session_state[kb_name] = kb

                # Show snippet of first chunk
                preview = preview_text(chunks[0]) if chunks else "(empty)"
                st.success(
                    f"✅ **{uploaded.name}** — {len(chunks)} chunks indexed\n"
                    f"*Preview:* `{preview}`"
                )

    st.divider()

    st.caption("""
    **Supported formats:** PDF (.pdf), Word (.docx), plain text (.txt, .md)
    **Tip:** For best results, keep documents under ~50 MB each.
    **Privacy:** All processing happens on your machine. Chunks are stored locally in `.chroma_db/`.
    """)


# ── Tab 2: Chat ────────────────────────────────────────────────────────────────
with tab_chat:
    kb_stats = KnowledgeBase.stats()

    if not kb_stats:
        st.warning("⚠️  No documents loaded yet. Go to the **Upload** tab to add some!")
        st.stop()

    # Which knowledge bases to search
    selected_kbs = st.multiselect(
        "Search in these documents:",
        options=list(kb_stats.keys()),
        default=list(kb_stats.keys())[:1],
    )

    if not selected_kbs:
        st.info("Select at least one document above to start chatting.")
        st.stop()

    # Load KB objects
    kbs = [st.session_state[name] for name in selected_kbs if name in st.session_state]
    if not kbs:
        st.error("Could not load any knowledge bases. Try re-uploading.")
        st.stop()

    # ── Chat history (persistent in session) ──
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ── Display messages ──
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        sources = msg.get("sources", [])

        css_class = "chat-user" if role == "user" else "chat-bot"
        avatar = "🧑‍💻" if role == "user" else "🤖"

        st.markdown(f'<div class="{css_class}"><b>{avatar} </b>{content}</div>', unsafe_allow_html=True)

        if sources:
            for src in sources:
                doc_name = src.get("source", "document")
                text = src.get("text", "")
                score = src.get("score", 0)
                st.markdown(
                    f'<div class="chat-source">📄 <b>{doc_name}</b> '
                    f'(similarity: {score:.3f})<br><i>"{text[:300]}"</i></div>',
                    unsafe_allow_html=True,
                )

    # ── Input bar ──
    prompt = st.chat_input("Ask me anything about your documents…", key="chat_input")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Show thinking indicator
        with st.spinner("Searching documents and crafting answer…"):
            # Gather relevant passages
            all_passages = []
            for kb in kbs:
                docs, dists, metas = kb.query(prompt, n_results=5)
                for d, dist, meta in zip(docs, dists, metas):
                    all_passages.append({
                        "text": d,
                        "score": round(1 - dist, 4),  # cosine distance → similarity
                        "source": meta.get("original_file", meta.get("source", "unknown")),
                    })

            # Sort by relevance
            all_passages.sort(key=lambda x: x["score"], reverse=True)
            top_passages = all_passages[:10]

            # Build RAG context
            context_parts = []
            seen_sources = set()
            for p in top_passages:
                if p["source"] not in seen_sources:
                    context_parts.append(f"[From: {p['source']}]\n{p['text']}")
                    seen_sources.add(p["source"])
            rag_context = "\n\n---\n\n".join(context_parts) if context_parts else "(no relevant passages found)"

            # Call OpenAI
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                reply = "⚠️ Please set your OpenAI API key in the sidebar settings."
            else:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                sys_prompt = (
                    "You are a helpful, friendly assistant that answers questions based ONLY on the provided document context.\n"
                    "If the answer cannot be found in the context, say so honestly — don't make things up.\n"
                    "Cite which document your answer comes from when possible.\n"
                    "Keep answers concise and well-structured."
                )
                completion = client.chat.completions.create(
                    model=st.session_state.chat_model,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": f"Context:\n{rag_context}\n\nQuestion: {prompt}"},
                    ],
                    temperature=0.3,
                    max_tokens=1024,
                )
                reply = completion.choices[0].message.content

        st.session_state.messages.append({
            "role": "assistant",
            "content": reply,
            "sources": [{"source": p["source"], "text": p["text"], "score": p["score"]} for p in top_passages],
        })

        st.rerun()

    # ── Clear chat button ──
    if st.session_state.messages and len(st.session_state.messages) > 0:
        if st.button("🔄 Clear Chat", use_container_width=False):
            st.session_state.messages = []
            st.rerun()

    # Help hint
    st.markdown("---")
    st.caption(
        "💡 **Tips:** Be specific with your questions. "
        "Multi-select multiple documents to compare across them. "
        "Sources are shown below each answer for verification."
    )
