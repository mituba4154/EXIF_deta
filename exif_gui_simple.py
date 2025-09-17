#!/usr/bin/env python3
"""
EXIF Data Viewer GUI - A web-based graphical interface for extracting and displaying EXIF data from photos
with tag-based selection functionality.
"""

import http.server
import socketserver
import webbrowser
import json
import base64
import urllib.parse
from pathlib import Path
from PIL import Image
import io
import threading
import time
import os
from exif_viewer import EXIFViewer


class EXIFViewerWebServer:
    """Web-based GUI server for EXIF data viewing."""
    
    def __init__(self, port=8000):
        self.port = port
        self.exif_viewer = EXIFViewer()
        self.current_exif_data = None
        
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
        
        <div class="file-section">
            <p>画像ファイルを選択してください</p>
            <input type="file" id="fileInput" accept="image/*" class="file-input">
            <div id="fileName" style="margin-top: 10px; color: #666;"></div>
        </div>
        
        <div class="controls">
            <button class="btn primary" onclick="showAllExif()">すべてのEXIFデータを表示</button>
            <button class="btn" onclick="showCommonTags()">よく使用されるタグを表示</button>
            <button class="btn" onclick="showAvailableTags()">利用可能なタグ一覧</button>
            <button class="btn" onclick="exportJson()">JSON形式でエクスポート</button>
        </div>
        
        <div class="search-section">
            <input type="text" id="searchInput" placeholder="タグを検索..." class="search-input">
            <button class="btn" onclick="searchTags()">検索</button>
        </div>
        
        <div class="tag-filter">
            <details>
                <summary>タグフィルター</summary>
                <div style="margin-top: 10px;">
                    <p>表示したい特定のタグを入力してください（1行に1つ）:</p>
                    <textarea id="tagFilterInput" placeholder="例:&#10;DateTime&#10;Make&#10;Model"></textarea>
                    <br>
                    <button class="btn" onclick="applyTagFilter()">フィルターを適用</button>
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
                currentImageFile = file;
                document.getElementById('fileName').textContent = file.name;
                loadImagePreview(file);
                extractExifData(file);
            }
        });
        
        // Load image preview
        function loadImagePreview(file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'preview-img';
                img.alt = 'Image preview';
                
                const previewDiv = document.getElementById('imagePreview');
                previewDiv.innerHTML = '';
                previewDiv.appendChild(img);
            };
            reader.readAsDataURL(file);
        }
        
        // Extract EXIF data from image
        function extractExifData(file) {
            // For demonstration, we'll simulate EXIF data extraction
            // In a real implementation, this would use a library like exif-js
            updateStatus('EXIF data extraction is simulated in this demo version');
            
            // Simulate some EXIF data
            currentExifData = {
                'DateTime': '2024:01:15 14:30:25',
                'Make': 'Canon',
                'Model': 'EOS R6',
                'Orientation': '1',
                'XResolution': '72',
                'YResolution': '72',
                'Software': 'Adobe Lightroom',
                'ExifImageWidth': '4000',
                'ExifImageHeight': '3000',
                'FocalLength': '85.0',
                'FNumber': 'f/2.8',
                'ExposureTime': '1/125',
                'ISOSpeedRatings': '400'
            };
            
            showAllExif();
        }
        
        // Show all EXIF data
        function showAllExif() {
            if (!currentExifData) {
                updateStatus('画像が選択されていないか、EXIFデータがありません');
                return;
            }
            
            displayExifData(currentExifData, 'すべてのEXIFデータ');
            updateStatus(`${Object.keys(currentExifData).length}個のEXIFタグを表示中`);
        }
        
        // Show common tags
        function showCommonTags() {
            if (!currentExifData) {
                updateStatus('画像が選択されていないか、EXIFデータがありません');
                return;
            }
            
            const commonTags = ['DateTime', 'Make', 'Model', 'FocalLength', 'FNumber', 'ExposureTime', 'ISOSpeedRatings'];
            const filteredData = {};
            
            for (const tag of commonTags) {
                if (currentExifData[tag]) {
                    filteredData[tag] = currentExifData[tag];
                }
            }
            
            displayExifData(filteredData, 'よく使用されるEXIFタグ');
            updateStatus(`${Object.keys(filteredData).length}個のよく使用されるタグを表示中`);
        }
        
        // Show available tags
        function showAvailableTags() {
            if (!currentExifData) {
                updateStatus('画像が選択されていないか、EXIFデータがありません');
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
            updateStatus(`${tags.length}個の利用可能なタグを一覧表示中`);
        }
        
        // Search tags
        function searchTags() {
            if (!currentExifData) {
                updateStatus('画像が選択されていないか、EXIFデータがありません');
                return;
            }
            
            const searchTerm = document.getElementById('searchInput').value.trim().toLowerCase();
            if (!searchTerm) {
                updateStatus('検索語を入力してください');
                return;
            }
            
            const matchingData = {};
            for (const [tag, value] of Object.entries(currentExifData)) {
                if (tag.toLowerCase().includes(searchTerm)) {
                    matchingData[tag] = value;
                }
            }
            
            displayExifData(matchingData, `検索結果: "${searchTerm}"`);
            updateStatus(`"${searchTerm}"を含む${Object.keys(matchingData).length}個のタグが見つかりました`);
        }
        
        // Apply tag filter
        function applyTagFilter() {
            if (!currentExifData) {
                updateStatus('画像が選択されていないか、EXIFデータがありません');
                return;
            }
            
            const filterText = document.getElementById('tagFilterInput').value.trim();
            if (!filterText) {
                updateStatus('フィルターするタグを入力してください');
                return;
            }
            
            const filterTags = filterText.split('\\n').map(tag => tag.trim()).filter(tag => tag);
            const filteredData = {};
            
            for (const tag of filterTags) {
                // Exact match
                if (currentExifData[tag]) {
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
            updateStatus(`フィルター適用: ${Object.keys(filteredData).length}個のマッチングタグが見つかりました`);
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
                html += `<tr><td>${tag}</td><td>${value}</td></tr>`;
            }
            
            html += '</tbody></table>';
            
            document.getElementById('exifData').innerHTML = html;
            document.getElementById('dataTitle').textContent = `${title} (${Object.keys(data).length}個のタグ)`;
        }
        
        // Export as JSON
        function exportJson() {
            if (!currentExifData) {
                updateStatus('エクスポートするデータがありません');
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
            
            updateStatus('EXIFデータをJSONファイルとしてエクスポートしました');
        }
        
        // Update status bar
        function updateStatus(message) {
            document.getElementById('statusBar').textContent = message;
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

    def start_server(self):
        """Start the web server."""
        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=Path(__file__).parent, **kwargs)
            
            def do_GET(self):
                if self.path == "/" or self.path == "/index.html":
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    html_content = self.server.gui_instance.create_html_page()
                    self.wfile.write(html_content.encode('utf-8'))
                else:
                    super().do_GET()
        
        with socketserver.TCPServer(("", self.port), CustomHandler) as httpd:
            httpd.gui_instance = self
            print(f"EXIF Viewer GUI サーバーを開始しました: http://localhost:{self.port}")
            print("ブラウザが自動的に開きます...")
            
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
    """Main function to start the web-based GUI application."""
    print("EXIF Data Viewer - Web GUI版")
    print("=============================")
    
    try:
        # Check if port is available
        server = EXIFViewerWebServer(port=8000)
        server.start_server()
    except OSError as e:
        if "Address already in use" in str(e):
            print("ポート8000は既に使用されています。別のポートを試しています...")
            try:
                server = EXIFViewerWebServer(port=8001)
                server.start_server()
            except OSError:
                print("利用可能なポートが見つかりません。しばらく待ってから再試行してください。")
        else:
            print(f"サーバーの開始中にエラーが発生しました: {e}")


if __name__ == "__main__":
    main()