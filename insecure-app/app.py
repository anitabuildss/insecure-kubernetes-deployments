from flask import Flask, request, render_template_string, send_from_directory
import subprocess
import os
import shlex
from functools import wraps

app = Flask(__name__)

# Simple authentication token (in production, use proper authentication)
API_TOKEN = os.environ.get('API_TOKEN', 'CHANGE_ME_IN_PRODUCTION')

# Allowlist of safe commands
ALLOWED_COMMANDS = {
    'ls': ['/bin/ls'],
    'pwd': ['/bin/pwd'],
    'whoami': ['/usr/bin/whoami'],
    'date': ['/bin/date'],
    'echo': ['/bin/echo']
}

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-API-Token') or request.form.get('token')
        if not token or token != API_TOKEN:
            return "Unauthorized: Valid API token required", 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['GET', 'POST'])
def index():
    output = ''
    if request.method == 'POST':
        if 'command' in request.form:
            # Require authentication for command execution
            token = request.form.get('token')
            if not token or token != API_TOKEN:
                output = "Error: Authentication required for command execution"
            else:
                cmd_input = request.form['command'].strip()
                
                # Parse command safely
                try:
                    parts = shlex.split(cmd_input)
                except ValueError as e:
                    output = f"Error: Invalid command syntax - {str(e)}"
                    return render_template_string(get_template(), output=output)
                
                if not parts:
                    output = "Error: Empty command"
                    return render_template_string(get_template(), output=output)
                
                cmd_name = parts[0]
                
                # Check if command is in allowlist
                if cmd_name not in ALLOWED_COMMANDS:
                    output = f"Error: Command '{cmd_name}' not allowed. Allowed commands: {', '.join(ALLOWED_COMMANDS.keys())}"
                else:
                    # Use the full path from allowlist and pass arguments safely
                    cmd_path = ALLOWED_COMMANDS[cmd_name]
                    full_cmd = cmd_path + parts[1:]
                    
                    try:
                        # Execute without shell=True to prevent command injection
                        process = subprocess.Popen(
                            full_cmd,
                            shell=False,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        stdout, stderr = process.communicate(timeout=5)
                        if process.returncode == 0:
                            output = stdout.decode('utf-8')
                        else:
                            output = f"Error (Exit Code: {process.returncode}):\n{stderr.decode('utf-8')}"
                    except subprocess.TimeoutExpired:
                        process.kill()
                        output = "Error: Command execution timeout"
                    except Exception as e:
                        output = f"Error executing command: {str(e)}"
                        
        elif 'file' in request.files:
            # Require authentication for file upload
            token = request.form.get('token')
            if not token or token != API_TOKEN:
                output = "Error: Authentication required for file upload"
            else:
                uploaded_file = request.files['file']
                if uploaded_file.filename:
                    # Sanitize filename to prevent path traversal
                    filename = os.path.basename(uploaded_file.filename)
                    if filename and not filename.startswith('.'):
                        try:
                            uploaded_file.save(os.path.join('/uploads', filename))
                            output = f"File {filename} uploaded successfully!"
                        except Exception as e:
                            output = f"Error uploading file: {str(e)}"
                    else:
                        output = "Error: Invalid filename"
                else:
                    output = "Error: No file selected"

    return render_template_string(get_template(), output=output)

def get_template():
    return """
        <h1>Intentionally Insecure App (Now Secured)</h1>
        <p><strong>Note:</strong> Authentication is now required. Allowed commands: {{ allowed_cmds }}</p>
        <form action="/" method="post">
            API Token: <input type="password" name="token" required><br><br>
            Run a command: <input type="text" name="command">
            <input type="submit" value="Run">
        </form>
        <br>
        <form action="/" method="post" enctype="multipart/form-data">
            API Token: <input type="password" name="token" required><br><br>
            Upload a file: <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
        <pre>{{output}}</pre>
    """


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
