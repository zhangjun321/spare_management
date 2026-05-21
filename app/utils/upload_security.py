# -*- coding: utf-8 -*-
"""
文件上传安全工具
- 文件类型白名单验证
- 文件名清洗 (防路径穿越)
- 文件大小限制
- 魔数检测 (MIME type sniffing)
"""

import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

# ── 允许的文件扩展名白名单 ───────────────────────────────
ALLOWED_IMAGE_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg',
}
ALLOWED_DOCUMENT_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'ppt', 'pptx',
    'txt', 'rtf', 'odt', 'ods',
}
ALLOWED_ARCHIVE_EXTENSIONS = {
    'zip', 'rar', '7z', 'tar', 'gz',
}

# 所有允许的扩展名（并集）
ALL_ALLOWED_EXTENSIONS = (
    ALLOWED_IMAGE_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS | ALLOWED_ARCHIVE_EXTENSIONS
)

# 最大文件大小 (bytes) — 默认 10MB
DEFAULT_MAX_SIZE = 10 * 1024 * 1024

# MIME 魔数映射 (前几字节 → 扩展名)
_MAGIC_NUMBERS = {
    b'\x89PNG\r\n\x1a\n': 'png',
    b'\xff\xd8\xff': 'jpg',
    b'GIF87a': 'gif',
    b'GIF89a': 'gif',
    b'BM': 'bmp',
    b'%PDF': 'pdf',
    b'PK\x03\x04': 'zip',  # also docx/xlsx/pptx
}


def is_allowed_extension(filename: str, allowed_extensions: set = None) -> bool:
    """
    检查文件扩展名是否在白名单中

    Args:
        filename: 原始文件名
        allowed_extensions: 允许的扩展名集合 (默认使用全部)

    Returns:
        bool: 是否合法
    """
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    allowed = allowed_extensions or ALL_ALLOWED_EXTENSIONS
    return ext in allowed


def sanitize_filename(filename: str) -> str:
    """
    清洗文件名：去除危险字符 + 添加 UUID 防碰撞

    Returns:
        安全的新文件名，保留原始扩展名
    """
    if not filename:
        return f"{uuid.uuid4().hex}"

    # 使用 Werkzeug 的 secure_filename 去除路径穿越字符
    safe = secure_filename(filename)

    # 如果 secure_filename 把名字清空了 (如全中文)，用 UUID 替代
    if not safe or safe.startswith('.') or safe == '':
        base = uuid.uuid4().hex
        if '.' in filename:
            ext = filename.rsplit('.', 1)[-1].lower()
            if ext in ALL_ALLOWED_EXTENSIONS:
                return f"{base}.{ext}"
        return base

    # 添加 UUID 前缀防止覆盖同名文件
    prefix = uuid.uuid4().hex[:8]
    if '.' in safe:
        name, ext = safe.rsplit('.', 1)
        return f"{prefix}_{name}.{ext.lower()}"
    return f"{prefix}_{safe}"


def validate_uploaded_file(file_storage, allowed_extensions: set = None,
                           max_size: int = DEFAULT_MAX_SIZE) -> tuple:
    """
    全面验证上传文件

    Args:
        file_storage: Flask FileStorage 对象
        allowed_extensions: 允许的扩展名集合
        max_size: 最大字节数

    Returns:
        (is_valid: bool, error_message: str or None)
    """
    if file_storage is None or file_storage.filename is None:
        return False, "未选择文件"

    filename = file_storage.filename

    # 1. 扩展名检查
    if not is_allowed_filename(filename, allowed_extensions):
        return False, f"不支持的文件类型: {filename}"

    # 2. 大小检查
    file_storage.seek(0, 2)  # 移到末尾
    size = file_storage.tell()
    file_storage.seek(0)      # 回到开头
    if size > max_size:
        return False, f"文件过大 ({size / 1024 / 1024:.1f}MB > {max_size / 1024 / 1024:.1f}MB)"

    # 3. 内容为空检查
    if size == 0:
        return False, "上传文件为空"

    # 4. 魔数检测（对图片和 PDF）
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext in ('png', 'jpg', 'jpeg', 'gif', 'bmp', 'pdf'):
        header = file_storage.read(16)
        file_storage.seek(0)
        detected = _detect_by_magic(header)
        if detected and detected != ext and not _is_compatible(ext, detected):
            return False, f"文件内容与扩展名不符 (检测为 .{detected})"

    return True, None


def is_allowed_filename(filename: str, allowed_extensions: set = None) -> bool:
    """别名，与 is_allowed_extension 相同"""
    return is_allowed_extension(filename, allowed_extensions)


def save_upload_safely(file_storage, subfolder: str = '',
                       allowed_extensions: set = None,
                       max_size: int = DEFAULT_MAX_SIZE) -> tuple:
    """
    安全地保存上传文件（一步完成验证+保存）

    Args:
        file_storage: Flask FileStorage 对象
        subfolder: uploads/ 下的子目录 (如 'images', 'documents')
        allowed_extensions: 允许的扩展名集合
        max_size: 最大文件大小

    Returns:
        (success: bool, result: str or error_message)
        成功时 result 为相对路径 '/uploads/subfolder/filename'
        失败时 result 为错误信息字符串
    """
    is_valid, err_msg = validate_uploaded_file(file_storage, allowed_extensions, max_size)
    if not is_valid:
        return False, err_msg

    safe_name = sanitize_filename(file_storage.filename)

    upload_dir = os.path.join(
        current_app.config.get('UPLOAD_FOLDER',
                               os.path.join(current_app.root_path, '..', 'uploads')),
        subfolder
    )
    os.makedirs(upload_dir, exist_ok=True)

    save_path = os.path.join(upload_dir, safe_name)
    file_storage.save(save_path)

    # 返回相对 URL 路径
    rel_path = os.path.join('/uploads', subfolder, safe_name) if subfolder else f'/uploads/{safe_name}'
    return True, rel_path.replace('\\', '/')


def _detect_by_magic(header: bytes) -> str or None:
    """通过魔数检测真实文件类型"""
    for magic, ext in _MAGIC_NUMBERS.items():
        if header[:len(magic)] == magic:
            return ext
    return None


def _is_similar(declared: str, detected: str) -> bool:
    """声明类型和检测类型是否兼容 (如 jpg/jpeg)"""
    mapping = {'jpg': 'jpeg', 'jpeg': 'jpg'}
    return declared == detected or mapping.get(declared) == detected


def _is_compatible(declared: str, detected: str) -> bool:
    """ZIP 容器格式可能被误检"""
    # docx/xlsx/pptx 本质上都是 zip
    zip_containers = {'docx', 'xlsx', 'pptx'}
    if declared in zip_containers and detected == 'zip':
        return True
    return _is_similar(declared, detected)
