from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
import whisper
import uuid
import ffmpeg

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
THUMB_FOLDER = os.path.join(UPLOAD_FOLDER, 'thumbs')
os.makedirs(THUMB_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

model = whisper.load_model("base", device="cpu")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return 'No video file part'

    file = request.files['video']
    if file.filename == '':
        return 'No selected file'

    filename = str(uuid.uuid4()) + ".mp4"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Extract frames every 5 seconds
    thumb_pattern = os.path.join(THUMB_FOLDER, 'thumb_%03d.jpg')
    os.system(f"ffmpeg -i {filepath} -vf fps=1/5 {thumb_pattern}")

    # STT
    result = model.transcribe(filepath)
    transcription = result['text']

    return render_template('result.html', transcription=transcription, image_count=len(os.listdir(THUMB_FOLDER)))

@app.route('/thumbs/<filename>')
def thumbs(filename):
    return send_from_directory(THUMB_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
