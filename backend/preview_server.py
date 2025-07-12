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
import signal
import psutil  # For better process management
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
    try:
        if process_id in active_runs:
            run_info = active_runs[process_id]
            logger.info(f"Quick cleanup of process {process_id}")
            
            process = run_info.get('process')
            if process and process.poll() is None:
                try:
                    logger.info(f"Force killing process {process_id} (PID: {process.pid})")
                    process.kill()  # Just kill it immediately
                except Exception as e:
                    logger.error(f"Error killing process {process_id}: {e}")

            # Don't bother with temp directory cleanup - let OS handle it
            # Remove from active runs immediately
            del active_runs[process_id]
            logger.info(f"Process {process_id} cleanup completed.")
        else:
            logger.warning(f"Process {process_id} not found in active_runs during cleanup.")
    except Exception as e:
        logger.error(f"Error during cleanup of process {process_id}: {e}")
        # Make sure we remove it from active_runs even if cleanup fails
        if process_id in active_runs:
            try:
                del active_runs[process_id]
            except:
                pass

# Cleanup all running processes on exit
def cleanup_all_processes():
    """Cleanup all processes without blocking shutdown"""
    logger.info("Starting cleanup of all processes...")
    try:
        # Just kill everything quickly
        for process_id, run_info in list(active_runs.items()):
            process = run_info.get('process')
            if process and process.poll() is None:
                try:
                    process.kill()
                except:
                    pass
        
        # Clear the active runs dictionary
        active_runs.clear()
        logger.info("Cleanup completed")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# Don't register atexit - it causes hanging
# atexit.register(cleanup_all_processes)


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
    logger.info("=== NEW RUN REQUEST ===")
    logger.info(f"Current active runs: {list(active_runs.keys())}")
    
    temp_dir = tempfile.mkdtemp(prefix="agentforge_run_")
    process_id = os.path.basename(temp_dir)
    port = get_next_available_port()

    logger.info(f"Generated process_id: {process_id}, port: {port}")

    # Clean up any previous run with the same process_id, just in case
    if process_id in active_runs:
        logger.warning(f"Found existing process {process_id}. Cleaning up before new run.")
        cleanup_process(process_id)

    # Kill any orphaned processes that might be blocking
    try:
        logger.info("Checking for orphaned processes...")
        for existing_id, run_info in list(active_runs.items()):
            process = run_info.get('process')
            if process and process.poll() is not None:  # Process is dead but still tracked
                logger.warning(f"Found dead process {existing_id}, cleaning up...")
                cleanup_process(existing_id)
    except Exception as e:
        logger.error(f"Error during orphan cleanup: {e}")

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
                        if not line:  # EOF
                            break
                        log_message = f"[{pipe_name}] {line.strip()}"
                        if process_id in active_runs:  # Only log if process still tracked
                            log_queue.put(log_message)
                            logger.info(f"[{process_id}]{log_message}")
                except Exception as e:
                    logger.error(f"Error reading from {pipe_name}: {e}")
                finally:
                    try:
                        pipe.close()
                    except:
                        pass

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
                if process_id in active_runs:
                    active_runs[process_id]["process"] = proc

                stdout_thread = threading.Thread(target=stream_reader, args=(proc.stdout, 'stdout'), daemon=True)
                stderr_thread = threading.Thread(target=stream_reader, args=(proc.stderr, 'stderr'), daemon=True)
                stdout_thread.start()
                stderr_thread.start()
                
                # Wait for process to finish
                proc.wait()
                
                # Wait for log readers to finish, but with timeout
                stdout_thread.join(timeout=2)
                stderr_thread.join(timeout=2)

            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                error_message = f"Error running project: {e}"
                if hasattr(e, 'stderr') and e.stderr:
                    error_message += f"\nStderr: {e.stderr}"
                if process_id in active_runs:
                    log_queue.put(f"[error] {error_message}")
                logger.error(f"[{process_id}] {error_message}")
            except Exception as e:
                error_message = f"Unexpected error: {e}"
                if process_id in active_runs:
                    log_queue.put(f"[error] {error_message}")
                logger.error(f"[{process_id}] {error_message}")
            finally:
                if process_id in active_runs:
                    log_queue.put("[system] Process finished. Cleaning up.")
                logger.info(f"[{process_id}] Process finished or failed. Cleaning up.")
                # Don't call cleanup_process here as it might cause recursion
                # The process will be cleaned up when stop is called or server shuts down


        threading.Thread(target=run_in_background, daemon=True).start()

        # Give the server a moment to start up, but don't wait too long
        logger.info(f"Waiting for process {process_id} to start...")
        time.sleep(3)  # Reduced from 5 to 3 seconds
        
        # Check if process actually started
        if process_id in active_runs:
            process = active_runs[process_id].get('process')
            if process and process.poll() is None:
                logger.info(f"Process {process_id} started successfully on port {port}")
                return {"url": f"http://127.0.0.1:{port}", "process_id": process_id}
            else:
                logger.error(f"Process {process_id} failed to start or died immediately")
                # Clean up failed process
                if process_id in active_runs:
                    cleanup_process(process_id)
                raise HTTPException(status_code=500, detail="Failed to start project - process died immediately")
        else:
            logger.error(f"Process {process_id} not found after startup attempt")
            raise HTTPException(status_code=500, detail="Failed to start project - process not found")

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
    
    try:
        # Quick and dirty cleanup - just kill and remove
        run_info = active_runs[process_id]
        process = run_info.get('process')
        
        if process and process.poll() is None:
            logger.info(f"Force killing process {process_id} (PID: {process.pid})")
            try:
                process.kill()
                process.wait(timeout=1)  # Quick wait
            except:
                pass  # Don't care if it fails
        
        # Remove from active runs immediately
        del active_runs[process_id]
        logger.info(f"Process {process_id} stopped and removed from tracking")
        
        return {"success": True, "message": f"Process {process_id} stopped successfully."}
    except Exception as e:
        logger.error(f"Error stopping process {process_id}: {e}")
        # Still try to remove it
        if process_id in active_runs:
            try:
                del active_runs[process_id]
            except:
                pass
        return {"success": True, "message": f"Process {process_id} removed from tracking (may have been stuck)."}  # Return success anyway

@app.post("/api/force-stop")
async def force_stop_project(request: Request):
    """Force stop a project by killing all processes on its port"""
    body = await request.json()
    process_id = body.get("process_id")
    if not process_id:
        raise HTTPException(status_code=400, detail="process_id is required.")
    
    logger.info(f"Received request to force stop process {process_id}")
    
    # Check if process exists
    if process_id not in active_runs:
        logger.warning(f"Process {process_id} not found in active_runs")
        return {"success": False, "message": f"Process {process_id} not found or already stopped."}
    
    port = active_runs[process_id].get("port")
    if port:
        try:
            # Find all processes using this port and kill them
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    for conn in proc.info['connections']:
                        if conn.laddr.port == port:
                            logger.info(f"Force killing process {proc.info['pid']} ({proc.info['name']}) using port {port}")
                            psutil.Process(proc.info['pid']).kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception as e:
            logger.error(f"Error force stopping processes on port {port}: {e}")
    
    # Clean up the process record
    cleanup_process(process_id)
    
    return {"success": True, "message": f"Process {process_id} force stopped."}

@app.post("/api/kill-port")
async def kill_processes_on_port(request: Request):
    """Kill all processes using a specific port"""
    body = await request.json()
    port = body.get("port")
    if not port:
        raise HTTPException(status_code=400, detail="port is required.")
    
    logger.info(f"Received request to kill all processes on port {port}")
    
    killed_processes = []
    try:
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.info['connections']:
                    if conn.laddr.port == port:
                        logger.info(f"Killing process {proc.info['pid']} ({proc.info['name']}) using port {port}")
                        psutil.Process(proc.info['pid']).kill()
                        killed_processes.append(f"PID {proc.info['pid']} ({proc.info['name']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        logger.error(f"Error killing processes on port {port}: {e}")
        raise HTTPException(status_code=500, detail=f"Error killing processes: {str(e)}")
    
    return {"success": True, "killed_processes": killed_processes, "message": f"Killed {len(killed_processes)} processes on port {port}"}

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

@app.get("/api/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok", "active_processes": list(active_runs.keys())}

@app.post("/api/cleanup-all")
async def cleanup_all():
    """Emergency cleanup endpoint to stop all processes"""
    logger.info("Emergency cleanup requested")
    try:
        # Make a copy of the keys to avoid dict changing during iteration
        process_ids = list(active_runs.keys())
        for process_id in process_ids:
            try:
                cleanup_process(process_id)
            except Exception as e:
                logger.error(f"Error cleaning up process {process_id}: {e}")
        
        return {"success": True, "message": f"Cleaned up {len(process_ids)} processes"}
    except Exception as e:
        logger.error(f"Error during cleanup all: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/reset-server")
async def reset_server():
    """Nuclear option - reset everything"""
    logger.info("=== SERVER RESET REQUESTED ===")
    try:
        # Kill all tracked processes
        for process_id, run_info in list(active_runs.items()):
            try:
                process = run_info.get('process')
                if process:
                    try:
                        process.kill()
                    except:
                        pass
            except:
                pass
        
        # Clear everything
        active_runs.clear()
        
        # Reset port counter
        global next_port
        next_port = 8002
        
        logger.info("Server reset completed")
        return {"success": True, "message": "Server reset successfully"}
    except Exception as e:
        logger.error(f"Error during server reset: {e}")
        return {"success": False, "message": f"Reset error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    import signal
    import sys
    
    def signal_handler(signum, frame):
        """Handle Ctrl+C gracefully"""
        logger.info(f"Received signal {signum}, shutting down immediately...")
        # Just exit immediately, don't try to clean up
        sys.exit(0)
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # This preview server should run on a different port than the main backend
    uvicorn.run(app, host="0.0.0.0", port=8001)
