import os
import re
import uuid
import threading
import time
import logging
import traceback
from flask import Flask, render_template, request, jsonify, send_file, abort
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def detect_platform(url):
    if any(d in url for d in ['instagram.com', 'instagr.am']):
        return 'instagram'
    elif any(d in url for d in ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com']):
        return 'tiktok'
    return None

def download_video(url, platform):
    now = time.time()
    for f in os.listdir(DOWNLOAD_FOLDER):
        fpath = os.path.join(DOWNLOAD_FOLDER, f)
        try:
            if os.path.isfile(fpath) and (now - os.path.getmtime(fpath)) > 900:
                os.remove(fpath)
        except:
            pass

    unique_id = uuid.uuid4().hex
    output_template = os.path.join(DOWNLOAD_FOLDER, f'{unique_id}_%(title).50s.%(ext)s')

    opts = {
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'format': 'best[ext=mp4]/best',
        'merge_output_format': None,
        'max_filesize': 100 * 1024 * 1024,
        'noplaylist': True,
        'retries': 3,
        'fragment_retries': 3,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            time.sleep(2)
            for f in os.listdir(DOWNLOAD_FOLDER):
                if f.startswith(unique_id) and f.endswith(('.mp4', '.mkv', '.webm')):
                    return {'success': True, 'filename': f, 'title': info.get('title', 'video')[:60], 'platform': platform}
            video_files = []
            for f in os.listdir(DOWNLOAD_FOLDER):
                if f.endswith(('.mp4', '.mkv', '.webm')):
                    video_files.append(os.path.join(DOWNLOAD_FOLDER, f))
            if video_files:
                latest = max(video_files, key=os.path.getctime)
                if time.time() - os.path.getctime(latest) < 60:
                    return {'success': True, 'filename': os.path.basename(latest), 'title': info.get('title', 'video')[:60], 'platform': platform}
            return {'success': False, 'error': 'لم يتم العثور على ملف التحميل'}
    except Exception as e:
        logger.error(f"Download error: {traceback.format_exc()}")
        return {'success': False, 'error': f'خطأ أثناء التحميل: {str(e)[:150]}'}

def delete_file_later(filepath, delay=600):
    def _delete():
        time.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass
    threading.Thread(target=_delete, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': 'يرجى إرسال الرابط'}), 400
        url = data['url'].strip()
        platform = detect_platform(url)
        if not platform:
            return jsonify({'success': False, 'error': 'المنصة غير مدعومة'}), 400
        logger.info(f"تحميل {platform}: {url}")
        result = download_video(url, platform)
        if result['success']:
            filepath = os.path.join(DOWNLOAD_FOLDER, result['filename'])
            download_url = f"/file/{result['filename']}"
            delete_file_later(filepath, 600)
            return jsonify({'success': True, 'download_url': download_url, 'title': result['title'], 'platform': platform})
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
    except Exception as e:
        logger.error(f"Route error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'خطأ غير متوقع: {str(e)}'}), 500

@app.route('/file/<filename>')
def serve_file(filename):
    if '..' in filename or '/' in filename:
        abort(404)
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        abort(404)
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
