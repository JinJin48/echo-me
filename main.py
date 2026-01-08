"""
Cloud Run エントリーポイント

Flask直接起動方式
"""

import os
import sys
from pathlib import Path

from flask import Flask, request

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cloud_function import main

app = Flask(__name__)


@app.route("/", methods=["POST", "GET"])
def http_handler():
    """HTTP トリガー用ハンドラ"""
    import json

    try:
        result = main(request)
        return json.dumps(result, ensure_ascii=False), 200, {"Content-Type": "application/json"}
    except Exception as e:
        error_response = {
            "error": str(e),
            "status": "error",
        }
        return json.dumps(error_response, ensure_ascii=False), 500, {"Content-Type": "application/json"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
