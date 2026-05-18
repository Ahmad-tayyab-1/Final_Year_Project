# AI-Powered Learning Support System

A sophisticated Django-based educational platform that leverages AI to help students and researchers interact with their learning materials. The system supports various document formats and YouTube videos, providing automated summaries, Q&A, flashcards, and quizzes.

## 🚀 Key Features

### 📄 Multi-Format Document Support
Upload and process a wide range of academic and professional formats:
- **PDF**: Full text extraction with page tracking.
- **Word (DOC, DOCX)**: Automatic conversion to searchable PDF.
- **PowerPoint (PPTX)**: Slide-by-slide text extraction and viewing.
- **Excel (XLSX)**: Spreadsheet data processing.
- **Text (TXT)**: Simple text parsing.

### 🎥 YouTube Learning
- Extract transcripts directly from YouTube URLs.
- Chat with video content as if it were a document.
- Generate study materials from lectures and tutorials.

### 🤖 AI-Powered Assistant (Groq Llama 3)
- **Context-Aware Chat**: Ask questions about your documents and get answers with page/timestamp citations.
- **Smart Explanations**: Select any text in a document to get a detailed AI explanation.
- **Flashcard Generation**: Automatically create front/back study cards from content.
- **Quiz Generation**: Generate Multiple Choice Questions (MCQs) and Short-Answer questions to test your knowledge.

### ✍️ Interactive Study Tools
- **Integrated PDF Viewer**: High-fidelity viewing of processed documents.
- **Highlighting**: Save important sections for later review.
- **Persistence**: Chat history and generated questions are saved per document.

---

## 🛠 Technical Architecture

- **Backend**: Django 6.0+
- **AI Engine**: Groq API (utilizing `llama-3.3-70b-versatile`)
- **Document Processing**:
  - `PyMuPDF (fitz)`: High-performance PDF text and metadata extraction.
  - `LibreOffice (Headless)`: Used for converting Office documents to PDF for consistent viewing.
  - `python-docx` / `python-pptx` / `openpyxl`: Secondary extraction for Office formats.
  - `youtube-transcript-api`: Reliable fetching of video captions.

---

## 📂 Project Structure

```text
newenv/
doc_learning_system/
├── doc_learning_system/       # Project configuration (settings, urls)
├── documents/                 # Core application logic
│   ├── models.py              # Database schema (Documents, Chat, Quizzes)
│   ├── views.py               # Request handling & AI orchestration
│   ├── utils.py               # Document & YouTube processing engines
│   └── urls.py                # App-specific routing
├── media/                     # Storage for uploaded/converted files
├── templates/                 # HTML templates
│   ├── base.html              # Main layout
│   └── documents/             # App-specific views (home, detail, upload)
└── manage.py                  # Django management script
```

---

## ⚙️ Installation & Setup

### Prerequisites
- **Python 3.10+**
- **LibreOffice**: Required for Office-to-PDF conversion. Ensure `soffice` is in your system PATH or installed in the default location.

### 1. Clone & Environment
```bash
git clone <repository-url>
cd "Final year project"
python -m venv newenv
source newenv/bin/activate  # On Windows: newenv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Key
The system uses the **Groq API**. Ensure your API key is set in the environment in a .env file
```python
os.environ['GROQ_API_KEY'] = 'your_api_key_here'
```

### 4. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Optional: for admin access
```

### 5. Run Server
```bash
python manage.py runserver
```

---

## 📖 Usage Guide

1. **Home Page**: View your list of uploaded documents and study materials.
2. **Upload**: Use the Upload page to drag-and-drop files or paste a YouTube URL.
3. **Study Mode**:
   - Open any document to see the viewer and chat panel.
   - Use the **Generate** buttons to create Flashcards, MCQs, or Short Questions.
   - Highlight text in the viewer and use the "Explain" tooltip.
   - Chat with the bot in the right-hand sidebar.

---

## 📝 License
This project is part of a Final Year Project development. All rights reserved.
