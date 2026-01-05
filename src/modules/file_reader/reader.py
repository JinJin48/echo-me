"""
file_reader モジュール

様々な形式のファイルからテキストを読み込む
"""

from pathlib import Path
from typing import Optional


def read_file(filepath: str) -> str:
    """ファイルを読み込んでテキストを返す

    Args:
        filepath: 読み込むファイルのパス

    Returns:
        ファイルの内容（テキスト）

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        ValueError: サポートされていないファイル形式の場合
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {filepath}")

    suffix = path.suffix.lower()

    if suffix in [".txt", ".md"]:
        return _read_text_file(path)
    elif suffix == ".docx":
        return _read_docx_file(path)
    elif suffix == ".pdf":
        return _read_pdf_file(path)
    else:
        raise ValueError(f"サポートされていないファイル形式です: {suffix}")


def _read_text_file(path: Path) -> str:
    """テキストファイル（.txt, .md）を読み込む

    Args:
        path: ファイルパス

    Returns:
        ファイルの内容
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _read_docx_file(path: Path) -> str:
    """Word文書（.docx）を読み込む

    Args:
        path: ファイルパス

    Returns:
        抽出されたテキスト

    Raises:
        ImportError: python-docxがインストールされていない場合
    """
    try:
        from docx import Document
    except ImportError:
        raise ImportError(
            "python-docxがインストールされていません。"
            "pip install python-docx を実行してください。"
        )

    doc = Document(str(path))
    paragraphs = [para.text for para in doc.paragraphs]
    return "\n".join(paragraphs)


def _read_pdf_file(path: Path) -> str:
    """PDFファイルを読み込む

    Args:
        path: ファイルパス

    Returns:
        抽出されたテキスト

    Raises:
        ImportError: PyMuPDFがインストールされていない場合
        ValueError: OCR処理されていないPDFの場合
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError(
            "PyMuPDFがインストールされていません。"
            "pip install PyMuPDF を実行してください。"
        )

    doc = fitz.open(str(path))
    text_parts = []

    for page in doc:
        text_parts.append(page.get_text())

    doc.close()
    text = "\n".join(text_parts).strip()

    # テキストが空または極端に短い場合はOCR未処理と判断
    if len(text) < 10:
        raise ValueError(
            "このPDFはOCR処理されていません。"
            "PDFelementなどでOCR処理してから再度お試しください。"
        )

    return text


def get_supported_extensions() -> list[str]:
    """サポートされているファイル拡張子のリストを返す

    Returns:
        サポートされている拡張子のリスト
    """
    return [".txt", ".md", ".docx", ".pdf"]
