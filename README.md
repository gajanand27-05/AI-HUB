# AI Hub

AI Hub is a multimodal intelligence platform designed to handle diverse tasks including document extraction, vision analysis, speech processing, and intelligent task orchestration. Built with a modern, glassmorphic UI, it provides a seamless and high-performance user experience.

## 🚀 Features

- **Circular Hub Interface:** A unique, interactive UI for navigating AI capabilities.
- **Multimodal Intelligence:** 
  - PDF and DOCX text extraction.
  - Image analysis and vision capabilities.
  - Speech-to-text and intent recognition.
- **AI Assistant:** Powered by Google Gemini 2.5 Flash for advanced reasoning and task execution.
- **Task Orchestration:** Step-by-step rendering of complex AI workflows.
- **Secure Authentication:** JWT-based login system with SQLite-backed session history.
- **Premium UX:** High-quality glassmorphism effects, interactive animations, and syntax highlighting via Prism.js.

## 🛠️ Tech Stack

### Frontend
- **Framework:** React (Vite-based)
- **Styling:** Vanilla CSS (Glassmorphism)
- **Utilities:** Prism.js for code highlighting.

### Backend
- **Framework:** FastAPI (Python)
- **Server:** Uvicorn
- **AI Core:** Google Gemini 2.5 Flash
- **Database:** SQLite (aiosqlite)
- **Security:** PyJWT, Passlib (Bcrypt)
- **Document Processing:** PyPDF2, python-docx, Pillow

## 📂 Project Structure

- `backend/`: FastAPI application, authentication logic, database models, and AI integration.
- `frontend/`: React-based interactive UI.
- `docs/`: Detailed project phases and documentation summaries.

## ⚙️ Installation & Setup

### Backend Setup
1. Navigate to the `backend` directory.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure your environment variables in a `.env` file (e.g., Gemini API keys).
5. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup
1. Navigate to the `frontend` directory.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## 📜 Roadmap

- **Phase 1:** Foundation & Design (UI Core, Circular Hub)
- **Phase 2:** Multimodal Intelligence (Extraction, Vision, Speech)
- **Phase 3:** Task Orchestration (AI Assistant, Intent Pipelining)
- **Phase 4:** Production & Memory (Auth, History, Premium UX)


