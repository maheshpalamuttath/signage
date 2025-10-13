import os
from flask import Flask, jsonify, send_from_directory, request, redirect, url_for, render_template_string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIGNAGE_FOLDER = os.path.join(BASE_DIR, 'signage_media')
URL_FILE = os.path.join(BASE_DIR, 'signage_urls.txt')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = SIGNAGE_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max

# --- HTML Template ---
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Digital Signage Admin</title>
<style>
  body { font-family: Arial, sans-serif; background: #111; color: #eee; padding: 30px; }
  h1 { text-align: center; color: #00d4ff; }
  .section { background: #222; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
  input[type=file], input[type=text] { width: 80%; padding: 8px; border-radius: 5px; border: none; }
  button { padding: 8px 12px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; background: #00d4ff; color: #000; font-weight: bold; }
  ul { list-style-type: none; padding: 0; }
  li { margin: 5px 0; background: #333; padding: 8px; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; }
  a, a:visited { color: #00d4ff; text-decoration: none; }
</style>
</head>
<body>
<h1>📺 Digital Signage Admin Panel</h1>

<div class="section">
  <h2>📤 Upload Media File</h2>
  <form method="POST" action="/upload" enctype="multipart/form-data">
    <input type="file" name="file" required>
    <button type="submit">Upload</button>
  </form>
</div>

<div class="section">
  <h2>🌐 Manage URLs</h2>
  <form method="POST" action="/add_url">
    <input type="text" name="url" placeholder="Enter a URL (e.g. https://example.com)" required>
    <button type="submit">Add URL</button>
  </form>
  <ul>
    {% for url in urls %}
      <li>{{ url }}
        <form style="display:inline" method="POST" action="/delete_url">
          <input type="hidden" name="url" value="{{ url }}">
          <button type="submit">Delete</button>
        </form>
      </li>
    {% endfor %}
  </ul>
</div>

<div class="section">
  <h2>🖼️ Uploaded Media Files</h2>
  <ul>
    {% for file in files %}
      <li>
        <a href="/media/{{ file }}" target="_blank">{{ file }}</a>
        <form style="display:inline" method="POST" action="/delete_file">
          <input type="hidden" name="filename" value="{{ file }}">
          <button type="submit">Delete</button>
        </form>
      </li>
    {% endfor %}
  </ul>
</div>

</body>
</html>
"""

# --- Routes ---
@app.route('/admin')
def admin():
    files = sorted(os.listdir(SIGNAGE_FOLDER))
    urls = []
    if os.path.exists(URL_FILE):
        with open(URL_FILE, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    return render_template_string(ADMIN_HTML, files=files, urls=urls)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    filename = file.filename
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        file.save(save_path)
        os.chmod(save_path, 0o664)
    except Exception as e:
        return f"Error saving file: {e}", 500
    return redirect(url_for('admin'))

@app.route('/add_url', methods=['POST'])
def add_url():
    url = request.form.get('url', '').strip()
    if not url:
        return "URL cannot be empty", 400
    try:
        with open(URL_FILE, 'a') as f:
            f.write(url + '\n')
        os.chmod(URL_FILE, 0o664)
    except Exception as e:
        return f"Error writing URL: {e}", 500
    return redirect(url_for('admin'))

@app.route('/delete_url', methods=['POST'])
def delete_url():
    url_to_delete = request.form.get('url')
    if not url_to_delete:
        return "No URL provided", 400
    if os.path.exists(URL_FILE):
        try:
            with open(URL_FILE, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            urls = [u for u in urls if u != url_to_delete]
            with open(URL_FILE, 'w') as f:
                f.write('\n'.join(urls) + '\n')
            os.chmod(URL_FILE, 0o664)
        except Exception as e:
            return f"Error deleting URL: {e}", 500
    return redirect(url_for('admin'))

@app.route('/delete_file', methods=['POST'])
def delete_file():
    filename = request.form.get('filename')
    if not filename:
        return "No filename provided", 400
    filepath = os.path.join(SIGNAGE_FOLDER, filename)
    if not os.path.exists(filepath):
        return f"File '{filename}' does not exist", 404
    try:
        os.remove(filepath)
    except Exception as e:
        return f"Error deleting file: {e}", 500
    return redirect(url_for('admin'))

@app.route('/files')
def list_files():
    allowed_exts = ('.png', '.jpg', '.jpeg', '.gif', '.mp4')
    files_with_time = [
        (f, os.path.getmtime(os.path.join(SIGNAGE_FOLDER, f)))
        for f in os.listdir(SIGNAGE_FOLDER)
        if f.lower().endswith(allowed_exts)
    ]
    files_sorted = [f for f, _ in sorted(files_with_time, key=lambda x: x[1])]
    return jsonify(files_sorted)

@app.route('/urls')
def list_urls():
    urls = []
    if os.path.exists(URL_FILE):
        with open(URL_FILE, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    return jsonify(urls)

@app.route('/media/<path:filename>')
def media(filename):
    return send_from_directory(SIGNAGE_FOLDER, filename)

@app.route('/')
def index():
    return send_from_directory('.', 'slideshow.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)

