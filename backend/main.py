from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
import openai
import google.generativeai as genai
import os
import logging
import datetime
import json
import asyncio
import re

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AgentForge API",
    description="AI-powered code generation API supporting OpenAI and Gemini",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for structured input
class AppGenerationRequest(BaseModel):
    app_name: str = Field(..., description="Name of the application to generate")
    features: List[str] = Field(..., description="List of features for the application")
    app_type: str = Field(default="streamlit", description="Type of application (e.g., 'react', 'vue', 'python-cli')")
    description: Optional[str] = Field(None, description="Additional description or requirements")

class CodeGenerationResponse(BaseModel):
    success: bool
    generated_code: Optional[str] = None
    error: Optional[str] = None
    app_name: str
    features: List[str]
    ai_provider: str

# Legacy endpoint for simple prompts (keeping for compatibility)
class Prompt(BaseModel):
    text: str

def get_ai_provider():
    """Get the current AI provider from environment"""
    return os.getenv("AI_PROVIDER", "gemini").lower()

def setup_ai_clients():
    """Setup and validate AI clients"""
    provider = get_ai_provider()
    
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        openai.api_key = api_key
        return "openai"
    
    elif provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        genai.configure(api_key=api_key)
        return "gemini"
    
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")

def create_meta_prompt(request: AppGenerationRequest) -> str:
    """
    Creates a detailed, structured meta-prompt for the LLM to generate a full project structure.
    The prompt instructs the model to return a single JSON object representing the file tree.
    """
    
    # Enhanced instructions for various app types
    app_type_details = {
        "react": "A modern React application using functional components, hooks, and a clear component hierarchy. Include a basic build setup (e.g., using Vite or Create React App structure).",
        "vue": "A Vue.js application using Single File Components (SFCs), a proper component structure, and Vue Router for navigation if multiple views are needed.",
        "streamlit": "A multi-page Streamlit application with a clear structure. Use a `pages/` directory for different pages and a main script to tie everything together. Ensure all necessary libraries are imported. The main script should have content and functionality visible when run.",
        "flask": "A well-structured Flask application with blueprints for modularity, a `templates/` directory for HTML files, and a `static/` directory for assets. Include a `requirements.txt` file. ALWAYS include a root route (`@app.route('/')`) that renders a page or returns content.",
        "fastapi": "A robust FastAPI application using APIRouter for modular endpoints, Pydantic models for validation, and a clear separation of concerns. Include a `requirements.txt` file. ALWAYS include a root route (`@app.get('/')`) that returns a welcome message or serves an HTML page.",
        "python-cli": "A Python command-line interface application using `argparse` or a library like `click` for argument parsing. Structure the code into logical modules.",
        "nextjs": "A Next.js application with a proper `pages` or `app` directory structure, API routes if needed, and components organized logically. Include necessary configurations like `tailwind.config.js` if applicable."
    }
    
    app_guidance = app_type_details.get(request.app_type.lower(), "A well-structured application of the specified type.")
    
    features_text = "\n".join([f"- {feature}" for feature in request.features])
    prompt = f"""
You are an expert software architect and senior developer. Your task is to generate a complete, production-ready project structure for an application based on the user's request.

Your output MUST be a single, valid JSON object. This JSON object must represent the entire file system tree of the project. Do not include any explanatory text before or after the JSON object.

JSON Structure Rules:
- The root of the JSON should be a single object representing the project's root folder (e.g., "{request.app_name}/").
- Keys represent file or folder names.
- Folder names MUST end with a forward slash (`/`).
- File names MUST NOT end with a forward slash.
- The value for a folder is another JSON object representing its children.
- The value for a file is a single string containing the complete, well-formatted, and production-quality code for that file.

User Request:
- Application Name: "{request.app_name}"
- Application Type: "{request.app_type}"
- Core Features:
{features_text}
- Detailed Description: "{request.description or 'No additional description provided.'}"

Project Guidance:
- {app_guidance}
- **Crucially, you MUST include a package manager manifest file.** For Python projects (like Flask, FastAPI, Streamlit), this MUST be a `requirements.txt` file. For Node.js projects (like React, Next.js, Vue), this MUST be a `package.json` file.
- **You MUST also include a `README.md` file.** This file should provide clear, simple instructions on how to set up the project (e.g., `pip install -r requirements.txt` or `npm install`) and how to run it (e.g., `streamlit run app.py` or `npm run dev`).
- **Ensure the application has a functional root/home page.** For web frameworks (Flask, FastAPI), always include a root route that displays content. For frontend frameworks (React, Vue), ensure there's a proper index/home component.
- Generate all necessary files, including configuration, source code, and the required `README.md`.
- The code should be robust, follow best practices for the specified technology, and be ready for development.
- Ensure the generated code directly implements the requested features.

Example of the required JSON output format:
```json
{{
  "my-cool-app/": {{
    "src/": {{
      "index.js": "console.log('Hello, World!');",
      "styles.css": "body {{ margin: 0; }}"
    }},
    "public/": {{
      "index.html": "<html>...</html>"
    }},
    "package.json": "{{ \"name\": \"my-cool-app\", \"version\": \"1.0.0\" }}"
  }}
}}

Now, generate the complete project structure as a single JSON object for the user's request.
"""
    return prompt

async def generate_with_openai(meta_prompt: str) -> str:
    """Generate code using OpenAI API"""
    model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {
                "role": "system", 
                "content": "You are an expert software engineer who generates complete, production-ready applications."
            },
            {
                "role": "user", 
                "content": meta_prompt
            }
        ],
        max_tokens=4000,
        temperature=0.7,
    )
    
    return response.choices[0].message.content.strip()

async def generate_with_gemini(meta_prompt: str) -> str:
    """Generate code using Gemini API"""
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    
    # Create the model
    model = genai.GenerativeModel(model_name)
    
    # Create the prompt with system instruction
    full_prompt = f"""You are an expert software engineer who generates complete, production-ready applications.

{meta_prompt}"""
    
    # Generate content
    response = model.generate_content(
        full_prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=4000,
            temperature=0.7,
        )
    )
    
    return response.text.strip()

async def generate_with_gemini_stream(meta_prompt: str):
    """Generate code using Gemini API with streaming."""
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)
    
    response_stream = model.generate_content(meta_prompt, stream=True)
    
    for chunk in response_stream:
        if chunk.text:
            yield chunk.text

async def generate_with_openai_stream(meta_prompt: str):
    """Generate code using OpenAI API with streaming."""
    model = os.getenv("OPENAI_MODEL", "gpt-4")
    
    response_stream = await openai.ChatCompletion.acreate(
        model=model,
        messages=[
            {
                "role": "system", 
                "content": "You are an expert software engineer who generates complete, production-ready applications."
            },
            {
                "role": "user", 
                "content": meta_prompt
            }
        ],
        max_tokens=4000,
        temperature=0.7,
        stream=True
    )
    
    async for chunk in response_stream:
        content = chunk.choices[0].delta.get('content', '')
        if content:
            yield content

def save_generated_code(generated_code: str, app_name: str, app_type: str, provider: str):
    """Save generated code to the proper directory structure"""
    
    # Create the base directory path
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_apps")
    app_type_dir = os.path.join(base_dir, app_type)
    
    # Ensure the directory exists
    os.makedirs(app_type_dir, exist_ok=True)
    
    # Create filename with timestamp for uniqueness
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{app_name}_{provider}_{timestamp}.py"
    
    # Handle different file extensions based on app type
    if app_type == "streamlit":
        filename = f"{app_name}_{provider}_{timestamp}.py"
    elif app_type == "flask":
        filename = f"{app_name}_{provider}_{timestamp}.py"
    elif app_type == "fastapi":
        filename = f"{app_name}_{provider}_{timestamp}.py"
    
    file_path = os.path.join(app_type_dir, filename)
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(generated_code)
        logger.info(f"Generated code saved to: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save generated code: {e}")

@app.post("/generate", response_model=CodeGenerationResponse)
async def generate_code(request: AppGenerationRequest):
    """Generate complete application code based on structured requirements"""
    
    try:
        # Setup AI client
        provider = setup_ai_clients()
        
        # Create the meta-prompt
        meta_prompt = create_meta_prompt(request)
        
        # Generate code based on provider
        if provider == "openai":
            generated_code = await generate_with_openai(meta_prompt)
        elif provider == "gemini":
            generated_code = await generate_with_gemini(meta_prompt)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        # Save the generated code to the proper directory
        save_generated_code(generated_code, request.app_name, request.app_type, provider)
        
        return CodeGenerationResponse(
            success=True,
            generated_code=generated_code,
            app_name=request.app_name,
            features=request.features,
            ai_provider=provider
        )
        
    except Exception as e:
        provider = get_ai_provider()
        return CodeGenerationResponse(
            success=False,
            error=f"Code generation failed ({provider}): {str(e)}",
            app_name=request.app_name,
            features=request.features,
            ai_provider=provider
        )

@app.post("/generate-simple")
async def generate_simple(prompt: Prompt):
    """Legacy endpoint for simple prompt-based generation"""
    try:
        provider = setup_ai_clients()
        
        if provider == "openai":
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt.text}],
                max_tokens=1000,
            )
            content = response.choices[0].message.content
            
        elif provider == "gemini":
            model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt.text)
            content = response.text
            
        return {"message": content, "provider": provider}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/generate_project_stream")
async def generate_project_stream(request: AppGenerationRequest):
    """Generates a complete project structure and streams file system events."""
    try:
        provider = setup_ai_clients()
        meta_prompt = create_project_structure_prompt(request)
        
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_apps")
        os.makedirs(base_dir, exist_ok=True)

        async def event_generator():
            if provider == "openai":
                generator = generate_with_openai_stream(meta_prompt)
            elif provider == "gemini":
                generator = generate_with_gemini_stream(meta_prompt)
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            # This is a simplified model. We're buffering the whole JSON.
            # A more advanced implementation would parse the JSON stream itself.
            full_response = ""
            async for chunk in generator:
                full_response += chunk
            
            # Clean the response to ensure it's valid JSON
            # Find the first '{' and the last '}'
            start_index = full_response.find('{')
            end_index = full_response.rfind('}')
            if start_index != -1 and end_index != -1:
                json_string = full_response[start_index:end_index+1]
                try:
                    project_structure = json.loads(json_string)
                    
                    async def traverse_and_yield(structure, current_path):
                        for name, content in structure.items():
                            # Construct the relative path for the event
                            relative_path = os.path.join(current_path, name).replace(os.sep, '/')
                            
                            if isinstance(content, dict):
                                yield f"data: {json.dumps({'type': 'log', 'message': f'Creating folder: {relative_path}'})}\n\n"
                                await asyncio.sleep(0.01)
                                yield f"data: {json.dumps({'type': 'create_folder', 'path': relative_path})}\n\n"
                                await asyncio.sleep(0.05)
                                async for event in traverse_and_yield(content, relative_path):
                                    yield event
                            else:
                                yield f"data: {json.dumps({'type': 'log', 'message': f'Creating file: {relative_path}'})}\n\n"
                                await asyncio.sleep(0.01)
                                yield f"data: {json.dumps({'type': 'create_file', 'path': relative_path, 'content': content})}\n\n"
                                await asyncio.sleep(0.05)

                    # The root of the project is the first key in the JSON
                    root_folder_name = list(project_structure.keys())[0]
                    yield f"data: {json.dumps({'type': 'log', 'message': f'Starting project generation for: {root_folder_name}'})}\n\n"
                    await asyncio.sleep(0.01)
                    async for event in traverse_and_yield(project_structure, ''):
                        yield event
                    yield f"data: {json.dumps({'type': 'log', 'message': 'Project generation complete.'})}\n\n"
                    await asyncio.sleep(0.01)

                except json.JSONDecodeError as e:
                    logger.error(f"JSON Decode Error: {e}")
                    yield f"data: {json.dumps({'type': 'log', 'message': 'Error: Failed to decode project structure from AI response.'})}\n\n"
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to decode project structure from AI response.'})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'log', 'message': 'Error: Invalid project structure format from AI.'})}\n\n"
                yield f"data: {json.dumps({'type': 'error', 'message': 'Invalid project structure format from AI.'})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Project generation stream failed: {e}")
        return StreamingResponse(f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n", media_type="text/event-stream")

@app.post("/generate_stream")
async def generate_code_stream(request: AppGenerationRequest):
    """Generate complete application code based on structured requirements with streaming."""
    
    try:
        provider = setup_ai_clients()
        meta_prompt = create_meta_prompt(request)

        async def stream_generator():
            if provider == "openai":
                generator = generate_with_openai_stream(meta_prompt)
            elif provider == "gemini":
                generator = generate_with_gemini_stream(meta_prompt)
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            async for chunk in generator:
                yield f"data: {json.dumps({'token': chunk})}\n\n"
                await asyncio.sleep(0.01) # Small delay to allow client to process
            
            # Signal end of stream
            yield f"data: {json.dumps({'status': 'done'})}\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Streaming code generation failed: {e}")
        # This error won't be sent to the client as the response headers are already sent.
        # Proper error handling for streaming endpoints is more complex.
        # For now, we log it.
        return StreamingResponse(f"data: {json.dumps({'error': str(e)})}\n\n", media_type="text/event-stream")

@app.get("/")
async def read_root():
    """Health check endpoint"""
    provider = get_ai_provider()
    return {
        "message": "AgentForge backend is running",
        "version": "1.0.0",
        "ai_provider": provider,
        "endpoints": {
            "generate": "/generate - Main code generation endpoint",
            "generate_simple": "/generate-simple - Simple prompt endpoint",
            "docs": "/docs - API documentation"
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    provider = get_ai_provider()
    
    if provider == "openai":
        api_configured = bool(os.getenv("OPENAI_API_KEY"))
        model = os.getenv("OPENAI_MODEL", "gpt-4")
    elif provider == "gemini":
        api_configured = bool(os.getenv("GEMINI_API_KEY"))
        model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    else:
        api_configured = False
        model = "unknown"
    
    return {
        "status": "healthy",
        "ai_provider": provider,
        "api_configured": api_configured,
        "model": model
    }

# Pydantic model for project structure request
class ProjectStructureRequest(BaseModel):
    app_name: str = Field(..., description="Name of the application")
    app_type: str = Field(default="streamlit", description="Type of application (streamlit, flask, fastapi)")
    description: Optional[str] = Field(None, description="Additional description or requirements")

def create_project_structure_prompt(request: AppGenerationRequest) -> str:
    """Create a detailed meta-prompt for the LLM to generate a project structure as JSON."""
    
    app_type_instructions = {
        "streamlit": "Generate a project structure for a Streamlit application.",
        "flask": "Generate a project structure for a Flask application with separate folders for templates and static files.",
        "fastapi": "Generate a project structure for a FastAPI application with a main router and models.",
        "nextjs": "Generate a project structure for a Next.js application with TypeScript, including pages, components, and styles.",
    }
    
    features_text = "\n".join([f"- {feature}" for feature in request.features])
    additional_context = f"\nAdditional requirements: {request.description}" if request.description else ""
    
    meta_prompt = f"""You are an expert software architect and senior software engineer.
Your task is to design and generate the complete file and folder structure for a new application based on the user's request.

APPLICATION DETAILS:
- App Name: "{request.app_name}"
- App Type: {request.app_type.upper()}
- Features:
{features_text}{additional_context}

OUTPUT FORMAT:
You must respond with a single JSON object that represents the entire project structure.
The JSON object should have a single root key, which is the project's root folder name.
Each key in the JSON object is a file or folder name.
- For a file, the value should be a string containing the full content of the file.
- For a folder, the value should be another JSON object representing the contents of that folder.

EXAMPLE JSON STRUCTURE:
{{
  "my-nextjs-app": {{
    "pages": {{
      "index.tsx": "export default function Home() {{ return <h1>Hello, World!</h1>; }}",
      "_app.tsx": "// App component"
    }},
    "components": {{
      "Button.tsx": "export function Button() {{ return <button>Click me</button>; }}"
    }},
    "package.json": "{{ \\"name\\": \\"my-nextjs-app\\", \\"version\\": \\"0.1.0\\" }}"
  }}
}}

CODE GENERATION GUIDELINES:
1.  Generate a complete and runnable project structure.
2.  The code in each file should be production-quality.
3.  Include all necessary configuration files (e.g., `package.json`, `tsconfig.json`, `requirements.txt`).
4.  Follow best practices for the specified application type.
5.  Do not include any explanations or markdown formatting in your response. Your entire output must be a single, valid JSON object.

{app_type_instructions.get(request.app_type, "Generate a standard project structure.")}

Now, generate the JSON for the "{request.app_name}" application.
"""
    return meta_prompt

async def stream_gemini_response(request: AppGenerationRequest):
    """Streams a structured response from Gemini, parsing the generated JSON."""
    try:
        setup_ai_clients()
        model = genai.GenerativeModel('gemini-pro')
        prompt = create_meta_prompt(request)
        
        # Use streaming generation
        response_stream = await model.generate_content_async(prompt, stream=True)
        
        full_response_text = ""
        async for chunk in response_stream:
            if chunk.text:
                full_response_text += chunk.text
        
        # Clean the response to get only the JSON part
        # Find the start and end of the JSON block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', full_response_text, re.DOTALL)
        if not json_match:
            # Fallback for when the model doesn't use markdown code blocks
            json_match = re.search(r'(\{.*?\})', full_response_text, re.DOTALL)

        if not json_match:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Could not parse AI response.'})}\n\n"
            return

        json_string = json_match.group(1)
        
        try:
            project_structure = json.loads(json_string)
        except json.JSONDecodeError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Invalid JSON from AI: {e}'})}\n\n"
            return

        # Coroutine to recursively stream the project structure
        async def stream_structure(item, current_path=""):
            if not isinstance(item, dict):
                return

            for name, content in item.items():
                new_path = os.path.join(current_path, name).replace("\\", "/")
                
                if name.endswith('/'): # It's a folder
                    yield f"data: {json.dumps({'type': 'create_folder', 'path': new_path})}\n\n"
                    await asyncio.sleep(0.1) # Small delay to make streaming visible
                    # Recurse into the folder
                    for event in stream_structure(content, new_path):
                        yield event
                else: # It's a file
                    yield f"data: {json.dumps({'type': 'create_file', 'path': new_path, 'content': content})}\n\n"
                    await asyncio.sleep(0.1) # Small delay

        # Start streaming the parsed structure
        async for event in stream_structure(project_structure):
            yield event

        yield f"data: {json.dumps({'type': 'log', 'message': 'Project generation complete.'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        logger.error(f"Error streaming from Gemini: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


# New two-stage generation logic
def create_planning_prompt(request: AppGenerationRequest) -> str:
    """Creates a prompt for the AI to plan the project structure."""
    app_guidance = {
        "react": "A modern React application using Vite, with `src/components`, `src/pages`, and `src/App.jsx`.",
        "nextjs": "A Next.js application with a standard `pages` or `app` directory structure.",
        "vue": "A Vue.js application with `src/components` and `src/views`.",
        "flask": "A Flask application with `app.py`, a `templates/` directory, and a `static/` directory.",
        "fastapi": "A FastAPI application with `main.py` and a `routers/` directory for modularity.",
        "streamlit": "A Streamlit application with a main script and a `pages/` directory for multi-page apps.",
        "python-cli": "A Python CLI with a main script and a `modules/` directory."
    }.get(request.app_type.lower(), "A standard project structure for this application type.")

    features_text = "\n".join([f"- {feature}" for feature in request.features])

    return f"""
You are a senior software architect. Your task is to plan the file and folder structure for a new software project.
Do not generate any code content. Only provide the file and folder hierarchy.

User Request:
- Application Name: "{request.app_name}"
- Application Type: "{request.app_type}"
- Features:
{features_text}
- Description: "{request.description}"

Based on the request, generate a list of all the necessary file and folder paths for a complete project.
Folders must end with a forward slash (`/`).
Your output MUST be a single, valid JSON array of strings.

Example format:
[
  "my-app/",
  "my-app/README.md",
  "my-app/package.json",
  "my-app/src/",
  "my-app/src/index.js"
]

Now, generate the JSON array for the requested project.
"""

def create_file_content_prompt(file_path: str, file_list: List[str], request: AppGenerationRequest) -> str:
    """Creates a prompt for the AI to generate the content of a single file."""
    
    project_context = "\n".join(file_list)

    return f"""
You are a senior software developer. Your task is to write the code for a single file within a larger project.
The code must be complete, production-ready, and adhere to best practices for the technology.

Project Details:
- Application Name: "{request.app_name}"
- Application Type: "{request.app_type}"
- Features: {', '.join(request.features)}
- Description: "{request.description}"

Complete Project File Structure (for context):
{project_context}

Now, generate the complete and correct code for the following file ONLY:
File Path: `{file_path}`

Do not write any explanations, comments, or markdown formatting (like ```python) around the code.
Only output the raw code for the file `{file_path}`.
"""

async def stream_gemini_response_two_stage(request: AppGenerationRequest):
    """
    Streams a project structure in two stages:
    1. Plan the file/folder structure.
    2. Generate content for each file individually.
    """
    try:
        setup_ai_clients()
        model = genai.GenerativeModel('gemini-pro')
        
        # --- STAGE 1: Plan the project structure ---
        yield f"data: {json.dumps({'type': 'log', 'message': 'Phase 1: Planning project structure...'})}\n\n"
        planning_prompt = create_planning_prompt(request)
        
        try:
            planning_response = await model.generate_content_async(planning_prompt)
            # Extract JSON array from the response
            json_text = re.search(r'\[.*?\]', planning_response.text, re.DOTALL).group(0)
            file_list = json.loads(json_text)
        except (AttributeError, json.JSONDecodeError, IndexError) as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Failed to plan project structure: {e}. AI response was: {planning_response.text}'})}\n\n"
            return

        # Stream the planned structure to the frontend
        for path in file_list:
            if path.endswith('/'):
                yield f"data: {json.dumps({'type': 'create_folder', 'path': path})}\n\n"
            else:
                # Create empty file first
                yield f"data: {json.dumps({'type': 'create_file', 'path': path, 'content': ''})}\n\n"
            await asyncio.sleep(0.05) # Fast stream for structure

        # --- STAGE 2: Generate file contents ---
        yield f"data: {json.dumps({'type': 'log', 'message': 'Phase 2: Generating code for each file...'})}\n\n"
        for file_path in [p for p in file_list if not p.endswith('/')]:
            yield f"data: {json.dumps({'type': 'log', 'message': f'Generating: {file_path}'})}\n\n"
            try:
                content_prompt = create_file_content_prompt(file_path, file_list, request)
                content_response = await model.generate_content_async(content_prompt)
                
                # Clean up response, remove markdown code blocks if they exist
                code_content = re.sub(r'```[a-zA-Z]*\n?', '', content_response.text)
                code_content = re.sub(r'```$', '', code_content).strip()

                yield f"data: {json.dumps({'type': 'update_file', 'path': file_path, 'content': code_content})}\n\n"
            except Exception as e:
                error_message = f"Failed to generate content for {file_path}: {e}"
                yield f"data: {json.dumps({'type': 'log', 'message': error_message})}\n\n"
                yield f"data: {json.dumps({'type': 'update_file', 'path': file_path, 'content': f'// Error generating file content: {e}'})}\n\n"
            await asyncio.sleep(0.1) # Small delay between file generations

        yield f"data: {json.dumps({'type': 'log', 'message': 'Project generation complete.'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        logger.error(f"Error in two-stage generation: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@app.get("/api/generate")
async def generate_code_streaming(request: Request):
    """
    Main endpoint for streaming code generation.
    Uses the new two-stage generation process.
    """
    try:
        query_params = request.query_params
        features_str = query_params.get("features", "")
        features = [f.strip() for f in features_str.split(',') if f.strip()]
        
        if not query_params.get("app_name") or not features:
            raise HTTPException(status_code=400, detail="app_name and features are required.")

        generation_request = AppGenerationRequest(
            app_name=query_params.get("app_name"),
            app_type=query_params.get("app_type", "react"),
            features=features,
            description=query_params.get("description", "")
        )
        
        provider = get_ai_provider()
        logger.info(f"Streaming code generation for '{generation_request.app_name}' using {provider}")

        if provider == "gemini":
            return StreamingResponse(stream_gemini_response_two_stage(generation_request), media_type="text/event-stream")
        else:
            async def not_implemented_stream():
                yield f"data: {json.dumps({'type': 'error', 'message': 'OpenAI streaming not implemented yet.'})}\n\n"
            return StreamingResponse(not_implemented_stream(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error in generate_code_streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))
