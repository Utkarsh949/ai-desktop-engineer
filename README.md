# ⬡ AI Desktop Engineer

> A standalone, local-first AI code review and engineering assistant powered by Groq (Llama 3).  
> No webhooks. No servers. No ngrok. Just open and run.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🔬 **Triple-Pass Audit** | Sequential Security (OWASP) → Performance (Big-O) → Architecture (SOLID) review |
| 🐛 **AI Debugger** | Paste broken code → AI explains bugs + rewrites fixed version |
| ✨ **Code Generator** | Describe any feature → AI generates production-grade code |
| 🏗️ **AI Builder** | Describe an app idea → AI generates full project with folder structure |
| 📊 **Project Analyzer** | Scan any local folder for complexity, duplicates, LOC, and health score |
| 🐙 **GitHub Import** | Paste a GitHub URL → clone and analyze without webhooks |
| ⬡ **Dashboard** | Real-time audit history, risk scores, activity log |

---

## 📋 Requirements

- Python 3.10+
- A [Groq API key](https://console.groq.com) (free tier available)
- Windows / macOS / Linux with a display

---

## ⚡ Quick Start

### 1. Clone or download

```bash
git clone https://github.com/yourname/ai_desktop_engineer
cd ai_desktop_engineer
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

```bash
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=gsk_your_actual_key_here
<<<<<<< HEAD
GROQ_MODEL=`llama-3.3-70b-versatile`
=======
GROQ_MODEL=llama-3.3-70b-versatile
>>>>>>> e6c3eb4 (update model)
```

Or configure directly in the **Settings** tab inside the app.

### 5. Run

```bash
python run.py
```

---

## 🗂️ Project Structure

```
ai_desktop_engineer/
│
├── run.py                          # Entry point
├── requirements.txt
├── .env.example
├── README.md
│
├── config/
│   └── config.py                   # Env variables & typed config
│
├── core/
│   ├── ai_engine.py                # Groq API, Triple-Pass audit, debug, generate
│   ├── risk_engine.py              # Risk scoring logic
│   └── logger.py                   # Rotating file + Rich console logger
│
├── services/
│   └── github_importer.py          # GitHub REST API import (no webhooks)
│
├── analyzers/
│   └── project_scanner.py          # Local folder scanner + complexity analysis
│
├── ui/
│   ├── main_gui.py                 # App window, sidebar nav, page routing
│   ├── dashboard_page.py           # Stats, activity log, recent audits
│   ├── code_review_page.py         # Triple-Pass code review UI
│   ├── ai_debugger_page.py         # Debug & fix broken code
│   ├── ai_generator_page.py        # Generate code + AI Builder mode
│   ├── project_analyzer_page.py    # Local project scan + metrics
│   ├── github_import_page.py       # GitHub repo import via API
│   ├── settings_page.py            # API keys & preferences
│   └── widgets.py                  # Shared UI components
│
├── themes/
│   └── themes.py                   # Neon dark colour palette
│
├── logs/                           # Auto-created rotating logs
├── projects/                       # Cloned repos land here
├── snippets/                       # Saved code snippets
└── exports/                        # Generated reports & projects
```

---

## 🎮 Usage Workflows

### Triple-Pass Code Review
1. Open **Code Review** tab
2. Paste code or upload a file/folder
3. Select language
4. Click **Run Triple-Pass Audit**
5. View Security / Performance / Architecture reports
6. Export as Markdown

### Debug Broken Code
1. Open **AI Debugger** tab
2. Paste your broken code
3. Click **Debug & Fix Code**
4. Read the explanation and copy the fixed version

### Generate Code
1. Open **Code Generator** tab
2. Type a prompt: _"Create JWT auth middleware in Python"_
3. Select language/framework
4. Click **Generate Code**
5. Copy or save the output

### Build Full Project
1. Open **Code Generator** tab
2. Switch mode to **AI Builder**
3. Describe your app idea
4. Click **Build Full Project**
5. Save the generated Markdown spec

### Analyze Local Project
1. Open **Project Analyzer** tab
2. Click **Browse Folder**
3. Click **Scan Project**
4. View health score, language breakdown, complexity hotspots

### Import from GitHub
1. Open **GitHub Import** tab
2. Paste a GitHub URL
3. Click **Fetch Info** to preview
4. Click **Clone & Analyze** to download
5. Click **Open in Analyzer**

---

## 🤖 AI Models (Groq)

| Model | Speed | Context | Best For |
|---|---|---|---|
| `llama-3.3-70b-versatile` | Fast | 8K | Best quality reviews |
| `llama-3.3-70b-versatile` | Very Fast | 8K | Quick analysis |
| `llama-3.3-70b-versatile` | Fast | 32K | Large file reviews |
| `llama-3.3-70b-versatile` | Fast | 8K | Code generation |

---

## 🔐 Security Notes

- API keys are stored locally in your `.env` file — never committed to git
- No data is sent to any server except Groq's inference API
- All project files stay on your machine

---

## 📝 License

MIT — use freely for personal and commercial projects.
