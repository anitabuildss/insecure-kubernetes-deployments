from flask import Flask, request, render_template_string, send_from_directory
import subprocess
import os
import shlex

app = Flask(__name__)

# Allowlist of safe commands - only these commands can be executed
ALLOWED_COMMANDS = {
    'date': ['date'],
    'whoami': ['whoami'],
    'pwd': ['pwd'],
    'hostname': ['hostname']
}

@app.route('/', methods=['GET', 'POST'])
def index():
    output = ''
    if request.method == 'POST':
        if 'command' in request.form:
            cmd = request.form['command'].strip()
            
            # Validate command against allowlist
            if cmd not in ALLOWED_COMMANDS:
                output = f"Error: Command '{cmd}' is not allowed. Allowed commands: {', '.join(ALLOWED_COMMANDS.keys())}"
            else:
                # Execute command safely without shell=True
                try:
                    process = subprocess.Popen(
                        ALLOWED_COMMANDS[cmd], 
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
                    output = "Error: Command timed out"
                except Exception as e:
                    output = f"Error: {str(e)}"
                    
        elif 'file' in request.files:
            uploaded_file = request.files['file']
            # Validate filename to prevent path traversal
            filename = os.path.basename(uploaded_file.filename)
            if not filename or filename.startswith('.'):
                output = "Error: Invalid filename"
            else:
                upload_dir = '/uploads'
                os.makedirs(upload_dir, exist_ok=True)
                uploaded_file.save(os.path.join(upload_dir, filename))
                output = f"File {filename} uploaded successfully!"

    return render_template_string("""
        <h1>Intentionally Insecure App</h1>
        <form action="/" method="post">
            Run a command: <input type="text" name="command">
            <input type="submit" value="Run">
        </form>
        <p>Allowed commands: date, whoami, pwd, hostname</p>
        <br>
        <form action="/" method="post" enctype="multipart/form-data">
            Upload a file: <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
        <pre>{{output}}</pre>
    """, output=output)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
