from flask import Flask, request, render_template_string, send_from_directory
import subprocess
import os
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Define the upload directory as a constant
UPLOAD_DIR = '/uploads'

def safe_save_file(file_storage):
    """
    Safely save an uploaded file with multiple security checks.
    
    Args:
        file_storage: FileStorage object from request.files
        
    Returns:
        tuple: (success: bool, message: str, saved_filename: str or None)
    """
    # Check if file has a filename
    if not file_storage.filename or file_storage.filename == '':
        return False, "No filename provided", None
    
    # Sanitize the filename to remove path traversal attempts
    original_filename = file_storage.filename
    safe_filename = secure_filename(original_filename)
    
    # Check if secure_filename resulted in an empty string
    if not safe_filename or safe_filename == '':
        return False, "Invalid filename", None
    
    # Generate a unique filename to prevent overwrites and predictable paths
    # Keep the original extension if present
    file_ext = os.path.splitext(safe_filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    
    # Construct the full path
    upload_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Resolve to canonical path and verify it's within UPLOAD_DIR
    try:
        canonical_upload_dir = os.path.realpath(UPLOAD_DIR)
        canonical_file_path = os.path.realpath(upload_path)
        
        # Ensure the resolved path is within the upload directory
        if not canonical_file_path.startswith(canonical_upload_dir + os.sep):
            return False, "Path traversal attempt detected", None
    except (OSError, ValueError) as e:
        return False, f"Path validation error: {str(e)}", None
    
    # Save the file
    try:
        file_storage.save(upload_path)
        return True, f"File uploaded successfully as {unique_filename}", unique_filename
    except Exception as e:
        return False, f"Failed to save file: {str(e)}", None

@app.route('/', methods=['GET', 'POST'])
def index():
    output = ''
    if request.method == 'POST':
        if 'command' in request.form:
            cmd = request.form['command']
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                output = stdout.decode('utf-8')
            else:
                output = f"Error (Exit Code: {process.returncode}):\n{stderr.decode('utf-8')}"
        elif 'file' in request.files:
            uploaded_file = request.files['file']
            success, message, saved_filename = safe_save_file(uploaded_file)
            output = message

    return render_template_string("""
        <h1>Intentionally Insecure App</h1>
        <form action="/" method="post">
            Run a command: <input type="text" name="command">
            <input type="submit" value="Run">
        </form>
        <br>
        <form action="/" method="post" enctype="multipart/form-data">
            Upload a file: <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
        <pre>{{output}}</pre>
    """, output=output)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
