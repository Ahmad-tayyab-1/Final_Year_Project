
# DocuLearn AI: AI-Powered Learning Support System

A sophisticated Django-based educational platform and intelligent software system that leverages artificial intelligence and advanced Natural Language Processing (NLP) techniques to help students and researchers interact with their learning materials. The system reads, analyzes, and transforms raw learning content from various document formats and YouTube video lectures into interactive, revision-friendly knowledge.

---

## 🚀 Key Features

### 📄 Multi-Format Document Support
Upload, validate, and process a wide range of academic and professional formats (up to 10 MB per file):
- **PDF**: Full text and metadata extraction with explicit page markers and page tracking.
- **Word (DOC, DOCX)**: Document text extraction and high-fidelity automatic conversion to searchable HTML/PDF for consistent inline browser viewing.
- **PowerPoint (PPTX)**: Slide-by-slide text extraction and interactive layout.
- **Excel (XLSX)**: Rows/spreadsheet data extraction and organized tabular parsing.
- **Text (TXT)**: Simple text parsing and whitespace normalization.

### 🎥 YouTube Learning & Advanced Metadata Support
- Extract timestamped lines and transcripts directly from supported YouTube URLs (including standard `youtube.com`, `youtu.be`, `embed`, and `shorts` formats).
- **oEmbed Metadata Integration**: Automatically retrieves public video titles, channel/creator names, channel URLs, and canonical video links without requiring a paid or rate-limited YouTube Data API key.
- Chat with video lecture content natively or ask identity-based contextual questions such as *"whose video is this?"*, *"who made this video?"*, or *"what channel is this?"*.

### 🤖 Intelligent Router-Driven AI Assistant
Powered by **Groq API** utilizing the advanced `llama-3.3-70b-versatile` model with a comprehensive intent-classification prompt policy:
- **Casual Chat**: Handles natural greetings, pleasantries (`hi`, `hello`, `thanks`), and short ambiguous statements with conversational, human-like replies without prematurely forcing document explanations.
- **Context-Aware Q&A**: Answers natural-language questions grounded strictly in the document text or video transcript context, returning page/timestamp citations.
- **General Knowledge Fallback**: If the answers are not found inside the uploaded file, the chatbot leverages its underlying core training parameters to clarify context while ensuring a complete answer.
- **Live Web-Assisted Search**: For real-time, broad, or internet-dependent questions, the backend queries DuckDuckGo HTML, parses snippets with BeautifulSoup, feeds them safely into the Llama prompt, and includes relevant clickable source URLs.

### ✍️ Study Artifacts & Interactive Tools
- **Integrated Document Viewer**: Provides side-by-side view splits placing the high-fidelity document representations right next to interactive work panels.
- **Smart Explanations**: Select any sentence, term, or passage in the viewer to get a localized tooltip explanation from the AI with real-time examples.
- **Flashcard Generation**: Automatically parses segments into persistent front/back study blocks.
- **Automated Quizzes**: Generates Multiple Choice Questions (MCQs with options, answers, and educational explanations) and structured Short-Answer verification sets.
- **Highlight Saving**: Persists highlighted blocks linked to specific colors and matching page numbers.

---

## 🛠 Technical Architecture

The codebase follows a clean, modular, layered design pattern isolating presentation, business orchestration, and data layers:

- **Presentation Layer**: Built using Django templates, CSS, and modern JavaScript AJAX endpoints for quick, asynchronous data updates without page reloads.
- **Application & Service Layer (`views.py`, `utils.py`)**: Coordinates incoming requests, routes input validation, manages session permissions, and acts as the lazy client wrapper wrapper for external endpoints.
- **Data Layer (`models.py`)**: Defines entities and cascades data parameters. It includes optional user foreign keys allowing seamless handling of both authenticated profiles and session-protected guest workflows.

### Core Dependencies & Libraries
- **Backend Framework**: Django 6.0+ (utilizing custom authentication backends accepting exact username or exact email).
- **Extraction & Rendering Suite**:
  - `PyMuPDF (fitz)`: High-performance PDF text and structural layout extraction.
  - `Mammoth`: Custom DOCX-to-HTML formatting parser for pristine browser views.
  - `LibreOffice (Headless / soffice)`: Primary translation engine converting complex multi-layered Office configurations into predictable PDFs.
  - `python-docx` / `python-pptx` / `openpyxl`: Secondary raw structural text mining for Office media types.
  - `beautifulsoup4` & `requests`: Core lightweight parsing utilities for on-demand live web lookup execution.
- **Video Processing**: `youtube-transcript-api` for gathering timestamp-accurate caption files.
- **Production Asset Support**: `WhiteNoise` for efficient serving of compressed static assets, and `Gunicorn` as the high-availability WSGI worker interface.

---

## 📂 Project Structure

```text
newenv/                        # Python virtual environment
doc_learning_system/           # Main Repository Directory
├── doc_learning_system/       # Project configuration (settings.py, urls.py, wsgi.py)
├── documents/                 # Primary Application Application Logic
│   ├── models.py              # Schema Definitions (Document, ChatMessage, Highlight, Flashcard, Quizzes)
│   ├── views.py               # Application logic, route management, and AI orchestration
│   ├── utils.py               # DocumentProcessor, YouTubeProcessor, WebSearch & AIAssistant classes
│   ├── youtube.py             # Reusable 11-character YouTube ID string extraction helpers
│   ├── backends.py            # Dual-authentication backend (Username/Email verification)
│   ├── forms.py               # Registration structures specifying required unique email parameters
│   └── urls.py                # Named application-specific endpoint definitions
├── media/                     # Native host storage location for uploaded/converted materials
│   └── documents/             # Staged target destination for system media streams
├── templates/                 # Global UI Template Architecture
│   ├── base.html              # Main architectural baseline layout
│   └── documents/             # Document views (home library, upload pipeline, detail workspace)
├── render-build.sh            # Automated compilation script package tailored for production
└── manage.py                  # Core Django administration wrapper executable