# Generated Applications Directory

This directory contains all the AI-generated applications created by AgentForge.

## Directory Structure

```
generated_apps/
├── streamlit/          # Streamlit applications
├── fastapi/           # FastAPI applications  
├── flask/             # Flask applications
└── README.md          # This file
```

## File Naming Convention

Generated files follow this naming pattern:
```
{app_name}_{ai_provider}_{timestamp}.py
```

Examples:
- `TaskManager_gemini_20250107_143022.py`
- `WeatherApp_openai_20250107_143156.py`
- `BlogSystem_gemini_20250107_143301.py`

## How to Run Generated Apps

### Streamlit Apps
```bash
cd generated_apps/streamlit
streamlit run your_app_name.py
```

### FastAPI Apps
```bash
cd generated_apps/fastapi
uvicorn your_app_name:app --reload
```

### Flask Apps
```bash
cd generated_apps/flask
python your_app_name.py
```

## Notes

- All generated applications are complete and ready to run
- Dependencies may need to be installed (check the generated code for required packages)
- Each app includes comprehensive error handling and best practices
- Files are automatically saved with timestamps to prevent overwrites
