# auto_version_hooks.py
# ファイル操作時の自動バージョン保存フック
# 行数: 95行

import os
from pathlib import Path
from typing import Optional
from file_version_manager import file_version_manager
import logging

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def auto_save_file_version(file_path: str, content: str, operation: str = "unknown") -> Optional[int]:
    """ファイル操作時に自動的にバージョンを保存
    
    Args:
        file_path: ファイルパス
        content: ファイル内容
        operation: 操作種別 (create, edit, update)
        
    Returns:
        保存されたバージョン番号、失敗時はNone
    """
    try:
        # 絶対パスに変換
        abs_path = os.path.abspath(file_path)
        
        # バージョン保存
        version = file_version_manager.save_version(abs_path, content)
        
        logger.info(f"[{operation}] ファイルバージョン保存: {file_path} -> v{version}")
        return version
        
    except Exception as e:
        logger.error(f"バージョン保存失敗: {file_path} - {e}")
        return None

def hook_file_create(file_path: str, content: str) -> tuple[bool, Optional[int]]:
    """ファイル作成時のフック
    
    Args:
        file_path: 作成するファイルパス
        content: ファイル内容
        
    Returns:
        (作成成功, バージョン番号)
    """
    try:
        # ファイル作成
        path_obj = Path(file_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # バージョン保存
        version = auto_save_file_version(file_path, content, operation="create")
        
        return True, version
        
    except Exception as e:
        logger.error(f"ファイル作成失敗: {file_path} - {e}")
        return False, None

def hook_file_edit(file_path: str, content: str) -> tuple[bool, Optional[int]]:
    """ファイル編集時のフック
    
    Args:
        file_path: 編集するファイルパス
        content: 新しいファイル内容
        
    Returns:
        (編集成功, バージョン番号)
    """
    try:
        # ファイル編集
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # バージョン保存
        version = auto_save_file_version(file_path, content, operation="edit")
        
        return True, version
        
    except Exception as e:
        logger.error(f"ファイル編集失敗: {file_path} - {e}")
        return False, None

def hook_file_update(file_path: str, old_content: str, new_content: str) -> tuple[bool, Optional[int]]:
    """ファイル更新時のフック（差分適用）
    
    Args:
        file_path: 更新するファイルパス
        old_content: 元の内容
        new_content: 新しい内容
        
    Returns:
        (更新成功, バージョン番号)
    """
    return hook_file_edit(file_path, new_content)

def save_current_file_version(file_path: str) -> Optional[int]:
    """既存ファイルの現在の状態をバージョン保存
    
    Args:
        file_path: ファイルパス
        
    Returns:
        保存されたバージョン番号、失敗時はNone
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return auto_save_file_version(file_path, content, operation="manual")
        
    except Exception as e:
        logger.error(f"手動バージョン保存失敗: {file_path} - {e}")
        return None
