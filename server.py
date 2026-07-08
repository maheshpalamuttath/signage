import os
from flask import Flask, jsonify, send_from_directory, request, redirect, url_for, render_template_string, session
from werkzeug.utils import secure_filename
from functools import wraps

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SIGNAGE_FOLDER = os.path.join(BASE_DIR, 'signage_media')
OVERLAY_FOLDER = os.path.join(BASE_DIR, 'overlay_media')
URL_FILE = os.path.join(BASE_DIR, 'signage_urls.txt')

ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif','mp4'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = SIGNAGE_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max

# 🔐 Security
app.secret_key = "change_this_to_a_random_secret_key"

USERNAME = "admin"
PASSWORD = "admin123"

# Create folders if not exist
for folder in [SIGNAGE_FOLDER, OVERLAY_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# ---------------- AUTH ----------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Login</title>
<style>
body {
    background: #f1f1f1;
    font-family: Arial;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
}
.login-box {
    background: white;
    padding: 40px;
    width: 320px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
    text-align: center;
}
h2 { margin-bottom: 20px; }
input {
    width: 90%;
    padding: 10px;
    margin: 8px 0;
}
button {
    width: 100%;
    padding: 10px;
    background: #2271b1;
    color: white;
    border: none;
    cursor: pointer;
}
button:hover { background: #135e96; }
</style>
</head>
<body>
<div class="login-box">
<h2>Campus Digital Signage</h2>
<h3> Admin Login</h3>
<form method="POST">
<input type="text" name="username" placeholder="Username" required>
<input type="password" name="password" placeholder="Password" required>
<button type="submit">Login</button>
</form>
</div>
</body>
</html>
"""

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')

        if u == USERNAME and p == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        return "Invalid credentials", 403

    return render_template_string(LOGIN_HTML)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------- ADMIN HTML ----------------
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Digital Signage Admin</title>
<style>
body { font-family: Arial; background:#111; color:#eee; padding:30px; }
h1 { text-align:center; color:#00d4ff; }
.section { background:#222; padding:20px; border-radius:10px; margin-bottom:20px; }
input[type=file], input[type=text] {
    width:80%; padding:8px; border-radius:5px; border:none;
}
button {
    padding:8px 12px; margin:5px;
    border:none; border-radius:5px;
    cursor:pointer;
    background:#00d4ff; color:#000; font-weight:bold;
}
ul { list-style:none; padding:0; }
li {
    margin:5px 0; background:#333;
    padding:8px; border-radius:5px;
    display:flex; justify-content:space-between;
}
a { color:#00d4ff; text-decoration:none; }
</style>
</head>
<body>

<h1>📺 Digital Signage Admin Panel</h1>

<p style="text-align:center;">
<a href="/logout">Logout</a>
</p>

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
<input type="text" name="url" placeholder="Enter URL" required>
<button type="submit">Add URL</button>
</form>

<ul>
{% for url in urls %}
<li>
{{ url }}
<form method="POST" action="/delete_url">
<input type="hidden" name="url" value="{{ url }}">
<button>Delete</button>
</form>
</li>
{% endfor %}
</ul>
</div>

<div class="section">
<h2>🖼️ Uploaded Media</h2>
<ul>
{% for file in files %}
<li>
<a href="/media/{{ file }}" target="_blank">{{ file }}</a>
<form method="POST" action="/delete_file">
<input type="hidden" name="filename" value="{{ file }}">
<button>Delete</button>
</form>
</li>
{% endfor %}
</ul>
</div>

</body>
</html>
"""

# ---------------- HELPERS ----------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------- ROUTES ----------------
@app.route('/admin')
@login_required
def admin():
    files = sorted(os.listdir(SIGNAGE_FOLDER))
    urls = []
    if os.path.exists(URL_FILE):
        with open(URL_FILE,'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    return render_template_string(ADMIN_HTML, files=files, urls=urls)


@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    file = request.files.get('file')
    if not file or file.filename == '':
        return "Invalid file", 400

    if not allowed_file(file.filename):
        return "Not allowed", 400

    filename = secure_filename(file.filename)
    path = os.path.join(SIGNAGE_FOLDER, filename)

    file.save(path)
    os.chmod(path, 0o664)
    return redirect(url_for('admin'))


@app.route('/add_url', methods=['POST'])
@login_required
def add_url():
    url = request.form.get('url','').strip()
    if not url:
        return "Empty URL", 400

    with open(URL_FILE,'a') as f:
        f.write(url + "\n")

    os.chmod(URL_FILE, 0o664)
    return redirect(url_for('admin'))


@app.route('/delete_url', methods=['POST'])
@login_required
def delete_url():
    url = request.form.get('url')

    if os.path.exists(URL_FILE):
        with open(URL_FILE,'r') as f:
            urls = [u.strip() for u in f if u.strip()]

        urls = [u for u in urls if u != url]

        with open(URL_FILE,'w') as f:
            f.write("\n".join(urls) + "\n")

    return redirect(url_for('admin'))


@app.route('/delete_file', methods=['POST'])
@login_required
def delete_file():
    filename = request.form.get('filename')
    path = os.path.join(SIGNAGE_FOLDER, filename)

    if os.path.exists(path):
        os.remove(path)

    return redirect(url_for('admin'))


@app.route('/files')
def list_files():
    return jsonify([f for f in os.listdir(SIGNAGE_FOLDER) if allowed_file(f)])


@app.route('/urls')
def list_urls():
    if not os.path.exists(URL_FILE):
        return jsonify([])
    with open(URL_FILE,'r') as f:
        return jsonify([line.strip() for line in f if line.strip()])


@app.route('/media/<path:filename>')
def media(filename):
    return send_from_directory(SIGNAGE_FOLDER, filename)


@app.route('/overlay_media/<path:filename>')
def overlay_media(filename):
    return send_from_directory(OVERLAY_FOLDER, filename)


@app.route('/')
def index():
    return send_from_directory('.', 'slideshow.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
