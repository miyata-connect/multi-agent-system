# file_operations.py
# ファイル操作の細分化されたユーティリティ関数
# 行数: 120行

import os
from pathlib import Path
from typing import Optional, List, Dict
from auto_version_hooks import hook_file_create, hook_file_edit, save_current_file_version
import logging

logger = logging.getLogger(__name__)

def create_file_with_version(file_path: str, content: str) -> Dict:
    """ファイルを作成し、自動的にバージョン保存
    
    Args:
        file_path: ファイルパス
        content: ファイル内容
        
    Returns:
        結果情報の辞書
    """
    success, version = hook_file_create(file_path, content)
    
    return {
        'success': success,
        'file_path': file_path,
        'version': version,
        'operation': 'create'
    }

def edit_file_with_version(file_path: str, new_content: str) -> Dict:
    """ファイルを編集し、自動的にバージョン保存
    
    Args:
        file_path: ファイルパス
        new_content: 新しい内容
        
    Returns:
        結果情報の辞書
    """
    success, version = hook_file_edit(file_path, new_content)
    
    return {
        'success': success,
        'file_path': file_path,
        'version': version,
        'operation': 'edit'
    }

def read_file(file_path: str) -> Optional[str]:
    """ファイルを読み込む
    
    Args:
        file_path: ファイルパス
        
    Returns:
        ファイル内容、失敗時はNone
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"ファイル読み込み失敗: {file_path} - {e}")
        return None

def replace_in_file_with_version(file_path: str, old_str: str, new_str: str) -> Dict:
    """ファイル内の文字列を置換し、バージョン保存
    
    Args:
        file_path: ファイルパス
        old_str: 置換前の文字列
        new_str: 置換後の文字列
        
    Returns:
        結果情報の辞書
    """
    try:
        # ファイル読み込み
        content = read_file(file_path)
        if content is None:
            return {
                'success': False,
                'error': 'ファイル読み込み失敗',
                'file_path': file_path
            }
        
        # 文字列置換
        if old_str not in content:
            return {
                'success': False,
                'error': '置換対象の文字列が見つかりません',
                'file_path': file_path
            }
        
        new_content = content.replace(old_str, new_str)
        
        # 編集して保存
        return edit_file_with_version(file_path, new_content)
        
    except Exception as e:
        logger.error(f"文字列置換失敗: {file_path} - {e}")
        return {
            'success': False,
            'error': str(e),
            'file_path': file_path
        }

def append_to_file_with_version(file_path: str, content: str) -> Dict:
    """ファイルに内容を追記し、バージョン保存
    
    Args:
        file_path: ファイルパス
        content: 追記する内容
        
    Returns:
        結果情報の辞書
    """
    try:
        # 既存内容を読み込み
        existing = read_file(file_path) or ""
        
        # 追記
        new_content = existing + content
        
        # 編集して保存
        return edit_file_with_version(file_path, new_content)
        
    except Exception as e:
        logger.error(f"ファイル追記失敗: {file_path} - {e}")
        return {
            'success': False,
            'error': str(e),
            'file_path': file_path
        }

def backup_current_files(file_paths: List[str]) -> Dict:
    """複数ファイルの現在状態をバックアップ
    
    Args:
        file_paths: ファイルパスのリスト
        
    Returns:
        バックアップ結果の辞書
    """
    results = []
    
    for file_path in file_paths:
        version = save_current_file_version(file_path)
        results.append({
            'file_path': file_path,
            'version': version,
            'success': version is not None
        })
    
    return {
        'total': len(file_paths),
        'success_count': sum(1 for r in results if r['success']),
        'results': results
    }
