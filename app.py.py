# Mcharive-Edit: 영상 업로드 → 5초 캡처 + STT 결과 표시 (경로 수정 포함)

import os
import subprocess
from flask import Flask, request, render_template_string, send_from_directory, abort
from werkzeug.utils import secure_filename
from faster_whisper import WhisperModel

# 절대 경로로 폴더 지정
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
THUMB_FOLDER = os.path.join(UPLOAD_FOLDER, "thumbs")
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'mkv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(THUMB_FOLDER, exist_ok=True)

# HTML 템플릿
HTML_TEMPLATE = '''
<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8">
    <title>Mcharive-Edit</title>
    <style>
      body {
        background-color: #f5f0fa;
        font-family: Arial, sans-serif;
        text-align: center;
        color: #4b0082;
      }
      h1 {
        color: #6a0dad;
      }
      .upload-box {
        background-color: #ffffff;
        border: 2px dashed #a275e3;
        padding: 30px;
        width: 60%;
        margin: auto;
        border-radius: 15px;
      }
      .button {
        padding: 10px 20px;
        background-color: #a275e3;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        cursor: pointer;
      }
      .thumbs img {
        margin: 5px;
        width: 200px;
        border: 2px solid #ccc;
        border-radius: 10px;
      }
    </style>
  </head>
  <body>
    <h1>Mcharive-Edit</h1>
    <div class="upload-box">
      <form action="/upload" method="post" enctype="multipart/form-data">
        <p>1시간 이하의 MP4 영상을 업로드하세요 (최대 1GB)</p>
        <input type="file" name="video" accept="video/*" required><br><br>
        <button class="button" type="submit">업로드 및 처리</button>
      </form>
    </div>

    {% if text %}
      <h2>🎤 음성 텍스트</h2>
      <p style="white-space: pre-wrap; padding: 20px;">{{ text }}</p>

      <h2>🖼️ 썸네일 이미지</h2>
      <div class="thumbs">
        {% for thumb in thumbnails %}
          <img src="{{ thumb }}">
        {% endfor %}
      </div>
    {% endif %}
  </body>
</html>
'''

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def limit_upload_size():
    if request.content_length and request.content_length > 1_000_000_000:
        abort(413)

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('video')
    if not file or not allowed_file(file.filename):
        return '지원하지 않는 파일 형식입니다.', 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # 썸네일 폴더 정리 후 추출
    for f in os.listdir(THUMB_FOLDER):
        os.remove(os.path.join(THUMB_FOLDER, f))

    subprocess.run([
        "ffmpeg", "-i", filepath,
        "-vf", "fps=1/5",
        os.path.join(THUMB_FOLDER, "thumb_%03d.jpg")
    ], check=True)

    # STT 수행 (CPU 모드)
    model = WhisperModel("base", compute_type="int8", device="cpu")
    segments, _ = model.transcribe(filepath)
    text = " ".join([s.text for s in segments])

    thumbnails = [f"/thumbs/{img}" for img in sorted(os.listdir(THUMB_FOLDER))]
    return render_template_string(HTML_TEMPLATE, text=text, thumbnails=thumbnails)

@app.route('/thumbs/<path:filename>')
def serve_thumb(filename):
    return send_from_directory(THUMB_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

