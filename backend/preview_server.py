from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import json
import os
import subprocess
import atexit
import threading
import time
import tempfile
import shutil
import queue
import re
from fastapi.responses import StreamingResponse

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AgentForge Preview Server",
    description="Runs generated code in a temporary environment for live preview.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- State Management ---
active_runs = {} # { process_id: {'process': proc, 'port': port, 'temp_dir': temp_dir, 'log_queue': Queue} }
next_port = 8002  # Start from 8002 to avoid conflict with preview server on 8001

def get_next_available_port():
    global next_port
    # In a real app, you'd check if the port is actually free.
    # For this example, we'll just increment.
    port = next_port
    next_port += 1
    return port

def cleanup_process(process_id):
    """Stop a running process and clean up its resources."""
    if process_id in active_runs:
        run_info = active_runs[process_id]
        logger.info(f"Cleaning up process {process_id} on port {run_info.get('port')}")
        
        process = run_info.get('process')
        if process and process.poll() is None:  # Check if process is still running
            try:
                logger.info(f"Terminating process {process_id}")
                process.terminate()
                try:
                    process.wait(timeout=3)  # Reduced timeout to 3 seconds
                    logger.info(f"Process {process_id} terminated gracefully.")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Process {process_id} did not terminate gracefully, force killing.")
                    process.kill()
                    try:
                        process.wait(timeout=2)  # Give it 2 more seconds to die
                        logger.info(f"Process {process_id} force killed.")
                    except subprocess.TimeoutExpired:
                        logger.error(f"Process {process_id} could not be killed - it may be stuck.")
            except Exception as e:
                logger.error(f"Error terminating process {process_id}: {e}")

        temp_dir = run_info.get('temp_dir')
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Removed temporary directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Error removing temporary directory {temp_dir}: {e}")

        del active_runs[process_id]
        logger.info(f"Process {process_id} cleanup completed.")
    else:
        logger.warning(f"Process {process_id} not found in active_runs during cleanup.")

# Cleanup all running processes on exit
atexit.register(lambda: [cleanup_process(pid) for pid in list(active_runs.keys())])


class RunRequest(BaseModel):
    fileSystem: dict

def write_project_to_disk(file_system: dict, base_dir: str):
    """Recursively write the virtual file system to a physical directory."""
    for name, item in file_system.items():
        # Sanitize the name to prevent directory traversal
        # and handle both folder and file names.
        # The name from the frontend can contain subdirectories.
        sanitized_name = name.replace('..', '').lstrip('/')
        path = os.path.join(base_dir, sanitized_name.replace('/', os.path.sep))

        if item.get('type') == 'folder':
            os.makedirs(path, exist_ok=True)
            if item.get('children'):
                write_project_to_disk(item['children'], path)
        elif item.get('type') == 'file':
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(item.get('content', ''))

@app.post("/api/run")
async def run_project(request: RunRequest):
    """
    Receives a file system, writes it to a temporary directory,
    installs dependencies, and runs the project.
    """
    temp_dir = tempfile.mkdtemp(prefix="agentforge_run_")
    process_id = os.path.basename(temp_dir)
    port = get_next_available_port()

    # Clean up any previous run with the same process_id, just in case
    if process_id in active_runs:
        logger.warning(f"Found existing process {process_id}. Cleaning up before new run.")
        cleanup_process(process_id)

    project_dir = temp_dir # The commands will run from the root of the temp dir
    try:
        logger.info(f"Writing project to temporary directory: {project_dir}")
        write_project_to_disk(request.fileSystem, project_dir)

        # --- Logic to install dependencies and run ---
        # This is highly dependent on the project type.
        # We need to detect the project type and run the correct commands.
        
        run_command = None
        install_command = None
        env = os.environ.copy()
        
        def find_project_root(start_path):
            """Recursively search for a project root (containing requirements.txt or package.json)."""
            for root, dirs, files in os.walk(start_path):
                if "requirements.txt" in files:
                    logger.info(f"Found requirements.txt in {root}")
                    return root
                if "package.json" in files:
                    logger.info(f"Found package.json in {root}")
                    return root
            return None

        execution_cwd = find_project_root(project_dir)
        
        if not execution_cwd:
            raise HTTPException(status_code=400, detail="Could not find a project root (requirements.txt or package.json).")

        logger.info(f"[{process_id}] Set execution CWD to: {execution_cwd}")

        # --- New logic: Read README.md to find commands ---
        readme_path = os.path.join(execution_cwd, "README.md")
        if os.path.exists(readme_path):
            logger.info(f"[{process_id}] Found README.md. Attempting to parse commands.")
            try:
                with open(readme_path, "r", encoding="utf-8") as f:
                    readme_content = f.read()

                # Regex to find install commands (e.g., pip install ..., npm install)
                install_match = re.search(r"`(pip install .*?)`|`(npm install.*?)`", readme_content)
                if install_match:
                    install_command = install_match.group(1) or install_match.group(2)
                    logger.info(f"[{process_id}] Parsed install command from README: '{install_command}'")

                # Regex to find run commands (e.g., streamlit run, npm run dev)
                run_match = re.search(r"`(streamlit run .*?)`|`(npm run .*?)`|`(flask run.*?)`|`(uvicorn .*?)`|`(python .*?)`", readme_content)
                if run_match:
                    # Find the first non-None group
                    run_command = next((cmd for cmd in run_match.groups() if cmd is not None), None)
                    if run_command and "streamlit" in run_command and "--server.port" not in run_command:
                         run_command += f" --server.port {port} --server.address 127.0.0.1 --server.headless true"
                    elif run_command and "flask" in run_command and "--port" not in run_command:
                        run_command += f" --host 127.0.0.1 --port {port}"
                    elif run_command and "uvicorn" in run_command and "--port" not in run_command:
                        run_command += f" --host 127.0.0.1 --port {port}"

                    logger.info(f"[{process_id}] Parsed run command from README: '{run_command}'")
                
                if install_command and "npm" in install_command:
                    env["PORT"] = str(port)
                    logger.info(f"[{process_id}] Detected Node.js project. Setting PORT env var to {port}")

            except Exception as e:
                logger.error(f"[{process_id}] Error parsing README.md: {e}. Falling back to detection logic.")
                install_command = None
                run_command = None
        else:
            logger.info(f"[{process_id}] No README.md found at {readme_path}")

        # --- Fallback to old detection logic if README parsing fails ---
        if not install_command or not run_command:
            logger.info(f"[{process_id}] README parsing failed or incomplete. Falling back to file-based detection.")
            
            if os.path.exists(os.path.join(execution_cwd, "requirements.txt")):
                # Python project
                logger.info(f"[{process_id}] Detected Python project.")
                if not install_command:
                    install_command = f"pip install -r requirements.txt"
                
                if not run_command:
                    # Check for streamlit, flask, fastapi
                    with open(os.path.join(execution_cwd, "requirements.txt"), "r") as f:
                        reqs = f.read().lower()
                        if "streamlit" in reqs:
                            # Find the python file to run.
                            py_files = [f for f in os.listdir(execution_cwd) if f.endswith('.py')]
                            if py_files:
                                main_file = py_files[0] # Assume first .py file is the entrypoint
                                run_command = f"streamlit run {main_file} --server.port {port} --server.address 127.0.0.1 --server.headless true"
                                logger.info(f"[{process_id}] Detected Streamlit. Running command: {run_command}")
                        elif "flask" in reqs:
                            run_command = f"flask run --host 127.0.0.1 --port {port}"
                            logger.info(f"[{process_id}] Detected Flask. Running command: {run_command}")
                        elif "fastapi" in reqs:
                            run_command = f"uvicorn main:app --host 127.0.0.1 --port {port} --reload"
                            logger.info(f"[{process_id}] Detected FastAPI. Running command: {run_command}")
                        else:
                            # Generic Python fallback - look for common entry point files
                            py_files = [f for f in os.listdir(execution_cwd) if f.endswith('.py')]
                            main_candidates = ['main.py', 'app.py', 'run.py', 'server.py']
                            main_file = None
                            
                            # Try to find a main file
                            for candidate in main_candidates:
                                if candidate in py_files:
                                    main_file = candidate
                                    break
                            
                            if not main_file and py_files:
                                main_file = py_files[0]  # Use first .py file as fallback
                            
                            if main_file:
                                run_command = f"python {main_file}"
                                logger.info(f"[{process_id}] Generic Python project. Running: {run_command}")
                            else:
                                logger.warning(f"[{process_id}] No Python files found in {execution_cwd}")

            elif os.path.exists(os.path.join(execution_cwd, "package.json")):
                # Node.js project
                logger.info(f"[{process_id}] Detected Node.js project.")
                if not install_command:
                    install_command = "npm install"
                    
                if not run_command:
                    with open(os.path.join(execution_cwd, "package.json"), "r") as f:
                        package_json = json.load(f)
                        scripts = package_json.get("scripts", {})
                        if "dev" in scripts:
                            run_command = "npm run dev"
                        elif "start" in scripts:
                            run_command = "npm run start"
                        else:
                            logger.warning(f"[{process_id}] No 'dev' or 'start' script found in package.json.")
                
                # Pass port as an environment variable for Node apps
                env["PORT"] = str(port)
                logger.info(f"[{process_id}] Found run command: '{run_command}'. Setting PORT env var to {port}")

        if not run_command:
            logger.error(f"[{process_id}] Could not determine how to run the project in {execution_cwd}.")
            # List files for debugging
            files_in_dir = os.listdir(execution_cwd)
            logger.error(f"[{process_id}] Files in directory: {files_in_dir}")
            
            # Additional debugging info
            logger.error(f"[{process_id}] install_command: {install_command}")
            logger.error(f"[{process_id}] run_command: {run_command}")
            if os.path.exists(os.path.join(execution_cwd, "requirements.txt")):
                with open(os.path.join(execution_cwd, "requirements.txt"), "r") as f:
                    logger.error(f"[{process_id}] requirements.txt content: {f.read()}")
            
            raise HTTPException(status_code=400, detail="Could not determine how to run the project.")

        # Create log queue before starting the background process
        log_queue = queue.Queue()
        log_queue.put(f"[system] Starting project setup...")
        
        # Initialize active_runs entry early so log streaming can start immediately
        active_runs[process_id] = {
            "process": None,  # Will be set when process starts
            "port": port,
            "temp_dir": temp_dir,
            "log_queue": log_queue
        }

        # Run commands in a separate thread to not block the server
        def run_in_background():
            def stream_reader(pipe, pipe_name):
                try:
                    for line in iter(pipe.readline, ''):
                        log_message = f"[{pipe_name}] {line.strip()}"
                        log_queue.put(log_message)
                        logger.info(f"[{process_id}]{log_message}")
                finally:
                    pipe.close()

            try:
                if install_command:
                    logger.info(f"[{process_id}] Installing dependencies with command: `{install_command}`")
                    log_queue.put(f"[install] Running: {install_command}")
                    install_process = subprocess.run(
                        install_command, shell=True, check=True, cwd=execution_cwd, capture_output=True, text=True
                    )
                    log_queue.put(f"[install] STDOUT: {install_process.stdout}")
                    if install_process.stderr:
                        log_queue.put(f"[install] STDERR: {install_process.stderr}")
                    logger.info(f"[{process_id}] Installation stdout: {install_process.stdout}")
                    if install_process.stderr:
                        logger.warning(f"[{process_id}] Installation stderr: {install_process.stderr}")

                logger.info(f"[{process_id}] Starting project on port {port} with command: `{run_command}`")
                logger.info(f"[{process_id}] Working directory: {execution_cwd}")
                logger.info(f"[{process_id}] Environment variables: {dict(env)}")
                log_queue.put(f"[run] Starting: {run_command}")
                log_queue.put(f"[run] Working directory: {execution_cwd}")
                log_queue.put(f"[run] Port: {port}")
                proc = subprocess.Popen(
                    run_command, 
                    shell=True, 
                    cwd=execution_cwd, 
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                
                # Update the active_runs entry with the actual process
                active_runs[process_id]["process"] = proc

                stdout_thread = threading.Thread(target=stream_reader, args=(proc.stdout, 'stdout'), daemon=True)
                stderr_thread = threading.Thread(target=stream_reader, args=(proc.stderr, 'stderr'), daemon=True)
                stdout_thread.start()
                stderr_thread.start()
                
                proc.wait() # Wait for process to finish
                stdout_thread.join()
                stderr_thread.join()

            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                error_message = f"Error running project: {e}"
                if hasattr(e, 'stderr'):
                    error_message += f"\nStderr: {e.stderr}"
                log_queue.put(f"[error] {error_message}")
                logger.error(f"[{process_id}] {error_message}")
            finally:
                log_queue.put("[system] Process finished. Cleaning up.")
                logger.info(f"[{process_id}] Process finished or failed. Cleaning up.")
                cleanup_process(process_id)


        threading.Thread(target=run_in_background, daemon=True).start()

        # Give the server a moment to start up
        time.sleep(5) 

        return {"url": f"http://127.0.0.1:8001/api/proxy/{process_id}", "process_id": process_id}

    except Exception as e:
        logger.error(f"Error setting up project run: {e}")
        # Ensure cleanup happens on setup failure as well
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stop")
async def stop_project(request: Request):
    body = await request.json()
    process_id = body.get("process_id")
    if not process_id:
        raise HTTPException(status_code=400, detail="process_id is required.")
    
    logger.info(f"Received request to stop process {process_id}")
    
    # Check if process exists
    if process_id not in active_runs:
        logger.warning(f"Process {process_id} not found in active_runs")
        return {"success": False, "message": f"Process {process_id} not found or already stopped."}
    
    # Run cleanup in a separate thread to avoid blocking the API response
    def cleanup_async():
        cleanup_process(process_id)
    
    threading.Thread(target=cleanup_async, daemon=True).start()
    
    return {"success": True, "message": f"Process {process_id} stop initiated."}

async def log_generator(process_id: str):
    """Yields logs from the queue for a given process_id."""
    logger.info(f"Starting log stream for process {process_id}")
    try:
        while True:
            if process_id not in active_runs:
                log_message = "Process not found or already terminated."
                yield f"data: {json.dumps({'type': 'log', 'message': log_message})}\n\n"
                break
            
            log_queue = active_runs[process_id].get("log_queue")
            try:
                log_message = log_queue.get(timeout=1)
                yield f"data: {json.dumps({'type': 'log', 'message': log_message})}\n\n"
            except queue.Empty:
                # Check if the process is still alive (if it exists)
                process = active_runs.get(process_id, {}).get('process')
                if process is not None and process.poll() is not None:
                    yield f"data: {json.dumps({'type': 'done', 'message': 'Process terminated.'})}\n\n"
                    break
                continue
    except Exception as e:
        logger.error(f"Log streaming error for {process_id}: {e}")
    finally:
        logger.info(f"Stopping log stream for process {process_id}")


@app.get("/api/logs/{process_id}")
async def stream_logs(process_id: str):
    logger.info(f"Log stream request for process_id: {process_id}")
    logger.info(f"Active runs: {list(active_runs.keys())}")
    if process_id not in active_runs:
        logger.warning(f"Process {process_id} not found in active_runs")
        raise HTTPException(status_code=404, detail="Process not found")
    return StreamingResponse(log_generator(process_id), media_type="text/event-stream")


@app.get("/api/debug/active-runs")
async def debug_active_runs():
    """Debug endpoint to see what processes are currently active"""
    return {
        "active_processes": list(active_runs.keys()),
        "details": {pid: {
            "port": data.get("port"),
            "temp_dir": data.get("temp_dir"),
            "has_process": data.get("process") is not None,
            "process_alive": data.get("process") and data.get("process").poll() is None
        } for pid, data in active_runs.items()}
    }

@app.get("/api/proxy/{process_id}")
async def proxy_to_app(process_id: str, request: Request):
    """Proxy requests to the running app to avoid iframe restrictions"""
    if process_id not in active_runs:
        raise HTTPException(status_code=404, detail="Process not found")
    
    app_port = active_runs[process_id]["port"]
    
    # Get the path from the request
    path = request.url.path.replace(f"/api/proxy/{process_id}", "")
    query_string = str(request.url.query) if request.url.query else ""
    
    # Build the target URL
    target_url = f"http://127.0.0.1:{app_port}{path}"
    if query_string:
        target_url += f"?{query_string}"
    
    try:
        import requests
        response = requests.get(target_url, timeout=10)
        
        # Remove headers that prevent iframe embedding
        headers_to_remove = [
            "x-frame-options",
            "content-security-policy",
            "x-content-type-options"
        ]
        
        response_headers = {}
        for key, value in response.headers.items():
            if key.lower() not in headers_to_remove:
                response_headers[key] = value
        
        from fastapi import Response
        return Response(
            content=response.content,
            media_type=response.headers.get("content-type", "text/html"),
            headers=response_headers,
            status_code=response.status_code
        )
    except Exception as e:
        logger.error(f"Error proxying to app: {e}")
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

@app.get("/api/debug/check-headers/{process_id}")
async def check_app_headers(process_id: str):
    """Debug endpoint to check what headers the app is sending"""
    if process_id not in active_runs:
        raise HTTPException(status_code=404, detail="Process not found")
    
    app_port = active_runs[process_id]["port"]
    
    try:
        import requests
        response = requests.get(f"http://127.0.0.1:{app_port}", timeout=5)
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "url": f"http://127.0.0.1:{app_port}"
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    # This preview server should run on a different port than the main backend
    uvicorn.run(app, host="0.0.0.0", port=8001)
