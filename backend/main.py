from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import io
import json
import PyPDF2
import docx
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI application
app = FastAPI(title="AI Hub Backend API")

# Configure Cross-Origin Resource Sharing (CORS) 
# to allow frontend HTML files to fetch data from this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For local development. In production, restrict to your domain.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API keys from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SPEECH_API_KEY = os.getenv("SPEECH_API_KEY")

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
If unsure, return:
{"tasks": [], "error": "Please clarify your request"}
"""

# =========================
# INTENT DETECTION
# =========================

def detect_intent(user_input: str):
    try:
        prompt = MASTER_PROMPT.replace("<<USER_INPUT>>", user_input)

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )

        text = response.text.strip()

        # Try parsing JSON
        try:
            cleaned = text.strip().removeprefix('```json').removesuffix('```').strip()
            data = json.loads(cleaned)
            return data
        except:
            # Retry forcing JSON
            retry_prompt = prompt + "\nReturn ONLY valid JSON."
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=retry_prompt
            )
            retry_text = response.text.strip().removeprefix('```json').removesuffix('```').strip()
            return json.loads(retry_text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intent detection failed: {str(e)}")

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

def execute_tool(tool: str, user_input: str):
    if tool == "generate":
        return generate_text(user_input)

    elif tool == "generate-code":
        return generate_code(user_input)

    elif tool == "summarize":
        return summarize_text(user_input)

    elif tool == "translate":
        return translate_text(user_input)

    elif tool in ["analyze-image", "recognize-speech"]:
        return "This tool requires file input (Phase 2)"

    else:
        raise HTTPException(status_code=400, detail="Invalid tool")

# =========================
# MAIN ASSISTANT ENDPOINT
# =========================

@app.post("/api/assistant")
def assistant_handler(request: AssistantRequest):
    user_input = request.message

    # Step 1: Detect intent
    intent_data = detect_intent(user_input)

    # Validate response
    if "tasks" not in intent_data or len(intent_data["tasks"]) == 0:
        return {
            "error": "Please clarify your request"
        }

    task = intent_data["tasks"][0]
    tool = task.get("tool")

    if not tool:
        return {
            "error": "Invalid task structure"
        }

    # Step 2: Execute tool
    try:
        result = execute_tool(tool, user_input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Step 3: Return response
    return {
        "tool_used": tool,
        "result": result
    }

if __name__ == "__main__":
    import uvicorn
    # Start the local development server at http://localhost:8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
