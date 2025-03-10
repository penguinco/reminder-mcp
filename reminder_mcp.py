#!/usr/bin/env python3
"""
macOSのリマインダーアプリと連携するMCPサーバーを提供するモジュール。

このモジュールは以下の機能を提供します：
- リマインダーの一覧表示
- リマインダーの詳細取得
- リマインダーの完了
- リマインダーの削除
- リマインダー名の更新
- リマインダーの追加
"""
import os
import subprocess
import sys
from mcp.server.fastmcp import FastMCP

def run_applescript(script: str):
    """
    AppleScriptを実行し、結果を返す関数。

    Args:
        script: 実行するAppleScriptコード

    Returns:
        dict: 実行結果または実行エラー
    """
    proc = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False
    )
    if proc.returncode != 0:
        return {"error": proc.stderr.strip()}
    return {"result": proc.stdout.strip()}

def list_reminders():
    """
    完了していないリマインダーのみを一覧表示する。

    Returns:
        dict: リマインダーのリスト
    """
    script = 'tell application "Reminders" to get name of reminders whose completed is false'
    result = run_applescript(script)
    reminders = result.get("result", "").split(", ")
    if reminders == ['']:
        return {"reminders": []}
    return {"reminders": reminders}

def get(name: str):
    """
    特定のリマインダーの詳細を取得する。

    Args:
        name: リマインダーの名前

    Returns:
        dict: リマインダーの詳細情報
    """
    script = (
        f'tell application "Reminders" to get properties of reminders '
        f'whose name is "{name}"'
    )
    return run_applescript(script)

def done(name: str):
    """
    リマインダーを完了済みにマークする。

    Args:
        name: リマインダーの名前

    Returns:
        dict: 操作結果
    """
    script = (
        f'tell application "Reminders" to set completed of '
        f'(first reminder whose name is "{name}") to true'
    )
    return run_applescript(script)

def delete(name: str):
    """
    リマインダーを削除する。

    Args:
        name: リマインダーの名前

    Returns:
        dict: 操作結果
    """
    script = f'tell application "Reminders" to delete (first reminder whose name is "{name}")'
    return run_applescript(script)

def update(old_name: str, new_name: str):
    """
    リマインダー名を更新する。

    Args:
        old_name: 現在のリマインダー名
        new_name: 新しいリマインダー名

    Returns:
        dict: 操作結果
    """
    script = (
        f'tell application "Reminders" to set name of '
        f'(first reminder whose name is "{old_name}") to "{new_name}"'
    )
    return run_applescript(script)

def add(name: str, body: str = ""):
    """
    リマインダーを追加する。

    Args:
        name: リマインダーの名前
        body: リマインダーの詳細（オプション）

    Returns:
        dict: 操作結果
    """
    script = (
        f'tell application "Reminders" to make new reminder with properties '
        f'{{name:"{name}", body:"{body}"}}'
    )
    return run_applescript(script)

# MCPサーバーの設定
# MCPサーバーの作成
mcp = FastMCP("Reminders")

@mcp.tool("list_reminders")
async def list_reminders_mcp():
    """未完了のリマインダー一覧を取得します。"""
    result = list_reminders()
    return result

@mcp.tool("get_reminder")
async def get_reminder(name: str):
    """特定のリマインダーの詳細を取得します。"""
    return get(name)

@mcp.tool("complete_reminder")
async def complete_reminder(name: str):
    """リマインダーを完了済みにマークします。"""
    return done(name)

@mcp.tool("delete_reminder")
async def delete_reminder(name: str):
    """リマインダーを削除します。"""
    return delete(name)

@mcp.tool("update_reminder")
async def update_reminder(old_name: str, new_name: str):
    """リマインダーの名前を更新します。"""
    return update(old_name, new_name)

@mcp.tool("add_reminder")
async def add_reminder(name: str, body: str = ""):
    """新しいリマインダーを追加します。"""
    return add(name, body)

def mcp_serve(port: int = 2501):
    """
    MCPサーバーとして起動します。

    Args:
        port: サーバーのポート番号（デフォルト: 2501）
    """
    # ポート番号をシステム引数として設定
    sys.argv = ["remcli.py", "--port", str(port)]
    
    # FastMCPの実行
    mcp.run()

if __name__ == "__main__":
    mcp_serve()
