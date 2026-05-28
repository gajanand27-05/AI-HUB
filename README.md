# <p align="center">✨ AI HUB — Multimodal Intelligence Platform ✨</p>

<p align="center">
  <img src="https://img.shields.io/badge/AI-Gemini%202.5%20Flash-blueviolet?style=for-the-badge&logo=google-gemini" alt="Gemini">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB?style=for-the-badge&logo=react" alt="React">
  <img src="https://img.shields.io/badge/Database-SQLite-003B57?style=for-the-badge&logo=sqlite" alt="SQLite">
</p>

<p align="center">
  <strong>The ultimate AI orchestration engine with a futuristic Glassmorphic UI.</strong>
  <br />
  <i>Empower your workflow with Vision, Speech, and Intelligent Task Pipelining.</i>
</p>

---

## 🌌 Project Overview

**AI Hub** is not just another chatbot. It is a high-performance **Multimodal Intelligence Platform** designed to handle diverse tasks through a unique **Circular Hub Interface**. Built with a focus on aesthetics and power, it uses **Google Gemini 2.5 Flash** to reason across text, images, and audio seamlessly.

### 🎯 Key Highlights
- **🎭 Glassmorphic UI:** A premium, translucent interface with interactive 3D-effect nodes.
- **🔄 Intent Pipelining:** Ask complex questions; AI Hub breaks them down into executable tasks.
- **📸 Vision Analysis:** Extract deep insights from images instantly.
- **🎙️ Live Transcription:** Real-time speech-to-text with a built-in terminal UI.
- **📑 Document Intelligence:** Instant summaries for PDF, DOCX, and Markdown files.

---

## 🚀 Interactive Features

### 🎡 The Circular Hub
A rotating, interactive dashboard where AI capabilities orbit a central core. Each "node" is a specialized tool:
1. **AI Assist Chatbot:** General reasoning and conversation.
2. **Text Generator:** High-quality creative and technical writing.
3. **AI Summarizer:** Surgical extraction of data from documents.
4. **Code Generator:** Expert-level code snippets with syntax highlighting.
5. **Image Analyzer:** Detailed visual description and object detection.
6. **Speech Recognition:** Native audio processing.
7. **Language Translator:** Polyglot support for global communication.

### 🧠 Smart Orchestration
The "Master Assistant" acts as a conductor. If you say: *"Explain this image and translate the summary to Kannada,"* AI Hub automatically:
1. Triggers **Vision Analysis**.
2. Passes the output to the **Summarizer**.
3. Feeds the final result into the **Translator**.

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React, Vite, Vanilla CSS (Glassmorphism), Prism.js |
| **Backend** | FastAPI (Python), Uvicorn, genai SDK |
| **AI Models** | Google Gemini 2.5 Flash (Multimodal) |
| **Persistence** | SQLite (aiosqlite), JWT Authentication |
| **Processing** | PyPDF2, python-docx, Pillow |

---

## ⚙️ Installation & Setup

### 📦 Prerequisites
- Python 3.9+
- Node.js & npm
- Gemini API Key ([Get it here](https://aistudio.google.com/))

### 🔧 Backend Configuration
1. Clone the repo and navigate to `backend/`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file:
   ```env
   GEMINI_API_KEY=your_api_key_here
   JWT_SECRET=your_secure_secret
   ```
4. Start the engine:
   ```bash
   uvicorn main:app --reload
   ```

### 🎨 Frontend Configuration
1. Navigate to `frontend/`.
2. Install packages:
   ```bash
   npm install
   ```
3. Launch the dashboard:
   ```bash
   npm run dev
   ```

---

## 🤝 Connect with the Developer

Developed with ❤️ by **Gajanand Dhayagode**.

- **GitHub:** [@gajanand27-05](https://github.com/gajanand27-05)
- **Email:** [gajanandvd2005@gmail.com](mailto:gajanandvd2005@gmail.com)
- **Project Link:** [AI-HUB Repository](https://github.com/gajanand27-05/AI-HUB)

---

<p align="center">
  <i>"Building the future of AI orchestration, one node at a time."</i>
</p>
