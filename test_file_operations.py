# test_file_operations.py
# ファイル操作のテストとサンプルコード
# 行数: 80行

from file_operations import (
    create_file_with_version,
    edit_file_with_version,
    replace_in_file_with_version,
    append_to_file_with_version,
    backup_current_files
)
from file_version_manager import file_version_manager

def test_create_file():
    """ファイル作成のテスト"""
    print("=== ファイル作成テスト ===")
    
    result = create_file_with_version(
        "/tmp/test_sample.py",
        "# サンプルPythonファイル\nprint('Hello, World!')\n"
    )
    
    print(f"作成結果: {result}")
    print()

def test_edit_file():
    """ファイル編集のテスト"""
    print("=== ファイル編集テスト ===")
    
    result = edit_file_with_version(
        "/tmp/test_sample.py",
        "# サンプルPythonファイル (編集版)\nprint('Hello, Claude!')\n"
    )
    
    print(f"編集結果: {result}")
    print()

def test_replace_in_file():
    """文字列置換のテスト"""
    print("=== 文字列置換テスト ===")
    
    result = replace_in_file_with_version(
        "/tmp/test_sample.py",
        "Claude",
        "Multi-Agent System"
    )
    
    print(f"置換結果: {result}")
    print()

def test_append_to_file():
    """ファイル追記のテスト"""
    print("=== ファイル追記テスト ===")
    
    result = append_to_file_with_version(
        "/tmp/test_sample.py",
        "\n# 追記された内容\nprint('追記テスト')\n"
    )
    
    print(f"追記結果: {result}")
    print()

def test_view_history():
    """履歴表示のテスト"""
    print("=== 履歴表示テスト ===")
    
    history = file_version_manager.get_file_history("/tmp/test_sample.py")
    
    print(f"バージョン数: {len(history)}")
    for h in history:
        print(f"  v{h['version']}: {h['updated_at']} ({h['file_size']}バイト)")
    print()

def test_restore_version():
    """バージョン復元のテスト"""
    print("=== バージョン復元テスト ===")
    
    # バージョン1を復元
    content = file_version_manager.restore_version("/tmp/test_sample.py", 1)
    
    if content:
        print(f"復元成功 (v1):")
        print(content)
    else:
        print("復元失敗")
    print()

def run_all_tests():
    """全テスト実行"""
    print("\n" + "="*50)
    print("ファイル操作テスト開始")
    print("="*50 + "\n")
    
    test_create_file()
    test_edit_file()
    test_replace_in_file()
    test_append_to_file()
    test_view_history()
    test_restore_version()
    
    print("="*50)
    print("テスト完了")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_all_tests()
