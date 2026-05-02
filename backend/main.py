from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import io
import json
import re
import logging
import PyPDF2
import docx
from google import genai
from google.genai import types
from database import init_db, get_db
from auth import (
    SignupRequest, LoginRequest, TokenResponse,
    hash_password, verify_password, create_token, get_current_user
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_hub")

# Load environment variables from .env file
# We look in the current folder, and the parent folder to be safe
env_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
    ".env"
]
for path in env_paths:
    if os.path.exists(path):
        load_dotenv(path, override=True)
        logger.info(f"Loaded environment from {path}")
        break

# Initialize FastAPI application
app = FastAPI(title="AI Hub Backend API")

# Global Exception Handler to catch internal errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
    )

# Initialize database on startup
@app.on_event("startup")
async def startup():
    await init_db()
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("CRITICAL: GEMINI_API_KEY not found in environment!")
    else:
        logger.info("Database and AI Core initialized successfully")

# Configure Cross-Origin Resource Sharing (CORS) 
# to allow frontend HTML files to fetch data from this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SPEECH_API_KEY = os.getenv("SPEECH_API_KEY")

# Some Google SDKs prefer GOOGLE_API_KEY
if GEMINI_API_KEY:
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
    logger.info(f"GEMINI_API_KEY loaded successfully (Length: {len(GEMINI_API_KEY)})")
else:
    logger.error("GEMINI_API_KEY NOT FOUND IN ENVIRONMENT")

# Initialize the Gemini Client
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Failed to intialize Gemini client: {e}")
    client = None

# Initialize a separate Gemini Client specifically for Speech-To-Text
try:
    speech_client = genai.Client(api_key=SPEECH_API_KEY)
except Exception as e:
    print(f"Failed to intialize Speech Gemini client: {e}")
    speech_client = None

# Pydantic models for request validation
class GenerateRequest(BaseModel):
    prompt: str

class TranslateRequest(BaseModel):
    text: str
    source_language: str
    target_language: str

class AssistantRequest(BaseModel):
    message: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

# =========================
# AUTH ENDPOINTS
# =========================

@app.post("/api/signup")
async def signup(request: SignupRequest):
    db = await get_db()
    try:
        # Check if user exists
        cursor = await db.execute("SELECT id FROM users WHERE email = ?", (request.email,))
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        cursor = await db.execute("SELECT id FROM users WHERE username = ?", (request.username,))
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create user
        hashed = hash_password(request.password)
        cursor = await db.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (request.username, request.email, hashed)
        )
        await db.commit()
        user_id = cursor.lastrowid
        
        token = create_token(user_id, request.username)
        logger.info(f"New user registered: {request.username}")
        return {"token": token, "username": request.username}
    finally:
        await db.close()

@app.post("/api/login")
async def login(request: LoginRequest):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, username, password_hash FROM users WHERE email = ?",
            (request.email,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user_id, username, password_hash = row[0], row[1], row[2]
        if not verify_password(request.password, password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token = create_token(user_id, username)
        logger.info(f"User logged in: {username}")
        return {"token": token, "username": username}
    finally:
        await db.close()

# =========================
# HEALTH CHECK
# =========================

@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "model": "gemini-2.5-flash",
        "client_ready": client is not None
    }

# =========================
# HISTORY ENDPOINT
# =========================

@app.get("/api/history")
async def get_history(user: dict = Depends(get_current_user)):
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT prompt, tools_used, response, created_at FROM history WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
            (user["user_id"],)
        )
        rows = await cursor.fetchall()
        history = []
        for row in rows:
            history.append({
                "prompt": row[0],
                "tools_used": row[1],
                "response": row[2],
                "created_at": row[3]
            })
        return {"history": history}
    finally:
        await db.close()

@app.post("/api/generate")
async def generate_text(request: GenerateRequest):
    if not client:
        raise HTTPException(status_code=500, detail="AI Client not properly initialized.")
        
    try:
        # Generate text using the Gemini 2.5 Flash model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=request.prompt,
            config=types.GenerateContentConfig(
                 temperature=0.7,
            )
        )
        return {"status": "success", "response": response.text}
        
    except Exception as e:
        # In case the API key is strictly restricted or invalid
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-code")
async def generate_code(request: GenerateRequest):
    if not client:
        raise HTTPException(status_code=500, detail="AI Client not properly initialized.")
        
    try:
        system_prompt = f"You are an expert software developer. Provide the optimal code snippet to solve the following prompt. Always use markdown code blocks (```language) to format your code. Keep conversational text to a minimum inside your response.\n\nPrompt: {request.prompt}"
        
        # Generate text using the Gemini 2.5 Flash model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt,
            config=types.GenerateContentConfig(
                 temperature=0.2, # Lower temperature for strictly formatted code
            )
        )
        return {"status": "success", "response": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/summarize")
async def summarize_file(file: UploadFile = File(...)):
    if not client:
        raise HTTPException(status_code=500, detail="AI Client not properly initialized.")
        
    try:
        extracted_text = ""
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # Read file content into memory
        content = await file.read()
        
        # Parse text based on file type
        if file_extension == '.pdf':
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
        elif file_extension == '.docx':
            doc = docx.Document(io.BytesIO(content))
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"
        elif file_extension in ['.txt', '.md']:
            extracted_text = content.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .txt, .md, .pdf, or .docx")

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any text from the file. It might be empty or scanned.")

        # Construct the summarization prompt
        prompt = f"Please provide a comprehensive summary of the following document:\n\n{extracted_text}"
        
        # Call Gemini
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                 temperature=0.7,
            )
        )
        return {"status": "success", "response": response.text, "filename": file.filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    if not client:
        raise HTTPException(status_code=500, detail="AI Client not properly initialized.")
        
    try:
        # Read the raw byte data from the uploaded image
        content = await file.read()
        
        # Determine MIME type based on extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        mime_type = "image/jpeg" # Default
        if file_extension in ['.png']:
            mime_type = "image/png"
        elif file_extension in ['.webp']:
            mime_type = "image/webp"
            
        # Instruct the model what to look for
        prompt = "You are an advanced Image Analyzer. Analyze the attached image in detail. Specifically look for and describe: \n1) Any persons present (estimate gender, describe their clothing, and note colors)\n2) Any animals present (identify their species/type)\n3) Detect and list the prominent objects in the scene. \n\nProvide your analysis in a clear, well-structured format with bullet points."
        
        # Package the raw bytes for the SDK
        image_part = types.Part.from_bytes(
            data=content,
            mime_type=mime_type,
        )
        
        # Call Gemini 2.5 Flash Vision capabilities
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image_part, prompt]
        )
        
        return {"status": "success", "response": response.text, "filename": file.filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recognize-speech")
async def recognize_speech(file: UploadFile = File(...)):
    if not speech_client:
        raise HTTPException(status_code=500, detail="Speech AI Client not properly initialized.")
        
    try:
        # Read the raw byte data from the uploaded audio file
        content = await file.read()
        
        # Audio from the web browser is typically .webm format
        mime_type = "audio/webm" 
        
        # Instruct the model to perform transcription
        prompt = "You are an expert transcriptionist. Transcribe the following audio accurately. Output ONLY the raw transcribed text. DO NOT output JSON, DO NOT use markdown blocks, DO NOT include any conversational filler. Just the direct text of the transcription. If there is no speech, output nothing."
        
        # Package the raw bytes for the SDK
        audio_part = types.Part.from_bytes(
            data=content,
            mime_type=mime_type,
        )
        
        # Call Gemini 2.5 Flash native audio capabilities
        response = speech_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[audio_part, prompt]
        )
        
        return {"status": "success", "response": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/translate")
async def translate_text(request: TranslateRequest):
    if not client:
        raise HTTPException(status_code=500, detail="AI Client not properly initialized.")
        
    try:
        system_prompt = f"You are an expert polyglot translator. Translate the following text from {request.source_language} to {request.target_language}. Provide ONLY the translated text without any conversational filler, explanations, or quotes around it.\n\nText to translate:\n{request.text}"
        
        # Generate text using the Gemini 2.5 Flash model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_prompt,
            config=types.GenerateContentConfig(
                 temperature=0.3, # Lower temperature for translation accuracy
            )
        )
        return {"status": "success", "response": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# MASTER PROMPT
# =========================

MASTER_PROMPT = """
You are an AI system that analyzes user requests and converts them into structured JSON tasks for an AI orchestration platform called "AI Hub".

Your job is to:
1. Understand the user's intent
2. Break the request into one or more tasks
3. Map each task to the correct tool
4. Return ONLY valid JSON (no explanation, no extra text)

---
AVAILABLE TOOLS:

1. "generate" -> for general text generation, explanations, writing
2. "generate-code" -> for programming, code generation, debugging
3. "summarize" -> for summarizing documents or long text
4. "analyze-image" -> for describing or analyzing images
5. "recognize-speech" -> for converting audio to text
6. "translate" -> for language translation (Always include target language in description. Detect language automatically if not specified)

---
RULES:

* Always return JSON in this format:
  {
  "tasks": [
  {
  "tool": "tool-name",
  "input": "text | file | previous_output",
  "description": "short explanation of task"
  }
  ]
  }

* If multiple actions are requested, split into multiple tasks in correct order. Tasks must be ordered logically based on dependency. Example: speech -> text -> summarize (NOT reverse)
* Use "previous_output" when a task depends on the result of a previous task. If output of one task is required for another, ALWAYS use "previous_output". Example: Explain this image and translate to Hindi -> analyze-image (file) -> translate (previous_output)
* Use "file" ONLY if user explicitly mentions upload, image, audio, or document
* Otherwise always use "text"
* You MUST only use tools from this exact list:
  ["generate", "generate-code", "summarize", "analyze-image", "recognize-speech", "translate"]
* If a request does not match any tool, return error JSON.

---
EDGE CASE HANDLING:

* If request is unclear:
  {
  "tasks": [],
  "error": "Please clarify your request"
  }

* If request is unsupported:
  {
  "tasks": [],
  "error": "This request is outside current capabilities"
  }

---
EXAMPLES:

User: "Summarize this PDF and generate Python code"
Output:
{
"tasks": [
{
"tool": "summarize",
"input": "file",
"description": "Summarize the uploaded document"
},
{
"tool": "generate-code",
"input": "previous_output",
"description": "Generate Python code based on the summary"
}
]
}

User: "Translate this text to Hindi"
Output:
{
"tasks": [
{
"tool": "translate",
"input": "text",
"description": "Translate text to Hindi"
}
]
}

User: "Explain this image"
Output:
{
"tasks": [
{
"tool": "analyze-image",
"input": "file",
"description": "Analyze and describe the image"
}
]
}

User: "Convert this speech to text and summarize it"
Output:
{
"tasks": [
{
"tool": "recognize-speech",
"input": "file",
"description": "Convert speech to text"
},
{
"tool": "summarize",
"input": "previous_output",
"description": "Summarize the transcribed text"
}
]
}

---
IMPORTANT:

* Do NOT return explanations
* Do NOT return markdown
* Do NOT return text outside JSON
* Ensure JSON is valid and parseable

---
Now analyze the following user input and return JSON:

USER INPUT:
"<<USER_INPUT>>"

STRICT RULE:
Return ONLY valid JSON.
Do NOT include explanations, markdown, comments, or extra text.
Wrap your JSON output strictly between:
BEGIN_JSON
{ ... }
END_JSON
If unsure, return:
{"tasks": [], "error": "Please clarify your request"}
"""

# =========================
# INTENT DETECTION
# =========================

def extract_json(text: str):
    # Preferred: sentinel markers
    match = re.search(r'BEGIN_JSON\s*(\{.*?\})\s*END_JSON', text, re.DOTALL)
    if match:
        return match.group(1)

    # Fallback: first valid JSON object
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0)

    raise ValueError("No JSON found")

def detect_intent(user_input: str):
    prompt = MASTER_PROMPT.replace("<<USER_INPUT>>", user_input)
    MAX_RETRIES = 2
    
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            clean_text = extract_json(response.text)
            return json.loads(clean_text)
        except Exception:
            if attempt == MAX_RETRIES - 1:
                raise HTTPException(status_code=500, detail="Failed to parse model response")
            # Retry prompting
            prompt += "\nReturn ONLY valid JSON."

# =========================
# TOOL EXECUTION FUNCTIONS
# =========================

def generate_text(prompt: str):
    return client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    ).text

def generate_code(prompt: str):
    code_prompt = f"Generate clean code for:\n{prompt}"
    return client.models.generate_content(
        model='gemini-2.5-flash',
        contents=code_prompt
    ).text

def summarize_text(prompt: str):
    summary_prompt = f"Summarize this:\n{prompt}"
    return client.models.generate_content(
        model='gemini-2.5-flash',
        contents=summary_prompt
    ).text

def translate_text(prompt: str):
    return client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    ).text

# =========================
# TOOL ROUTER
# =========================

def execute_tool(tool: str, input_data: str):
    if tool == "generate":
        return generate_text(input_data)

    elif tool == "generate-code":
        return generate_code(input_data)

    elif tool == "summarize":
        return summarize_text(input_data)

    elif tool == "translate":
        return translate_text(input_data)

    elif tool in ["analyze-image", "recognize-speech"]:
        return "This tool requires file input (Phase 2)"

    else:
        raise HTTPException(status_code=400, detail="Invalid tool")

# =========================
# MULTI-STEP EXECUTION ENGINE
# =========================

def execute_tasks(tasks, user_input):
    context = {}
    results = []

    for index, task in enumerate(tasks):
        tool = task.get("tool")
        input_type = task.get("input")

        # Decide input source
        if input_type == "text":
            input_data = user_input

        elif input_type == "previous_output":
            input_data = context.get("last_output", "")
            if not input_data:
                return {"error": f"Step {index+1} requires previous output, but none is available"}

        else:
            return {"error": f"Unsupported input type: {input_type}"}

        # Execute tool
        try:
            output = execute_tool(tool, input_data)
        except Exception as e:
            return {"error": f"Execution failed at step {index+1}: {str(e)}"}

        # Store output
        context["last_output"] = output

        # Save step result
        results.append({
            "step": index + 1,
            "tool": tool,
            "output": output
        })

    return {
        "steps": results,
        "final_output": context.get("last_output", "")
    }

# =========================
# SMART SUGGESTIONS
# =========================

def get_suggestions(tools_used):
    """Generate contextual follow-up suggestions based on tools that were executed."""
    suggestions = []
    tool_set = set(tools_used)
    
    if "summarize" in tool_set and "translate" not in tool_set:
        suggestions.append("Translate this summary to another language")
    if "summarize" in tool_set and "generate-code" not in tool_set:
        suggestions.append("Generate code based on this summary")
    if "generate" in tool_set and "translate" not in tool_set:
        suggestions.append("Translate this text")
    if "generate-code" in tool_set:
        suggestions.append("Explain this code in simple terms")
    if "translate" in tool_set:
        suggestions.append("Summarize the translated text")
    if "analyze-image" in tool_set:
        suggestions.append("Generate code based on this analysis")
    
    if not suggestions:
        suggestions = ["Try another prompt", "Summarize a document", "Generate some code"]
    
    return suggestions[:3]

# =========================
# MAIN ASSISTANT ENDPOINT
# =========================

@app.post("/api/assistant")
async def assistant_handler(
    request: AssistantRequest,
    debug: bool = Query(False),
    user: dict = Depends(get_current_user)
):
    user_input = request.message
    
    # Input validation
    if len(user_input) > 5000:
        return {"error": "Message too long. Maximum 5000 characters allowed."}
    
    if not user_input.strip():
        return {"error": "Please enter a message."}

    logger.info(f"Assistant request from user {user['username']}: {user_input[:100]}...")

    intent_data = detect_intent(user_input)

    if "error" in intent_data:
        return intent_data

    tasks = intent_data.get("tasks", [])

    if not tasks:
        return {"error": "Please clarify your request"}

    # Execute multi-step tasks
    result = execute_tasks(tasks, user_input)
    
    # Collect tools used for suggestions and history
    tools_used = []
    if "steps" in result:
        tools_used = [step["tool"] for step in result["steps"]]
    
    # Add smart suggestions
    result["suggestions"] = get_suggestions(tools_used)
    
    # Add debug info if requested
    if debug:
        result["debug"] = {
            "raw_intent": intent_data,
            "user_id": user["user_id"]
        }
    
    # Store in history
    try:
        db = await get_db()
        await db.execute(
            "INSERT INTO history (user_id, prompt, tools_used, response) VALUES (?, ?, ?, ?)",
            (
                user["user_id"],
                user_input,
                json.dumps(tools_used),
                json.dumps(result.get("final_output", ""))
            )
        )
        await db.commit()
        await db.close()
        logger.info(f"History saved for user {user['username']}")
    except Exception as e:
        logger.error(f"Failed to save history: {str(e)}")

    return result

# =========================
# CONVERSATIONAL CHATBOT
# =========================

@app.post("/api/chat")
async def chat_handler(
    request: ChatRequest,
    user: dict = Depends(get_current_user)
):
    if not client:
        raise HTTPException(status_code=503, detail="Gemini AI client not initialized")
    
    user_input = request.message
    history = request.history

    if not user_input.strip():
        return {"error": "Please enter a message."}

    logger.info(f"Chat request from user {user['username']}: {user_input[:50]}...")

    try:
        # Convert Pydantic history objects to Gemini format
        # Gemini expects roles: 'user' and 'model'
        gemini_history = []
        for msg in history:
            role = "user" if msg.role == "user" else "model"
            gemini_history.append({"role": role, "parts": [{"text": msg.content}]})

        # Start a chat session with the provided history
        chat_session = client.chats.create(
            model="gemini-2.5-flash",
            history=gemini_history
        )

        # Send the user's message and get a response
        response = chat_session.send_message(user_input)
        
        return {
            "status": "success",
            "response": response.text
        }

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return {"error": f"Failed to get response from AI: {str(e)}"}

# =========================
# SERVE FRONTEND
# =========================

# Resolve the absolute path to the frontend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

# Mount the frontend directory to serve static files (HTML, CSS, JS)
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    logger.error(f"Frontend directory not found at {FRONTEND_DIR}")

if __name__ == "__main__":
    import uvicorn
    # Start the local development server at http://0.0.0.0:8000
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

