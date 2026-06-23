# AI Web Extractor & Content Restructurer

A modern, high-performance desktop GUI application built in Python using CustomTkinter that scrapes any webpage, extracts the core content, and restructures it using Google Gemini or a local Ollama AI model.

## Features

- **Responsive Multi-Resolution Layout**: Modern Dark Theme desktop interface that dynamically scales down to `800x600` and supports vertical scrolling inside the settings sidebar to prevent clipping on low-resolution displays.
- **AI Enhancement Providers**:
  - **Google Gemini**: Supports standard and next-generation models (`gemini-3.5-flash`, `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-3.1-pro-preview`, etc.).
  - **Ollama (Local)**: Runs offline models (`llama3`, `mistral`, `gemma`, etc.) on local hardware.
- **Dynamic Local Model Auto-Discovery**: Automatically queries local Ollama instances on startup, url changes, or connection toggle, displaying your installed local models in a dropdown combobox and auto-selecting the first available one.
- **Pre-check Safeguards**: Alerts you before launching if a local Ollama service is unreachable and offers to dynamically switch the execution to Gemini if you have a Gemini API Key configured.
- **Restructuring Presets**: Includes pre-defined structuring prompts (Executive Summary, Structured Q&A, Data Extractor, Clean Markdown Document) as well as custom system instructions.
- **Clipboard & Export Utilities**: Quick actions to copy parsed outputs or save content to `.txt`, `.md`, or `.json` files.

---

## Installation

### Prerequisites
- Python 3.8 or higher.
- (Optional) [Ollama](https://ollama.com) installed and running locally for offline models.

### Step 1: Install Dependencies
Open your command terminal in the project directory and run:
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Create a file named `.env` in the root directory (or use the inside-app settings to input them):
```ini
GEMINI_API_KEY=your_gemini_api_key_here
```

### Step 3: Run the Application
Start the desktop interface:
```bash
python app.py
```

---

## Using Local AI (Ollama)

To run predictions completely locally without an internet connection:
1. Install Ollama on your system.
2. Open your terminal and pull a model of your choice:
   ```bash
   ollama pull llama3
   ```
3. Run the Ollama app (ensure it is running at `http://localhost:11434`).
4. Launch `app.py` and select **Ollama (Local)** in the dropdown. The application will scan and let you pick your downloaded model.
