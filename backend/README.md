# AgentForge Backend 🚀

A FastAPI backend that provides AI-powered code generation endpoints. This backend accepts structured input (app name, features) and generates complete, runnable applications using OpenAI's GPT models.

## 🎯 Week 1 Goals - COMPLETED ✅

✅ **FastAPI Fundamentals**: Complete backend with path operations, request/response models, and async patterns  
✅ **Pydantic Models**: Structured input handling for app name, features list, and app type  
✅ **Multi-AI Integration**: Support for both OpenAI and Gemini APIs with dynamic switching  
✅ **Environment Management**: Secure API key handling with .env files  
✅ **Testing**: Comprehensive test suite to verify functionality with both providers  

## 🛠️ Features

- **Structured Code Generation**: Generate complete applications from app requirements
- **Multi-AI Provider Support**: Switch between OpenAI and Gemini APIs
- **Multiple App Types**: Support for Streamlit, Flask, and FastAPI applications
- **Meta-Prompt Engineering**: Intelligent prompt construction for better code quality
- **Free Testing**: Use Gemini API for free development and testing
- **Production Ready**: Switch to OpenAI for deployment
- **Error Handling**: Comprehensive error handling and validation
- **CORS Support**: Ready for frontend integration
- **API Documentation**: Auto-generated docs with FastAPI
- **Health Monitoring**: Health check endpoints for system status

## 📋 API Endpoints

### Main Endpoints
- `POST /generate` - Generate complete applications (main endpoint)
- `GET /health` - Health check with configuration status
- `GET /` - Root endpoint with API information

### Legacy Endpoints
- `POST /generate-simple` - Simple prompt-based generation

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## 🚀 Quick Setup

### Prerequisites
- Conda (Anaconda or Miniconda)
- **For free testing**: Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))
- **For deployment**: OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate conda environment:**
   ```bash
   # Create conda environment with Python 3.9+
   conda create -n agentforge python=3.9
   
   # Activate the environment
   conda activate agentforge
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   The `.env` file is already created for you! Add your API keys:
   
   **For free testing with Gemini (recommended):**
   ```env
   AI_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   
   **For OpenAI (deployment):**
   ```env
   AI_PROVIDER=openai
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Running the Server

```bash
uvicorn main:app --reload
```

The server will start at `http://127.0.0.1:8000`

## 🧪 Testing Your Setup

### Option 1: Run the Test Suite
```bash
python test_api.py
```

This will test all endpoints and save a sample generated app to `generated_app.py`.

### Option 2: Manual Testing

1. **Health Check:**
   ```bash
   curl http://127.0.0.1:8000/health
   ```

2. **Generate Code:**
   ```bash
   curl -X POST "http://127.0.0.1:8000/generate" \
        -H "Content-Type: application/json" \
        -d '{
          "app_name": "TodoApp",
          "features": ["Add tasks", "Mark complete", "Delete tasks"],
          "app_type": "streamlit",
          "description": "A simple task manager"
        }'
   ```

### Option 3: Interactive API Docs
Visit `http://127.0.0.1:8000/docs` in your browser for interactive API testing.

## 📝 API Usage Examples

### Generate a Streamlit App
```json
{
  "app_name": "DataDashboard",
  "features": [
    "Upload CSV files",
    "Display data statistics",
    "Create interactive charts",
    "Export filtered data"
  ],
  "app_type": "streamlit",
  "description": "A data analysis dashboard with visualization capabilities"
}
```

### Generate a Flask Web App
```json
{
  "app_name": "BlogSite",
  "features": [
    "User registration and login",
    "Create and edit blog posts",
    "Comment system",
    "Admin panel"
  ],
  "app_type": "flask",
  "description": "A simple blog platform with user management"
}
```

### Generate a FastAPI Backend
```json
{
  "app_name": "TaskAPI",
  "features": [
    "CRUD operations for tasks",
    "User authentication",
    "Task categories",
    "API documentation"
  ],
  "app_type": "fastapi",
  "description": "A RESTful API for task management"
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_PROVIDER` | Which AI to use: 'openai' or 'gemini' | `gemini` |
| `GEMINI_API_KEY` | Your Gemini API key (free) | Required for Gemini |
| `GEMINI_MODEL` | Gemini model to use | `gemini-1.5-flash` |
| `OPENAI_API_KEY` | Your OpenAI API key (paid) | Required for OpenAI |
| `OPENAI_MODEL` | GPT model to use | `gpt-4` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `DEBUG` | Enable debug mode | `True` |

### Model Recommendations

**Gemini (Free):**
- **gemini-1.5-flash**: Fast, good quality, **FREE** 🎉
- **gemini-1.5-pro**: Higher quality, slower, **FREE**

**OpenAI (Paid):**
- **gpt-4**: Best quality, slower, more expensive
- **gpt-3.5-turbo**: Good quality, faster, cheaper
- **gpt-4-turbo**: Balanced option (if available)

## 🐛 Troubleshooting

### Common Issues

1. **"API_KEY not configured"**
   - Make sure you created a `.env` file
   - Verify your API key is correct
   - Check `AI_PROVIDER` matches your configured API key
   - For Gemini: Get key at [Google AI Studio](https://aistudio.google.com/app/apikey)
   - For OpenAI: Get key at [OpenAI Platform](https://platform.openai.com/api-keys)

2. **"Model not found" errors**
   - For Gemini: Try `gemini-1.5-flash` (most reliable)
   - For OpenAI: Try `gpt-3.5-turbo` (if gpt-4 fails)

3. **CORS errors from frontend**
   - Make sure CORS middleware is enabled
   - Check that frontend URL is in allowed origins

4. **Import errors**
   - Ensure conda environment is activated: `conda activate agentforge`
   - Reinstall requirements: `pip install -r requirements.txt`

### Getting Help

- Check the FastAPI docs at `/docs`
- Run the test suite to verify setup
- Check server logs for detailed error messages

## 🚀 Next Steps

Your Week 1 backend is complete! Here's what you can do next:

1. **Get a free Gemini API key** at [Google AI Studio](https://aistudio.google.com/app/apikey)
2. **Test thoroughly** using the provided test script
3. **Experiment** with different app types and features
4. **Connect the frontend** to consume these APIs
5. **Switch to OpenAI** for final deployment
6. **Optimize prompts** for better code generation

## 📚 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Guide](https://platform.openai.com/docs)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)

---

**Milestone Achieved**: You now have a working, AI-powered code generation engine accessible via API! 🎉
