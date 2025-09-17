#!/usr/bin/env python3
"""
Enhanced EXIF Data Viewer GUI - A web-based graphical interface with backend integration
for extracting and displaying real EXIF data from uploaded photos.
"""

import http.server
import socketserver
import webbrowser
import json
import base64
import urllib.parse
import cgi
from pathlib import Path
from PIL import Image
import io
import threading
import time
import tempfile
import mimetypes
from exif_viewer import EXIFViewer


class EXIFRequestHandler(http.server.BaseHTTPRequestHandler):
    """Custom request handler for EXIF viewer web application."""
    
    def __init__(self, *args, exif_viewer=None, **kwargs):
        self.exif_viewer = exif_viewer or EXIFViewer()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html_content = self.create_html_page()
            self.wfile.write(html_content.encode('utf-8'))
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests for file uploads and EXIF processing."""
        if self.path == "/upload":
            self.handle_upload()
        else:
            self.send_error(404)
    
    def handle_upload(self):
        """Handle file upload and EXIF extraction."""
        try:
            # Parse the multipart form data
            content_type = self.headers['content-type']
            if not content_type.startswith('multipart/form-data'):
                self.send_error(400, "Bad Request: Expected multipart/form-data")
                return
            
            # Get boundary
            boundary = content_type.split("boundary=")[1]
            
            # Read the content
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Parse multipart data
            parts = post_data.split(f'--{boundary}'.encode())
            
            image_data = None
            filename = None
            
            for part in parts:
                if b'Content-Disposition: form-data' in part and b'filename=' in part:
                    # Extract filename
                    lines = part.split(b'\r\n')
                    for line in lines:
                        if b'filename=' in line:
                            filename = line.decode().split('filename=')[1].strip('"')
                            break
                    
                    # Extract image data
                    data_start = part.find(b'\r\n\r\n') + 4
                    if data_start > 3:
                        image_data = part[data_start:-2]  # Remove trailing \r\n
                        break
            
            if not image_data:
                self.send_error(400, "No image file found")
                return
            
            # Save to temporary file and extract EXIF
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            
            try:
                # Extract EXIF data
                exif_data = self.exif_viewer.extract_exif_data(temp_path)
                
                # Create thumbnail for preview
                thumbnail_data = None
                try:
                    with Image.open(temp_path) as img:
                        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                        thumb_io = io.BytesIO()
                        img.save(thumb_io, format='JPEG')
                        thumbnail_data = base64.b64encode(thumb_io.getvalue()).decode('utf-8')
                except Exception:
                    pass
                
                # Prepare response
                response_data = {
                    'success': True,
                    'filename': filename,
                    'exif_data': exif_data or {},
                    'thumbnail': thumbnail_data,
                    'message': f'Successfully loaded {len(exif_data or {})} EXIF tags' if exif_data else 'No EXIF data found in this image'
                }
                
            finally:
                # Clean up temporary file
                Path(temp_path).unlink()
            
            # Send JSON response
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False, indent=2).encode('utf-8'))
            
        except Exception as e:
            # Send error response
            error_response = {
                'success': False,
                'error': str(e),
                'message': 'Failed to process uploaded image'
            }
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def create_html_page(self):
        """Create the HTML page for the web GUI."""
        return """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EXIF Data Viewer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .file-section {
            border: 2px dashed #ddd;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
            background-color: #fafafa;
            transition: border-color 0.3s;
        }
        
        .file-section.dragover {
            border-color: #007bff;
            background-color: #e7f3ff;
        }
        
        .file-input {
            margin: 10px;
            padding: 10px 20px;
            border: none;
            background-color: #007bff;
            color: white;
            border-radius: 4px;
            cursor: pointer;
        }
        
        .file-input:hover {
            background-color: #0056b3;
        }
        
        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
            justify-content: center;
        }
        
        .btn {
            padding: 8px 16px;
            border: 1px solid #ddd;
            background-color: white;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .btn:hover {
            background-color: #f0f0f0;
        }
        
        .btn.primary {
            background-color: #007bff;
            color: white;
            border-color: #007bff;
        }
        
        .btn.primary:hover {
            background-color: #0056b3;
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .search-section {
            margin-bottom: 20px;
            text-align: center;
        }
        
        .search-input {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 200px;
            margin-right: 10px;
        }
        
        .content {
            display: flex;
            gap: 20px;
            margin-top: 20px;
        }
        
        .preview-panel {
            flex: 0 0 300px;
        }
        
        .preview-img {
            max-width: 100%;
            max-height: 300px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        
        .data-panel {
            flex: 1;
        }
        
        .exif-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        
        .exif-table th,
        .exif-table td {
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .exif-table th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        
        .exif-table tr:hover {
            background-color: #f8f9fa;
        }
        
        .status {
            margin-top: 20px;
            padding: 10px;
            background-color: #e9ecef;
            border-radius: 4px;
            font-size: 14px;
        }
        
        .status.success {
            background-color: #d4edda;
            color: #155724;
        }
        
        .status.error {
            background-color: #f8d7da;
            color: #721c24;
        }
        
        .hidden {
            display: none;
        }
        
        .tag-filter {
            margin-bottom: 20px;
        }
        
        .tag-filter textarea {
            width: 100%;
            max-width: 300px;
            height: 100px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            resize: vertical;
        }
        
        .loading {
            text-align: center;
            color: #666;
        }
        
        @media (max-width: 768px) {
            .content {
                flex-direction: column;
            }
            
            .preview-panel {
                flex: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>EXIF Data Viewer</h1>
            <p>写真ファイルからEXIFデータを抽出・表示するアプリケーション</p>
        </div>
        
        <div class="file-section" id="fileSection">
            <p>画像ファイルを選択またはドラッグ&ドロップしてください</p>
            <input type="file" id="fileInput" accept="image/*" class="file-input">
            <div id="fileName" style="margin-top: 10px; color: #666;"></div>
        </div>
        
        <div class="controls">
            <button class="btn primary" onclick="showAllExif()" id="showAllBtn" disabled>すべてのEXIFデータを表示</button>
            <button class="btn" onclick="showCommonTags()" id="commonBtn" disabled>よく使用されるタグを表示</button>
            <button class="btn" onclick="showAvailableTags()" id="availableBtn" disabled>利用可能なタグ一覧</button>
            <button class="btn" onclick="exportJson()" id="exportBtn" disabled>JSON形式でエクスポート</button>
        </div>
        
        <div class="search-section">
            <input type="text" id="searchInput" placeholder="タグを検索..." class="search-input" disabled>
            <button class="btn" onclick="searchTags()" id="searchBtn" disabled>検索</button>
        </div>
        
        <div class="tag-filter">
            <details>
                <summary>タグフィルター</summary>
                <div style="margin-top: 10px;">
                    <p>表示したい特定のタグを入力してください（1行に1つ）:</p>
                    <textarea id="tagFilterInput" placeholder="例:&#10;DateTime&#10;Make&#10;Model" disabled></textarea>
                    <br>
                    <button class="btn" onclick="applyTagFilter()" id="filterBtn" disabled>フィルターを適用</button>
                </div>
            </details>
        </div>
        
        <div class="content">
            <div class="preview-panel">
                <h3>画像プレビュー</h3>
                <div id="imagePreview">
                    <p style="text-align: center; color: #666;">画像が選択されていません</p>
                </div>
            </div>
            
            <div class="data-panel">
                <h3 id="dataTitle">EXIFデータ</h3>
                <div id="exifData">
                    <p style="text-align: center; color: #666;">画像を選択してEXIFデータを表示</p>
                </div>
            </div>
        </div>
        
        <div class="status" id="statusBar">
            準備完了 - 画像を選択してEXIFデータを表示してください
        </div>
    </div>

    <script>
        let currentExifData = null;
        let currentImageFile = null;
        
        // File input change handler
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                handleFile(file);
            }
        });
        
        // Drag and drop handlers
        const fileSection = document.getElementById('fileSection');
        
        fileSection.addEventListener('dragover', function(e) {
            e.preventDefault();
            fileSection.classList.add('dragover');
        });
        
        fileSection.addEventListener('dragleave', function(e) {
            e.preventDefault();
            fileSection.classList.remove('dragover');
        });
        
        fileSection.addEventListener('drop', function(e) {
            e.preventDefault();
            fileSection.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });
        
        // Handle file upload and processing
        function handleFile(file) {
            currentImageFile = file;
            document.getElementById('fileName').textContent = file.name;
            
            // Show loading state
            updateStatus('ファイルをアップロード中...', 'loading');
            disableControls();
            
            // Create FormData for upload
            const formData = new FormData();
            formData.append('image', file);
            
            // Upload and process
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentExifData = data.exif_data;
                    
                    // Update preview
                    if (data.thumbnail) {
                        const img = document.createElement('img');
                        img.src = 'data:image/jpeg;base64,' + data.thumbnail;
                        img.className = 'preview-img';
                        img.alt = 'Image preview';
                        
                        const previewDiv = document.getElementById('imagePreview');
                        previewDiv.innerHTML = '';
                        previewDiv.appendChild(img);
                    }
                    
                    // Show EXIF data
                    showAllExif();
                    enableControls();
                    updateStatus(data.message, 'success');
                } else {
                    updateStatus('エラー: ' + data.message, 'error');
                    disableControls();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                updateStatus('ファイルの処理中にエラーが発生しました', 'error');
                disableControls();
            });
        }
        
        // Enable/disable controls
        function enableControls() {
            const controls = ['showAllBtn', 'commonBtn', 'availableBtn', 'exportBtn', 
                             'searchInput', 'searchBtn', 'tagFilterInput', 'filterBtn'];
            controls.forEach(id => {
                document.getElementById(id).disabled = false;
            });
        }
        
        function disableControls() {
            const controls = ['showAllBtn', 'commonBtn', 'availableBtn', 'exportBtn', 
                             'searchInput', 'searchBtn', 'tagFilterInput', 'filterBtn'];
            controls.forEach(id => {
                document.getElementById(id).disabled = true;
            });
        }
        
        // Show all EXIF data
        function showAllExif() {
            if (!currentExifData) {
                updateStatus('画像が選択されていないか、EXIFデータがありません', 'error');
                return;
            }
            
            displayExifData(currentExifData, 'すべてのEXIFデータ');
            updateStatus(`${Object.keys(currentExifData).length}個のEXIFタグを表示中`, 'success');
        }
        
        // Show common tags
        function showCommonTags() {
            if (!currentExifData) {
                updateStatus('画像が選択されていないか、EXIFデータがありません', 'error');
                return;
            }
            
            const commonTags = ['DateTime', 'Make', 'Model', 'FocalLength', 'FNumber', 
                               'ExposureTime', 'ISOSpeedRatings', 'Flash', 'WhiteBalance',
                               'ExifImageWidth', 'ExifImageHeight', 'Orientation'];
            const filteredData = {};
            
            for (const tag of commonTags) {
                if (currentExifData[tag] !== undefined) {
                    filteredData[tag] = currentExifData[tag];
                }
            }
            
            displayExifData(filteredData, 'よく使用されるEXIFタグ');
            updateStatus(`${Object.keys(filteredData).length}個のよく使用されるタグを表示中`, 'success');
        }
        
        // Show available tags
        function showAvailableTags() {
            if (!currentExifData) {
                updateStatus('画像が選択されていないか、EXIFデータがありません', 'error');
                return;
            }
            
            const tags = Object.keys(currentExifData).sort();
            let html = '<h4>利用可能なタグ一覧</h4><ol>';
            
            tags.forEach(tag => {
                html += `<li>${tag}</li>`;
            });
            
            html += '</ol>';
            html += `<p>合計: ${tags.length}個のタグ</p>`;
            
            document.getElementById('exifData').innerHTML = html;
            document.getElementById('dataTitle').textContent = '利用可能なタグ一覧';
            updateStatus(`${tags.length}個の利用可能なタグを一覧表示中`, 'success');
        }
        
        // Search tags
        function searchTags() {
            if (!currentExifData) {
                updateStatus('画像が選択されていないか、EXIFデータがありません', 'error');
                return;
            }
            
            const searchTerm = document.getElementById('searchInput').value.trim().toLowerCase();
            if (!searchTerm) {
                updateStatus('検索語を入力してください', 'error');
                return;
            }
            
            const matchingData = {};
            for (const [tag, value] of Object.entries(currentExifData)) {
                if (tag.toLowerCase().includes(searchTerm)) {
                    matchingData[tag] = value;
                }
            }
            
            displayExifData(matchingData, `検索結果: "${searchTerm}"`);
            updateStatus(`"${searchTerm}"を含む${Object.keys(matchingData).length}個のタグが見つかりました`, 'success');
        }
        
        // Apply tag filter
        function applyTagFilter() {
            if (!currentExifData) {
                updateStatus('画像が選択されていないか、EXIFデータがありません', 'error');
                return;
            }
            
            const filterText = document.getElementById('tagFilterInput').value.trim();
            if (!filterText) {
                updateStatus('フィルターするタグを入力してください', 'error');
                return;
            }
            
            const filterTags = filterText.split('\\n').map(tag => tag.trim()).filter(tag => tag);
            const filteredData = {};
            
            for (const tag of filterTags) {
                // Exact match
                if (currentExifData[tag] !== undefined) {
                    filteredData[tag] = currentExifData[tag];
                } else {
                    // Partial match
                    for (const [exifTag, value] of Object.entries(currentExifData)) {
                        if (exifTag.toLowerCase().includes(tag.toLowerCase())) {
                            filteredData[exifTag] = value;
                        }
                    }
                }
            }
            
            displayExifData(filteredData, `フィルター結果 (${filterTags.length}個のタグ)`);
            updateStatus(`フィルター適用: ${Object.keys(filteredData).length}個のマッチングタグが見つかりました`, 'success');
        }
        
        // Display EXIF data in table format
        function displayExifData(data, title) {
            if (!data || Object.keys(data).length === 0) {
                document.getElementById('exifData').innerHTML = '<p>表示するデータがありません</p>';
                document.getElementById('dataTitle').textContent = title;
                return;
            }
            
            let html = '<table class="exif-table">';
            html += '<thead><tr><th>タグ</th><th>値</th></tr></thead>';
            html += '<tbody>';
            
            // Sort tags for consistent display
            const sortedTags = Object.keys(data).sort();
            
            for (const tag of sortedTags) {
                const value = data[tag];
                const displayValue = (value !== null && value !== undefined) ? String(value) : '';
                html += `<tr><td>${tag}</td><td>${displayValue}</td></tr>`;
            }
            
            html += '</tbody></table>';
            
            document.getElementById('exifData').innerHTML = html;
            document.getElementById('dataTitle').textContent = `${title} (${Object.keys(data).length}個のタグ)`;
        }
        
        // Export as JSON
        function exportJson() {
            if (!currentExifData) {
                updateStatus('エクスポートするデータがありません', 'error');
                return;
            }
            
            // Get currently displayed data
            const tableRows = document.querySelectorAll('.exif-table tbody tr');
            const exportData = {};
            
            tableRows.forEach(row => {
                const cells = row.querySelectorAll('td');
                if (cells.length === 2) {
                    exportData[cells[0].textContent] = cells[1].textContent;
                }
            });
            
            if (Object.keys(exportData).length === 0) {
                exportData = currentExifData;
            }
            
            const jsonString = JSON.stringify(exportData, null, 2);
            
            // Create download link
            const blob = new Blob([jsonString], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `exif_data_${currentImageFile ? currentImageFile.name : 'export'}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            updateStatus('EXIFデータをJSONファイルとしてエクスポートしました', 'success');
        }
        
        // Update status bar
        function updateStatus(message, type = '') {
            const statusBar = document.getElementById('statusBar');
            statusBar.textContent = message;
            statusBar.className = 'status ' + type;
        }
        
        // Enter key handler for search input
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchTags();
            }
        });
    </script>
</body>
</html>"""

    def log_message(self, format, *args):
        """Override to reduce log spam."""
        return


class EXIFViewerEnhancedWebServer:
    """Enhanced web-based GUI server for EXIF data viewing with real backend integration."""
    
    def __init__(self, port=8000):
        self.port = port
        self.exif_viewer = EXIFViewer()
        
    def start_server(self):
        """Start the web server."""
        def handler_factory(*args, **kwargs):
            return EXIFRequestHandler(*args, exif_viewer=self.exif_viewer, **kwargs)
        
        with socketserver.TCPServer(("", self.port), handler_factory) as httpd:
            print(f"Enhanced EXIF Viewer GUI サーバーを開始しました: http://localhost:{self.port}")
            print("ブラウザが自動的に開きます...")
            print("サーバーを停止するには Ctrl+C を押してください")
            
            # Open browser after a short delay
            def open_browser():
                time.sleep(1)
                webbrowser.open(f"http://localhost:{self.port}")
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nサーバーを停止しています...")
                return


def main():
    """Main function to start the enhanced web-based GUI application."""
    print("EXIF Data Viewer - Enhanced Web GUI版")
    print("=====================================")
    print("実際のEXIFデータ抽出機能付きの高機能版です")
    
    try:
        # Check if port is available
        server = EXIFViewerEnhancedWebServer(port=8000)
        server.start_server()
    except OSError as e:
        if "Address already in use" in str(e):
            print("ポート8000は既に使用されています。別のポートを試しています...")
            try:
                server = EXIFViewerEnhancedWebServer(port=8001)
                server.start_server()
            except OSError:
                print("利用可能なポートが見つかりません。しばらく待ってから再試行してください。")
        else:
            print(f"サーバーの開始中にエラーが発生しました: {e}")


if __name__ == "__main__":
    main()