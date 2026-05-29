import os
import re
import uuid
import threading
import time
import logging
import traceback
from flask import Flask, request, jsonify, send_file, abort
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ========== HTML مدمج كامل ==========
HTML_CONTENT = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VideoLoader - TEXAS</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&family=Poppins:wght@700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Tajawal', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh; display: flex; align-items: center; justify-content: center;
            padding: 20px; color: #fff; position: relative;
        }
        .bg-particles { position: fixed; top:0; left:0; width:100%; height:100%; z-index:0; overflow:hidden; }
        .particle { position: absolute; border-radius: 50%; background: rgba(255,255,255,0.05); animation: float 15s infinite ease-in-out; }
        @keyframes float { 0%,100%{ transform:translateY(0) rotate(0deg); } 50%{ transform:translateY(-40px) rotate(180deg); } }
        .corner-sh { position: absolute; top:20px; left:20px; z-index:10; display:flex; align-items:center; justify-content:center;
            background: rgba(255,255,255,0.08); backdrop-filter: blur(10px); border-radius:50%; width:50px; height:50px;
            border:1px solid rgba(255,255,255,0.15); box-shadow:0 4px 15px rgba(0,0,0,0.3); text-decoration:none; }
        .corner-sh .heart-icon { position:absolute; font-size:38px; color:#e94560; opacity:0.8; }
        .corner-sh .sh-text { position:relative; z-index:1; font-family:'Poppins',sans-serif; font-weight:900; font-size:14px; color:#fff; text-shadow:0 0 8px rgba(233,69,96,0.8); }
        .container { position:relative; z-index:1; width:100%; max-width:650px; background:rgba(255,255,255,0.05);
            backdrop-filter:blur(20px); border-radius:24px; padding:40px 30px; box-shadow:0 30px 60px rgba(0,0,0,0.4);
            border:1px solid rgba(255,255,255,0.1); text-align:center; animation: fadeInUp 0.8s ease-out; }
        @keyframes fadeInUp { from{opacity:0;transform:translateY(40px);} to{opacity:1;transform:translateY(0);} }
        .brand { font-family:'Poppins',sans-serif; font-size:4rem; font-weight:900; letter-spacing:6px;
            background: linear-gradient(135deg, #e94560, #ff8c00); -webkit-background-clip:text; -webkit-text-fill-color:transparent;
            text-transform:uppercase; margin-bottom:5px; }
        .logo-icon { font-size:48px; margin:15px 0 10px; color:#e94560; }
        h1 { font-weight:900; font-size:2.8rem; margin-bottom:10px; background:linear-gradient(135deg, #e94560, #ff6b6b);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .subtitle { font-size:1.1rem; color:#ccc; margin-bottom:30px; }
        .platform-badges { display:flex; justify-content:center; gap:30px; margin-bottom:30px; flex-wrap:wrap; }
        .badge { background:rgba(255,255,255,0.08); border-radius:16px; padding:12px 24px; font-weight:700;
            display:flex; align-items:center; gap:10px; font-size:1.1rem; border:1px solid rgba(255,255,255,0.15); }
        .badge.instagram i { color:#E1306C; } .badge.tiktok i { color:#69C9D0; }
        .input-group { display:flex; gap:12px; background:rgba(255,255,255,0.07); border-radius:16px; padding:8px;
            border:1px solid rgba(255,255,255,0.1); margin-bottom:20px; }
        .input-group:focus-within { border-color:#e94560; box-shadow:0 0 20px rgba(233,69,96,0.2); }
        #urlInput { flex:1; background:transparent; border:none; padding:16px 20px; font-size:1.1rem; color:#fff;
            font-family:'Tajawal',sans-serif; outline:none; direction:ltr; text-align:left; }
        #urlInput::placeholder { color:#aaa; }
        #downloadBtn { background:linear-gradient(135deg, #e94560, #c23152); border:none; color:white; padding:16px 28px;
            border-radius:12px; font-weight:700; font-size:1.1rem; cursor:pointer; display:flex; align-items:center; gap:8px;
            transition:all 0.3s; font-family:'Tajawal',sans-serif; }
        #downloadBtn:hover { transform:translateY(-2px); box-shadow:0 10px 25px rgba(233,69,96,0.4); }
        #downloadBtn:disabled { opacity:0.5; cursor:not-allowed; transform:none; }
        .progress-container { display:none; margin:20px 0; }
        .progress { background:rgba(255,255,255,0.1); border-radius:20px; height:8px; overflow:hidden; }
        .progress-bar { height:100%; width:0%; background:linear-gradient(90deg, #e94560, #ff6b6b); border-radius:20px; }
        .loading-text { display:flex; align-items:center; justify-content:center; gap:10px; margin-top:10px; color:#ccc; }
        .spinner { width:20px; height:20px; border:3px solid rgba(255,255,255,0.2); border-top-color:#e94560;
            border-radius:50%; animation:spin 0.8s linear infinite; }
        @keyframes spin { to{transform:rotate(360deg);} }
        .result { display:none; margin-top:20px; padding:20px; background:rgba(255,255,255,0.05); border-radius:16px;
            border:1px solid rgba(255,255,255,0.1); }
        .result i { font-size:2.5rem; color:#4CAF50; }
        .result h3 { margin:10px 0 5px; color:#fff; }
        .download-link { display:inline-block; margin-top:15px; background:#4CAF50; color:white; padding:12px 30px;
            border-radius:12px; font-weight:700; text-decoration:none; }
        .download-link:hover { background:#45a049; }
        .error-message { display:none; background:rgba(255,0,0,0.15); border:1px solid rgba(255,0,0,0.3);
            color:#ff8a80; padding:15px; border-radius:12px; margin-top:20px; }
        @media (max-width:600px) { .container { padding:30px 20px; } .brand { font-size:3rem; } h1 { font-size:2rem; }
            .input-group { flex-direction:column; background:none; padding:0; gap:10px; border:none; }
            #urlInput { background:rgba(255,255,255,0.07); border-radius:12px; border:1px solid rgba(255,255,255,0.1); }
            .corner-sh { width:40px; height:40px; top:15px; left:15px; } .corner-sh .heart-icon { font-size:30px; } .corner-sh .sh-text { font-size:12px; } }
    </style>
</head>
<body>
    <div class="bg-particles" id="particles"></div>
    <a href="#" class="corner-sh" title="SH">
        <i class="fas fa-heart heart-icon"></i>
        <span class="sh-text">SH</span>
    </a>
    <div class="container">
        <div class="brand">TEXAS</div>
        <div class="logo-icon">🎬</div>
        <h1>VideoLoader</h1>
        <p class="subtitle">حمل فيديوهات إنستغرام وتيك توك بجودة عالية وبدون علامة مائية</p>
        <div class="platform-badges">
            <div class="badge instagram"><i class="fab fa-instagram"></i> Instagram</div>
            <div class="badge tiktok"><i class="fab fa-tiktok"></i> TikTok</div>
        </div>
        <div class="input-group">
            <input type="text" id="urlInput" placeholder="انسخ رابط الفيديو هنا..." dir="ltr">
            <button id="downloadBtn" onclick="startDownload()"><i class="fas fa-download"></i> تحميل</button>
        </div>
        <div class="progress-container" id="progressContainer">
            <div class="progress"><div class="progress-bar" id="progressBar"></div></div>
            <div class="loading-text"><div class="spinner"></div><span id="statusText">جاري التحميل...</span></div>
        </div>
        <div class="error-message" id="errorMessage"></div>
        <div class="result" id="resultBox">
            <i class="fas fa-check-circle"></i>
            <h3 id="videoTitle"></h3>
            <p style="color:#ccc;">تم التحميل بنجاح!</p>
            <a href="#" class="download-link" id="downloadLink"><i class="fas fa-download"></i> تنزيل الفيديو</a>
        </div>
    </div>
    <script>
        (() => {
            const pc = document.getElementById('particles');
            for (let i = 0; i < 30; i++) {
                const p = document.createElement('div');
                p.classList.add('particle');
                const s = Math.random() * 80 + 20;
                p.style.width = s + 'px';
                p.style.height = s + 'px';
                p.style.left = Math.random() * 100 + '%';
                p.style.top = Math.random() * 100 + '%';
                p.style.animationDelay = Math.random() * 10 + 's';
                pc.appendChild(p);
            }
        })();

        const urlInput = document.getElementById('urlInput');
        const downloadBtn = document.getElementById('downloadBtn');
        const progressContainer = document.getElementById('progressContainer');
        const errorMessage = document.getElementById('errorMessage');
        const resultBox = document.getElementById('resultBox');
        const statusText = document.getElementById('statusText');
        const videoTitle = document.getElementById('videoTitle');
        const downloadLink = document.getElementById('downloadLink');

        function resetUI() {
            errorMessage.style.display = 'none';
            resultBox.style.display = 'none';
            progressContainer.style.display = 'none';
            downloadBtn.disabled = false;
        }

        async function startDownload() {
            const url = urlInput.value.trim();
            if (!url) {
                errorMessage.style.display = 'block';
                errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> يرجى إدخال رابط الفيديو';
                return;
            }
            resetUI();
            downloadBtn.disabled = true;
            progressContainer.style.display = 'block';
            statusText.textContent = 'جاري تحليل الرابط...';

            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                const data = await response.json();

                if (data.success) {
                    statusText.textContent = 'اكتمل التحميل! جاري تجهيز الملف...';
                    try {
                        const fileResp = await fetch(data.download_url);
                        if (!fileResp.ok) throw new Error('الملف لم يعد موجوداً');
                        const blob = await fileResp.blob();
                        const blobUrl = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = blobUrl;
                        a.download = (data.title || 'video') + '.mp4';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(blobUrl);
                        videoTitle.textContent = data.title || 'فيديو';
                        downloadLink.href = data.download_url;
                        downloadLink.setAttribute('download', (data.title || 'video') + '.mp4');
                        resultBox.style.display = 'block';
                        progressContainer.style.display = 'none';
                    } catch (e) {
                        errorMessage.style.display = 'block';
                        errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> فشل تحميل الملف من الخادم. ربما انتهت صلاحية الرابط، أعد المحاولة.';
                    }
                } else {
                    errorMessage.style.display = 'block';
                    errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> ' + (data.error || 'خطأ غير معروف');
                }
            } catch (err) {
                errorMessage.style.display = 'block';
                errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> فشل الاتصال بالخادم';
            } finally {
                downloadBtn.disabled = false;
            }
        }

        urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') startDownload();
        });
    </script>
</body>
</html>
"""

# ========== دوال التحميل ==========
def detect_platform(url):
    if any(d in url for d in ['instagram.com', 'instagr.am']):
        return 'instagram'
    elif any(d in url for d in ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com']):
        return 'tiktok'
    return None

def download_video(url, platform):
    # تنظيف الملفات القديمة جداً (أكثر من 15 دقيقة)
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

    # صيغ لا تحتاج إلى دمج (mp4 واحد)
    opts = {
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'format': 'best[ext=mp4]/best',  # يطلب فيديو MP4 جاهز
        'merge_output_format': None,     # لا حاجة لدمج
        'max_filesize': 100 * 1024 * 1024,
        'noplaylist': True,
        'retries': 3,
        'fragment_retries': 3,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            time.sleep(2)  # انتظر حتى يكتمل الكتابة

            # ابحث عن ملف يحمل المعرف الفريد
            for f in os.listdir(DOWNLOAD_FOLDER):
                if f.startswith(unique_id) and f.endswith(('.mp4', '.mkv', '.webm')):
                    return {'success': True, 'filename': f, 'title': info.get('title', 'video')[:60], 'platform': platform}

            # وإلا خذ أحدث ملف فيديو
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

# ========== المسارات ==========
@app.route('/')
def index():
    return HTML_CONTENT

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
    app.run(host='0.0.0.0', port=port) os
import re
import uuid
import threading
import time
import logging
import traceback
from flask import Flask, request, jsonify, send_file, abort
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# لتخزين اسم التحميل الأصلي لكل معرف فريد
file_metadata = {}

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ========== HTML مدمج ==========
HTML_CONTENT = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VideoLoader - TEXAS</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&family=Poppins:wght@700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Tajawal', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            display: flex; align-items: center; justify-content: center;
            padding: 20px; color: #fff; position: relative;
        }
        .bg-particles { position: fixed; top:0; left:0; width:100%; height:100%; z-index:0; overflow:hidden; }
        .particle { position: absolute; border-radius: 50%; background: rgba(255,255,255,0.05); animation: float 15s infinite ease-in-out; }
        @keyframes float { 0%,100%{ transform:translateY(0) rotate(0deg); } 50%{ transform:translateY(-40px) rotate(180deg); } }
        .corner-sh { position: absolute; top:20px; left:20px; z-index:10; display:flex; align-items:center; justify-content:center;
            background: rgba(255,255,255,0.08); backdrop-filter: blur(10px); border-radius:50%; width:50px; height:50px;
            border:1px solid rgba(255,255,255,0.15); box-shadow:0 4px 15px rgba(0,0,0,0.3); text-decoration:none; }
        .corner-sh .heart-icon { position:absolute; font-size:38px; color:#e94560; opacity:0.8; }
        .corner-sh .sh-text { position:relative; z-index:1; font-family:'Poppins',sans-serif; font-weight:900; font-size:14px; color:#fff; text-shadow:0 0 8px rgba(233,69,96,0.8); }
        .container { position:relative; z-index:1; width:100%; max-width:650px; background:rgba(255,255,255,0.05);
            backdrop-filter:blur(20px); border-radius:24px; padding:40px 30px; box-shadow:0 30px 60px rgba(0,0,0,0.4);
            border:1px solid rgba(255,255,255,0.1); text-align:center; animation: fadeInUp 0.8s ease-out; }
        @keyframes fadeInUp { from{opacity:0;transform:translateY(40px);} to{opacity:1;transform:translateY(0);} }
        .brand { font-family:'Poppins',sans-serif; font-size:4rem; font-weight:900; letter-spacing:6px;
            background: linear-gradient(135deg, #e94560, #ff8c00); -webkit-background-clip:text; -webkit-text-fill-color:transparent;
            text-transform:uppercase; margin-bottom:5px; }
        .logo-icon { font-size:48px; margin:15px 0 10px; color:#e94560; }
        h1 { font-weight:900; font-size:2.8rem; margin-bottom:10px; background:linear-gradient(135deg, #e94560, #ff6b6b);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .subtitle { font-size:1.1rem; color:#ccc; margin-bottom:30px; }
        .platform-badges { display:flex; justify-content:center; gap:30px; margin-bottom:30px; flex-wrap:wrap; }
        .badge { background:rgba(255,255,255,0.08); border-radius:16px; padding:12px 24px; font-weight:700;
            display:flex; align-items:center; gap:10px; font-size:1.1rem; border:1px solid rgba(255,255,255,0.15); }
        .badge.instagram i { color:#E1306C; } .badge.tiktok i { color:#69C9D0; }
        .input-group { display:flex; gap:12px; background:rgba(255,255,255,0.07); border-radius:16px; padding:8px;
            border:1px solid rgba(255,255,255,0.1); margin-bottom:20px; }
        .input-group:focus-within { border-color:#e94560; box-shadow:0 0 20px rgba(233,69,96,0.2); }
        #urlInput { flex:1; background:transparent; border:none; padding:16px 20px; font-size:1.1rem; color:#fff;
            font-family:'Tajawal',sans-serif; outline:none; direction:ltr; text-align:left; }
        #urlInput::placeholder { color:#aaa; }
        #downloadBtn { background:linear-gradient(135deg, #e94560, #c23152); border:none; color:white; padding:16px 28px;
            border-radius:12px; font-weight:700; font-size:1.1rem; cursor:pointer; display:flex; align-items:center; gap:8px;
            transition:all 0.3s; font-family:'Tajawal',sans-serif; }
        #downloadBtn:hover { transform:translateY(-2px); box-shadow:0 10px 25px rgba(233,69,96,0.4); }
        #downloadBtn:disabled { opacity:0.5; cursor:not-allowed; transform:none; }
        .progress-container { display:none; margin:20px 0; }
        .progress { background:rgba(255,255,255,0.1); border-radius:20px; height:8px; overflow:hidden; }
        .progress-bar { height:100%; width:0%; background:linear-gradient(90deg, #e94560, #ff6b6b); border-radius:20px; }
        .loading-text { display:flex; align-items:center; justify-content:center; gap:10px; margin-top:10px; color:#ccc; }
        .spinner { width:20px; height:20px; border:3px solid rgba(255,255,255,0.2); border-top-color:#e94560;
            border-radius:50%; animation:spin 0.8s linear infinite; }
        @keyframes spin { to{transform:rotate(360deg);} }
        .result { display:none; margin-top:20px; padding:20px; background:rgba(255,255,255,0.05); border-radius:16px;
            border:1px solid rgba(255,255,255,0.1); }
        .result i { font-size:2.5rem; color:#4CAF50; }
        .result h3 { margin:10px 0 5px; color:#fff; }
        .download-link { display:inline-block; margin-top:15px; background:#4CAF50; color:white; padding:12px 30px;
            border-radius:12px; font-weight:700; text-decoration:none; }
        .download-link:hover { background:#45a049; }
        .error-message { display:none; background:rgba(255,0,0,0.15); border:1px solid rgba(255,0,0,0.3);
            color:#ff8a80; padding:15px; border-radius:12px; margin-top:20px; }
        @media (max-width:600px) { .container { padding:30px 20px; } .brand { font-size:3rem; } h1 { font-size:2rem; }
            .input-group { flex-direction:column; background:none; padding:0; gap:10px; border:none; }
            #urlInput { background:rgba(255,255,255,0.07); border-radius:12px; border:1px solid rgba(255,255,255,0.1); }
            .corner-sh { width:40px; height:40px; top:15px; left:15px; } .corner-sh .heart-icon { font-size:30px; } .corner-sh .sh-text { font-size:12px; } }
    </style>
</head>
<body>
    <div class="bg-particles" id="particles"></div>
    <a href="#" class="corner-sh" title="SH">
        <i class="fas fa-heart heart-icon"></i>
        <span class="sh-text">SH</span>
    </a>
    <div class="container">
        <div class="brand">TEXAS</div>
        <div class="logo-icon">🎬</div>
        <h1>VideoLoader</h1>
        <p class="subtitle">حمل فيديوهات إنستغرام وتيك توك بجودة عالية وبدون علامة مائية</p>
        <div class="platform-badges">
            <div class="badge instagram"><i class="fab fa-instagram"></i> Instagram</div>
            <div class="badge tiktok"><i class="fab fa-tiktok"></i> TikTok</div>
        </div>
        <div class="input-group">
            <input type="text" id="urlInput" placeholder="انسخ رابط الفيديو هنا..." dir="ltr">
            <button id="downloadBtn" onclick="startDownload()"><i class="fas fa-download"></i> تحميل</button>
        </div>
        <div class="progress-container" id="progressContainer">
            <div class="progress"><div class="progress-bar" id="progressBar"></div></div>
            <div class="loading-text"><div class="spinner"></div><span id="statusText">جاري التحميل...</span></div>
        </div>
        <div class="error-message" id="errorMessage"></div>
        <div class="result" id="resultBox">
            <i class="fas fa-check-circle"></i>
            <h3 id="videoTitle"></h3>
            <p style="color:#ccc;">تم التحميل بنجاح!</p>
            <a href="#" class="download-link" id="downloadLink"><i class="fas fa-download"></i> تنزيل الفيديو</a>
        </div>
    </div>
    <script>
        (() => {
            const pc = document.getElementById('particles');
            for (let i = 0; i < 30; i++) {
                const p = document.createElement('div');
                p.classList.add('particle');
                const s = Math.random() * 80 + 20;
                p.style.width = s + 'px';
                p.style.height = s + 'px';
                p.style.left = Math.random() * 100 + '%';
                p.style.top = Math.random() * 100 + '%';
                p.style.animationDelay = Math.random() * 10 + 's';
                pc.appendChild(p);
            }
        })();

        const urlInput = document.getElementById('urlInput');
        const downloadBtn = document.getElementById('downloadBtn');
        const progressContainer = document.getElementById('progressContainer');
        const errorMessage = document.getElementById('errorMessage');
        const resultBox = document.getElementById('resultBox');
        const statusText = document.getElementById('statusText');
        const videoTitle = document.getElementById('videoTitle');
        const downloadLink = document.getElementById('downloadLink');

        function resetUI() {
            errorMessage.style.display = 'none';
            resultBox.style.display = 'none';
            progressContainer.style.display = 'none';
            downloadBtn.disabled = false;
        }

        async function startDownload() {
            const url = urlInput.value.trim();
            if (!url) {
                errorMessage.style.display = 'block';
                errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> يرجى إدخال رابط الفيديو';
                return;
            }
            resetUI();
            downloadBtn.disabled = true;
            progressContainer.style.display = 'block';
            statusText.textContent = 'جاري تحليل الرابط...';

            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                const data = await response.json();

                if (data.success) {
                    statusText.textContent = 'اكتمل التحميل! جاري تجهيز الملف...';
                    try {
                        const fileResp = await fetch(data.download_url);
                        if (!fileResp.ok) throw new Error('الملف لم يعد موجوداً');
                        const blob = await fileResp.blob();
                        const blobUrl = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = blobUrl;
                        a.download = (data.title || 'video') + '.mp4';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(blobUrl);
                        videoTitle.textContent = data.title || 'فيديو';
                        downloadLink.href = data.download_url;
                        downloadLink.setAttribute('download', (data.title || 'video') + '.mp4');
                        resultBox.style.display = 'block';
                        progressContainer.style.display = 'none';
                    } catch (e) {
                        errorMessage.style.display = 'block';
                        errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> فشل تحميل الملف من الخادم. ربما انتهت صلاحية الرابط، أعد المحاولة.';
                    }
                } else {
                    errorMessage.style.display = 'block';
                    errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> ' + (data.error || 'خطأ غير معروف');
                }
            } catch (err) {
                errorMessage.style.display = 'block';
                errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> فشل الاتصال بالخادم';
            } finally {
                downloadBtn.disabled = false;
            }
        }

        urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') startDownload();
        });
    </script>
</body>
</html>
"""

# ========== دوال التحميل ==========
def detect_platform(url):
    if any(d in url for d in ['instagram.com', 'instagr.am']):
        return 'instagram'
    elif any(d in url for d in ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com']):
        return 'tiktok'
    return None

def download_video(url, platform):
    # تنظيف أي ملفات قديمة جداً (أكثر من 30 دقيقة)
    now = time.time()
    for f in os.listdir(DOWNLOAD_FOLDER):
        fpath = os.path.join(DOWNLOAD_FOLDER, f)
        try:
            if os.path.isfile(fpath) and (now - os.path.getmtime(fpath)) > 1800:
                os.remove(fpath)
        except:
            pass

    unique_id = uuid.uuid4().hex
    output_template = os.path.join(DOWNLOAD_FOLDER, f'{unique_id}_%(title).50s.%(ext)s')

    # خيارات محسنة
    opts = {
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'max_filesize': 100 * 1024 * 1024,
        'noplaylist': True,
        'retries': 3,
        'fragment_retries': 3,
    }
    if platform == 'tiktok':
        opts['format'] = 'bestvideo+bestaudio/best'  # دمج الصوت والفيديو لضمان وجود ملف
    else:
        opts['format'] = 'best[ext=mp4]/best'

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # انتظر قليلاً للتأكد من انتهاء أي عمليات دمج
            time.sleep(2)

            # البحث عن أي ملف فيديو حديث يحتوي على المعرف الفريد
            for f in os.listdir(DOWNLOAD_FOLDER):
                if f.startswith(unique_id) and f.endswith(('.mp4', '.mkv', '.webm', '.mov')):
                    filepath = os.path.join(DOWNLOAD_FOLDER, f)
                    # تخزين العنوان الأصلي
                    file_metadata[unique_id] = {
                        'title': info.get('title', 'video')[:60]
                    }
                    return {
                        'success': True,
                        'filename': f,
                        'title': info.get('title', 'video')[:60],
                        'platform': platform
                    }

            # إذا لم نجد بالمعرف، ابحث عن أحدث ملف فيديو في المجلد
            video_files = []
            for f in os.listdir(DOWNLOAD_FOLDER):
                if f.endswith(('.mp4', '.mkv', '.webm', '.mov')):
                    video_files.append(os.path.join(DOWNLOAD_FOLDER, f))
            if video_files:
                latest_file = max(video_files, key=os.path.getctime)
                # تأكد من أنه حديث (آخر 60 ثانية)
                if time.time() - os.path.getctime(latest_file) < 60:
                    # استخرج الاسم من المسار
                    fname = os.path.basename(latest_file)
                    # حاول استخراج unique_id من الاسم (قد يكون جزءاً منه)
                    file_metadata[fname.split('_')[0]] = {
                        'title': info.get('title', 'video')[:60]
                    }
                    return {
                        'success': True,
                        'filename': fname,
                        'title': info.get('title', 'video')[:60],
                        'platform': platform
                    }
            
            return {'success': False, 'error': 'لم يتم العثور على ملف التحميل بعد المعالجة'}

    except Exception as e:
        logger.error(f"Download error: {traceback.format_exc()}")
        return {'success': False, 'error': f'خطأ أثناء التحميل: {str(e)[:150]}'}

def delete_file_later(filepath, delay=600):
    """حذف الملف بعد delay ثواني (الافتراضي 10 دقائق)"""
    def _delete():
        time.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"تم حذف الملف: {filepath}")
        except Exception as e:
            logger.error(f"خطأ في حذف الملف: {e}")
    threading.Thread(target=_delete, daemon=True).start()

# ========== المسارات ==========
@app.route('/')
def index():
    return HTML_CONTENT

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'yt_dlp_version': yt_dlp.version.__version__})

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
            delete_file_later(filepath, 600)  # 10 دقائق
            return jsonify({
                'success': True,
                'download_url': download_url,
                'title': result['title'],
                'platform': platform
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
    except Exception as e:
        logger.error(f"Download route error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'خطأ غير متوقع: {str(e)}'}), 500

@app.route('/file/<filename>')
def serve_file(filename):
    if '..' in filename or '/' in filename:
        abort(404)
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if not os.path.exists(filepath):
        logger.warning(f"طلب ملف غير موجود: {filename}")
        abort(404)
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)        .bg-particles { position: fixed; top:0; left:0; width:100%; height:100%; z-index:0; overflow:hidden; }
        .particle { position: absolute; border-radius: 50%; background: rgba(255,255,255,0.05); animation: float 15s infinite ease-in-out; }
        @keyframes float { 0%,100%{ transform:translateY(0) rotate(0deg); } 50%{ transform:translateY(-40px) rotate(180deg); } }
        .corner-sh { position: absolute; top:20px; left:20px; z-index:10; display:flex; align-items:center; justify-content:center;
            background: rgba(255,255,255,0.08); backdrop-filter: blur(10px); border-radius:50%; width:50px; height:50px;
            border:1px solid rgba(255,255,255,0.15); box-shadow:0 4px 15px rgba(0,0,0,0.3); text-decoration:none; }
        .corner-sh .heart-icon { position:absolute; font-size:38px; color:#e94560; opacity:0.8; }
        .corner-sh .sh-text { position:relative; z-index:1; font-family:'Poppins',sans-serif; font-weight:900; font-size:14px; color:#fff; text-shadow:0 0 8px rgba(233,69,96,0.8); }
        .container { position:relative; z-index:1; width:100%; max-width:650px; background:rgba(255,255,255,0.05);
            backdrop-filter:blur(20px); border-radius:24px; padding:40px 30px; box-shadow:0 30px 60px rgba(0,0,0,0.4);
            border:1px solid rgba(255,255,255,0.1); text-align:center; animation: fadeInUp 0.8s ease-out; }
        @keyframes fadeInUp { from{opacity:0;transform:translateY(40px);} to{opacity:1;transform:translateY(0);} }
        .brand { font-family:'Poppins',sans-serif; font-size:4rem; font-weight:900; letter-spacing:6px;
            background: linear-gradient(135deg, #e94560, #ff8c00); -webkit-background-clip:text; -webkit-text-fill-color:transparent;
            text-transform:uppercase; margin-bottom:5px; }
        .logo-icon { font-size:48px; margin:15px 0 10px; color:#e94560; }
        h1 { font-weight:900; font-size:2.8rem; margin-bottom:10px; background:linear-gradient(135deg, #e94560, #ff6b6b);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
        .subtitle { font-size:1.1rem; color:#ccc; margin-bottom:30px; }
        .platform-badges { display:flex; justify-content:center; gap:30px; margin-bottom:30px; flex-wrap:wrap; }
        .badge { background:rgba(255,255,255,0.08); border-radius:16px; padding:12px 24px; font-weight:700;
            display:flex; align-items:center; gap:10px; font-size:1.1rem; border:1px solid rgba(255,255,255,0.15); }
        .badge.instagram i { color:#E1306C; } .badge.tiktok i { color:#69C9D0; }
        .input-group { display:flex; gap:12px; background:rgba(255,255,255,0.07); border-radius:16px; padding:8px;
            border:1px solid rgba(255,255,255,0.1); margin-bottom:20px; }
        .input-group:focus-within { border-color:#e94560; box-shadow:0 0 20px rgba(233,69,96,0.2); }
        #urlInput { flex:1; background:transparent; border:none; padding:16px 20px; font-size:1.1rem; color:#fff;
            font-family:'Tajawal',sans-serif; outline:none; direction:ltr; text-align:left; }
        #urlInput::placeholder { color:#aaa; }
        #downloadBtn { background:linear-gradient(135deg, #e94560, #c23152); border:none; color:white; padding:16px 28px;
            border-radius:12px; font-weight:700; font-size:1.1rem; cursor:pointer; display:flex; align-items:center; gap:8px;
            transition:all 0.3s; font-family:'Tajawal',sans-serif; }
        #downloadBtn:hover { transform:translateY(-2px); box-shadow:0 10px 25px rgba(233,69,96,0.4); }
        #downloadBtn:disabled { opacity:0.5; cursor:not-allowed; transform:none; }
        .progress-container { display:none; margin:20px 0; }
        .progress { background:rgba(255,255,255,0.1); border-radius:20px; height:8px; overflow:hidden; }
        .progress-bar { height:100%; width:0%; background:linear-gradient(90deg, #e94560, #ff6b6b); border-radius:20px; }
        .loading-text { display:flex; align-items:center; justify-content:center; gap:10px; margin-top:10px; color:#ccc; }
        .spinner { width:20px; height:20px; border:3px solid rgba(255,255,255,0.2); border-top-color:#e94560;
            border-radius:50%; animation:spin 0.8s linear infinite; }
        @keyframes spin { to{transform:rotate(360deg);} }
        .result { display:none; margin-top:20px; padding:20px; background:rgba(255,255,255,0.05); border-radius:16px;
            border:1px solid rgba(255,255,255,0.1); }
        .result i { font-size:2.5rem; color:#4CAF50; }
        .result h3 { margin:10px 0 5px; color:#fff; }
        .download-link { display:inline-block; margin-top:15px; background:#4CAF50; color:white; padding:12px 30px;
            border-radius:12px; font-weight:700; text-decoration:none; }
        .download-link:hover { background:#45a049; }
        .error-message { display:none; background:rgba(255,0,0,0.15); border:1px solid rgba(255,0,0,0.3);
            color:#ff8a80; padding:15px; border-radius:12px; margin-top:20px; }
        @media (max-width:600px) { .container { padding:30px 20px; } .brand { font-size:3rem; } h1 { font-size:2rem; }
            .input-group { flex-direction:column; background:none; padding:0; gap:10px; border:none; }
            #urlInput { background:rgba(255,255,255,0.07); border-radius:12px; border:1px solid rgba(255,255,255,0.1); }
            .corner-sh { width:40px; height:40px; top:15px; left:15px; } .corner-sh .heart-icon { font-size:30px; } .corner-sh .sh-text { font-size:12px; } }
    </style>
</head>
<body>
    <div class="bg-particles" id="particles"></div>
    <a href="#" class="corner-sh" title="SH">
        <i class="fas fa-heart heart-icon"></i>
        <span class="sh-text">SH</span>
    </a>
    <div class="container">
        <div class="brand">TEXAS</div>
        <div class="logo-icon">🎬</div>
        <h1>VideoLoader</h1>
        <p class="subtitle">حمل فيديوهات إنستغرام وتيك توك بجودة عالية وبدون علامة مائية</p>
        <div class="platform-badges">
            <div class="badge instagram"><i class="fab fa-instagram"></i> Instagram</div>
            <div class="badge tiktok"><i class="fab fa-tiktok"></i> TikTok</div>
        </div>
        <div class="input-group">
            <input type="text" id="urlInput" placeholder="انسخ رابط الفيديو هنا..." dir="ltr">
            <button id="downloadBtn" onclick="startDownload()"><i class="fas fa-download"></i> تحميل</button>
        </div>
        <div class="progress-container" id="progressContainer">
            <div class="progress"><div class="progress-bar" id="progressBar"></div></div>
            <div class="loading-text"><div class="spinner"></div><span id="statusText">جاري التحميل...</span></div>
        </div>
        <div class="error-message" id="errorMessage"></div>
        <div class="result" id="resultBox">
            <i class="fas fa-check-circle"></i>
            <h3 id="videoTitle"></h3>
            <p style="color:#ccc;">تم التحميل بنجاح!</p>
            <a href="#" class="download-link" id="downloadLink"><i class="fas fa-download"></i> تنزيل الفيديو</a>
        </div>
    </div>
    <script>
        (() => {
            const pc = document.getElementById('particles');
            for (let i = 0; i < 30; i++) {
                const p = document.createElement('div');
                p.classList.add('particle');
                const s = Math.random() * 80 + 20;
                p.style.width = s + 'px';
                p.style.height = s + 'px';
                p.style.left = Math.random() * 100 + '%';
                p.style.top = Math.random() * 100 + '%';
                p.style.animationDelay = Math.random() * 10 + 's';
                pc.appendChild(p);
            }
        })();

        const urlInput = document.getElementById('urlInput');
        const downloadBtn = document.getElementById('downloadBtn');
        const progressContainer = document.getElementById('progressContainer');
        const errorMessage = document.getElementById('errorMessage');
        const resultBox = document.getElementById('resultBox');
        const statusText = document.getElementById('statusText');
        const videoTitle = document.getElementById('videoTitle');
        const downloadLink = document.getElementById('downloadLink');

        function resetUI() {
            errorMessage.style.display = 'none';
            resultBox.style.display = 'none';
            progressContainer.style.display = 'none';
            downloadBtn.disabled = false;
        }

        async function startDownload() {
            const url = urlInput.value.trim();
            if (!url) {
                errorMessage.style.display = 'block';
                errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> يرجى إدخال رابط الفيديو';
                return;
            }
            resetUI();
            downloadBtn.disabled = true;
            progressContainer.style.display = 'block';
            statusText.textContent = 'جاري تحليل الرابط...';

            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
                const data = await response.json();
                if (data.success) {
                    statusText.textContent = 'اكتمل التحميل! جاري التجهيز...';
                    try {
                        const fileResp = await fetch(data.download_url);
                        if (!fileResp.ok) throw new Error('فشل جلب الملف');
                        const blob = await fileResp.blob();
                        const blobUrl = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = blobUrl;
                        a.download = (data.title || 'video') + '.mp4';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(blobUrl);
                        videoTitle.textContent = data.title || 'فيديو';
                        downloadLink.href = data.download_url;
                        downloadLink.setAttribute('download', (data.title || 'video') + '.mp4');
                        resultBox.style.display = 'block';
                        progressContainer.style.display = 'none';
                    } catch (e) {
                        errorMessage.style.display = 'block';
                        errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> فشل تحميل الملف من الخادم';
                    }
                } else {
                    errorMessage.style.display = 'block';
                    errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> ' + (data.error || 'خطأ غير معروف');
                }
            } catch (err) {
                errorMessage.style.display = 'block';
                errorMessage.innerHTML = '<i class="fas fa-exclamation-triangle"></i> فشل الاتصال بالخادم';
            } finally {
                downloadBtn.disabled = false;
                if (progressContainer.style.display !== 'none' && !errorMessage.style.display) {
                    // leave
                }
            }
        }

        urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') startDownload();
        });
    </script>
</body>
</html>
"""

# ========== وظائف التحميل ==========
def detect_platform(url):
    if any(d in url for d in ['instagram.com', 'instagr.am']):
        return 'instagram'
    elif any(d in url for d in ['tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com']):
        return 'tiktok'
    return None

def download_video(url, platform):
    output_template = os.path.join(DOWNLOAD_FOLDER, f'{uuid.uuid4().hex}_%(title).50s.%(ext)s')
    opts = {
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'format': 'best[ext=mp4]/best',
        'merge_output_format': None,
        'max_filesize': 100 * 1024 * 1024,
        'noplaylist': True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            for f in os.listdir(DOWNLOAD_FOLDER):
                if f.endswith('.mp4'):
                    return {'success': True, 'filename': f, 'title': info.get('title', 'video')[:60], 'platform': platform}
            for f in os.listdir(DOWNLOAD_FOLDER):
                if f.endswith(('.webm', '.mkv')):
                    return {'success': True, 'filename': f, 'title': info.get('title', 'video')[:60], 'platform': platform}
            return {'success': False, 'error': 'لم يتم العثور على ملف التحميل'}
    except Exception as e:
        logger.error(f"Download error: {traceback.format_exc()}")
        return {'success': False, 'error': str(e)[:200]}

def delete_file_later(filepath, delay=300):
    def _delete():
        time.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass
    threading.Thread(target=_delete, daemon=True).start()

# ========== المسارات ==========
@app.route('/')
def index():
    return HTML_CONTENT

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'yt_dlp_version': yt_dlp.version.__version__})

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
        logger.info(f"Downloading {platform}: {url}")
        result = download_video(url, platform)
        if result['success']:
            filepath = os.path.join(DOWNLOAD_FOLDER, result['filename'])
            download_url = f"/file/{result['filename']}"
            delete_file_later(filepath, 300)
            return jsonify({'success': True, 'download_url': download_url, 'title': result['title'], 'platform': platform})
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
    except Exception as e:
        logger.error(f"Download route error: {traceback.format_exc()}")
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
