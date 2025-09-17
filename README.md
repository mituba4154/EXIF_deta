# EXIF_deta

Pythonで写真のEXIFデータをタグごとに選択して出力できるアプリです。

## 概要

このアプリケーションは、写真ファイルからEXIFデータを抽出し、指定したタグのみを表示できるPythonアプリケーションです。JPEG、TIFF、その他のPillowがサポートする画像形式に対応しています。

## 機能

- 写真ファイルからEXIFデータを抽出
- タグごとの選択表示
- 利用可能なタグの一覧表示
- よく使用されるEXIFタグの表示
- タグ名の検索機能
- JSON形式での出力
- GPS情報の処理
- コマンドライン インターフェース

## インストール

### 依存関係のインストール

```bash
# 依存関係をインストール
pip install -r requirements.txt
```

### パッケージとしてのインストール（オプション）

```bash
# 開発用インストール
pip install -e .

# 通常のインストール
pip install .
```

## 使用方法

### 基本的な使用方法

```bash
# すべてのEXIFデータを表示
python exif_viewer.py photo.jpg

# 特定のタグのみを表示
python exif_viewer.py photo.jpg -t DateTime Make Model

# 利用可能なタグを一覧表示
python exif_viewer.py photo.jpg --list-tags

# よく使用されるEXIFタグを表示
python exif_viewer.py --common-tags

# GPS関連のタグを検索
python exif_viewer.py photo.jpg --search GPS

# JSON形式で出力
python exif_viewer.py photo.jpg --format json
```

### オプション

- `image_path`: 画像ファイルのパス
- `-t, --tags`: 表示する特定のEXIFタグ（複数指定可能）
- `--list-tags`: 画像内の利用可能なタグをすべて一覧表示
- `--common-tags`: よく使用されるEXIFタグを表示
- `--search TERM`: 指定した文字列を含むタグを検索
- `--format {table,json}`: 出力形式（デフォルト: table）

### 使用例

```bash
# カメラ情報のみを表示
python exif_viewer.py IMG_001.jpg -t Make Model

# 撮影設定のみを表示
python exif_viewer.py IMG_001.jpg -t ExposureTime FNumber ISOSpeedRatings

# 日時情報のみを表示
python exif_viewer.py IMG_001.jpg -t DateTime

# 解像度関連の情報を検索
python exif_viewer.py IMG_001.jpg --search Resolution

# JSON形式でカメラ情報を出力
python exif_viewer.py IMG_001.jpg -t Make Model --format json
```

## 対応するEXIFタグ（例）

### 基本情報
- `DateTime`: 撮影日時
- `Make`: カメラメーカー
- `Model`: カメラモデル
- `Software`: 使用ソフトウェア

### 画像情報
- `ExifImageWidth`: 画像幅
- `ExifImageHeight`: 画像高さ
- `Orientation`: 画像の向き
- `XResolution`: X方向解像度
- `YResolution`: Y方向解像度
- `ResolutionUnit`: 解像度の単位

### 撮影設定
- `ExposureTime`: 露出時間
- `FNumber`: F値
- `ISOSpeedRatings`: ISO感度
- `FocalLength`: 焦点距離
- `Flash`: フラッシュ設定
- `WhiteBalance`: ホワイトバランス

### GPS情報
- `GPS GPSLatitude`: GPS緯度
- `GPS GPSLongitude`: GPS経度
- その他のGPS関連タグ

## サポートされる画像形式

- JPEG
- TIFF
- その他Pillowライブラリがサポートする形式

## 動作要件

- Python 3.6以上
- Pillow (PIL) 10.0.0以上

## エラーハンドリング

- 存在しないファイルの場合は適切なエラーメッセージを表示
- EXIFデータが存在しない画像の場合はその旨を表示
- 読み込みエラーが発生した場合はエラー詳細を表示

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの報告をお待ちしています。