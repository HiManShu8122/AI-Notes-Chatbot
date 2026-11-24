# 📚 AI Notes Chatbot

A beautiful, easy-to-use web app that lets you **upload PDFs, Word docs, and text files** — then **chat with them** using RAG (Retrieval-Augmented Generation). Perfect for studying, research, or reviewing lengthy documents with friends!

## ✨ Features

- 📤 **Drag & drop upload** — supports PDF (.pdf), Word (.docx), plain text (.txt, .md)
- 🤖 **AI-powered Q&A** — ask natural-language questions about your documents
- 🔍 **Source citations** — every answer shows which document it came from + similarity score
- 💬 **Multi-document chat** — search across multiple uploaded files simultaneously
- 🧠 **RAG pipeline** — smart chunking + vector search via ChromaDB
- 🔐 **Your data stays private** — everything processes locally; only OpenAI is called for completions
- 🎨 **Beautiful Streamlit UI** — dark sidebar, message bubbles, clean layout

## 🚀 Quick Start

### 1. Get an OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create a new secret key
3. Save it — you'll paste it into the app's Settings panel

### 2. Activate the virtual environment & launch

```powershell
cd C:\Users\USER\pdf-notes-chatbot
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

The app will open automatically in your default browser at `http://localhost:8501`.

### 3. Upload & chat!

1. Switch to the **📤 Upload Documents** tab
2. Drag and drop your PDF / DOCX / TXT / MD files
3. Switch to **💬 Chat** and start asking questions!

## 🌐 Sharing with Friends

### Option A — Same Wi-Fi (easiest)
```powershell
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```
Friends on the same network can visit `http://<YOUR_IP>:8501`. Find your IP with `ipconfig` → "IPv4 Address".

### Option B — Streamlit Community Cloud (public link)
Push this repo to GitHub, then connect it at https://share.streamlit.io/ for a permanent public URL anyone can use.

## 📦 Dependencies

All dependencies are listed in `requirements.txt`. The venv is pre-created.

Key packages:
- **Streamlit** — web UI framework
- **OpenAI SDK** — LLM chat completions
- **ChromaDB** — local vector database
- **sentence-transformers** — embedding model (`all-MiniLM-L6-v2` from HuggingFace, downloaded once)
- **PyPDF2 / python-docx** — document parsing

## 🗂️ Project Structure

```
pdf-notes-chatbot/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .env.example            # API key template
├── .chroma_db/             # Local vector store (auto-created on first run)
└── utils/
    ├── __init__.py
    ├── parser.py           # Document parsing (PDF, DOCX, TXT, MD)
    ├── embeddings.py       # Embedding provider setup
    └── vectorstore.py      # ChromaDB knowledge base wrapper
```

## ⚙️ Configuration

| Setting | Location | Description |
|---------|----------|-------------|
| API Key | Sidebar → ⚙️ Settings | Your OpenAI API key (session-only, not saved to disk) |
| Model | Sidebar → ⚙️ Settings | Choose between gpt-4o-mini, gpt-4o, or gpt-4-turbo |
| Chunk Size | Sidebar → ⚙️ Settings | Text chunk size for embedding (default: 800 chars) |

## 🔒 Privacy

- **No data leaves your machine** except the chat prompts/completions sent to OpenAI
- Vector chunks are stored locally in `.chroma_db/`
- API keys are never written to disk (entered interactively)
- No analytics, no telemetry, no tracking

## 🐛 Troubleshooting

**"OpenAI API key not found"** — Make sure you entered your key in the sidebar Settings panel.

**App won't start** — Run `.\venv\Scripts\pip.exe install -r requirements.txt` to reinstall deps.

**Embedding model download slow** — First run downloads ~230 MB of model weights from HuggingFace. Subsequent runs reuse the cached copy.

---

Built with ❤️ using Streamlit, OpenAI, and ChromaDB.
