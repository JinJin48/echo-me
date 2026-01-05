"""
Cloud Run エントリーポイント

Google Cloud Buildpacksが認識するmain.py
実際の処理はsrc/cloud_function.pyに委譲する
"""

import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cloud_function import http_handler, pubsub_handler, main

# Cloud Run / Cloud Functions用のエントリーポイント
app = http_handler

__all__ = ["http_handler", "pubsub_handler", "main", "app"]
