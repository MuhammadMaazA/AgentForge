from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from dotenv import load_dotenv
import openai
import google.generativeai as genai
import os
import logging
import datetime
import datetime

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
    app_type: str = Field(default="streamlit", description="Type of application (streamlit, flask, fastapi)")
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
    """Create a detailed meta-prompt for the LLM based on the input requirements"""
    
    app_type_instructions = {
        "streamlit": """
Create a single-file Streamlit application that is production-ready and well-structured.
Use st.sidebar for navigation and controls, implement proper error handling, and include data visualization where appropriate.
Make sure to include all necessary imports and follow Streamlit best practices.
""",
        "flask": """
Create a Flask web application with proper route structure, templates, and error handling.
Include both backend logic and HTML templates. Use Flask best practices and proper project structure.
""",
        "fastapi": """
Create a FastAPI application with proper async/await patterns, Pydantic models, and API documentation.
Include proper error handling, request validation, and follow FastAPI best practices.
"""
    }
    
    features_text = "\n".join([f"- {feature}" for feature in request.features])
    additional_context = f"\nAdditional requirements: {request.description}" if request.description else ""
    
    meta_prompt = f"""You are a senior software engineer with expertise in building production-ready applications.

Your task is to create a complete, functional {request.app_type.upper()} application named "{request.app_name}".

APPLICATION REQUIREMENTS:
{features_text}{additional_context}

TECHNICAL SPECIFICATIONS:
{app_type_instructions.get(request.app_type, app_type_instructions["streamlit"])}

CODE GENERATION GUIDELINES:
1. Generate COMPLETE, runnable code - not pseudo-code or partial implementations
2. Include ALL necessary imports and dependencies
3. Add comprehensive error handling and input validation
4. Include helpful comments explaining key functionality
5. Follow best practices for the chosen framework
6. Make the UI clean, professional, and user-friendly
7. Include sample data or placeholder content where needed
8. Ensure the code is modular and well-organized

The generated code should be ready to run immediately after creating the file and installing dependencies.
Return ONLY the complete application code without any markdown formatting or explanations."""

    return meta_prompt

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
