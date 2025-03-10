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
- カレンダーへのイベント追加 (新機能)
- カレンダーからのイベント取得 (新機能)
- 現在時刻の取得 (新機能)
"""
import os
import subprocess
import sys
import json
import datetime
from typing import Optional, Dict, List, Any
from mcp.server.fastmcp import FastMCP

def run_applescript(script: str):
    """
    AppleScriptを実行し、結果を返す関数。

    Args:
        script: 実行するAppleScriptのコード

    Returns:
        AppleScriptの実行結果
    """
    try:
        result = subprocess.run(['osascript', '-e', script], 
                               capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing AppleScript: {e.stderr}", file=sys.stderr)
        return None

# リマインダー関連の関数
def list_reminders():
    """
    未完了のリマインダー一覧を取得する。

    Returns:
        リマインダー名のリスト
    """
    script = '''
    tell application "Reminders"
        set remindersList to {}
        repeat with r in (reminders whose completed is false)
            set end of remindersList to name of r
        end repeat
        return remindersList
    end tell
    '''
    result = run_applescript(script)
    if result:
        return result.split(", ")
    return []

def get(name: str):
    """
    特定のリマインダーの詳細を取得する。

    Args:
        name: リマインダー名

    Returns:
        リマインダーの詳細情報
    """
    script = f'''
    tell application "Reminders"
        set matchingReminders to (reminders whose name is "{name}")
        if (count of matchingReminders) > 0 then
            set r to item 1 of matchingReminders
            return name of r & "," & (body of r as string) & "," & (completed of r as string)
        else
            return "not found"
        end if
    end tell
    '''
    result = run_applescript(script)
    if result and result != "not found":
        parts = result.split(",", 2)
        return {"name": parts[0], "body": parts[1] if len(parts) > 1 else "", "completed": parts[2] == "true" if len(parts) > 2 else False}
    return None

def done(name: str):
    """
    リマインダーを完了済みにマークする。

    Args:
        name: リマインダー名

    Returns:
        操作結果
    """
    script = f'''
    tell application "Reminders"
        set matchingReminders to (reminders whose name is "{name}")
        if (count of matchingReminders) > 0 then
            set r to item 1 of matchingReminders
            set completed of r to true
            return "completed"
        else
            return "not found"
        end if
    end tell
    '''
    return run_applescript(script) == "completed"

def delete(name: str):
    """
    リマインダーを削除する。

    Args:
        name: リマインダー名

    Returns:
        操作結果
    """
    script = f'''
    tell application "Reminders"
        set matchingReminders to (reminders whose name is "{name}")
        if (count of matchingReminders) > 0 then
            delete item 1 of matchingReminders
            return "deleted"
        else
            return "not found"
        end if
    end tell
    '''
    return run_applescript(script) == "deleted"

def update(old_name: str, new_name: str):
    """
    リマインダー名を更新する。

    Args:
        old_name: 現在の名前
        new_name: 新しい名前

    Returns:
        操作結果
    """
    script = f'''
    tell application "Reminders"
        set matchingReminders to (reminders whose name is "{old_name}")
        if (count of matchingReminders) > 0 then
            set r to item 1 of matchingReminders
            set name of r to "{new_name}"
            return "updated"
        else
            return "not found"
        end if
    end tell
    '''
    return run_applescript(script) == "updated"

def add(name: str, body: str = ""):
    """
    新しいリマインダーを追加する。

    Args:
        name: リマインダー名
        body: リマインダーの詳細 (オプション)

    Returns:
        操作結果
    """
    script = f'''
    tell application "Reminders"
        set defaultList to first list
        tell defaultList
            make new reminder with properties {{name:"{name}", body:"{body}"}}
            return "added"
        end tell
    end tell
    '''
    return run_applescript(script) == "added"

# カレンダー関連の関数 (新機能)
def get_calendars():
    """
    利用可能なカレンダーの一覧を取得する。

    Returns:
        カレンダー名のリスト
    """
    script = '''
    tell application "Calendar"
        set calendarList to name of every calendar
        set jsonList to "["
        repeat with i from 1 to count of calendarList
            set calName to item i of calendarList
            set jsonList to jsonList & "\\"" & calName & "\\""
            if i < count of calendarList then
                set jsonList to jsonList & ", "
            end if
        end repeat
        set jsonList to jsonList & "]"
        return jsonList
    end tell
    '''
    result = run_applescript(script)
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {result}")
            return []
    return []

def create_calendar_event(title, start_date, end_date, calendar_name=None, location="", notes=""):
    """
    カレンダーにイベントを作成する。

    Args:
        title: イベントのタイトル
        start_date: 開始日時 (YYYY-MM-DD HH:MM:SS形式)
        end_date: 終了日時 (YYYY-MM-DD HH:MM:SS形式)
        calendar_name: カレンダー名 (Noneの場合はデフォルトカレンダー)
        location: 場所
        notes: メモ

    Returns:
        成功時はTrue、失敗時はFalse
    """
    if calendar_name is None:
        calendars = get_calendars()
        if calendars:
            calendar_name = calendars[0]
        else:
            return False

    script = f'''
    tell application "Calendar"
        tell calendar "{calendar_name}"
            make new event with properties {{summary:"{title}", start date:date "{start_date}", end date:date "{end_date}", location:"{location}", description:"{notes}"}}
            return "Event created successfully"
        end tell
    end tell
    '''
    result = run_applescript(script)
    return result is not None and "successfully" in result

def get_calendar_events(start_date, end_date, calendar_name=None):
    """
    指定した期間のイベントを取得する。

    Args:
        start_date: 開始日時 (YYYY-MM-DD形式)
        end_date: 終了日時 (YYYY-MM-DD形式)
        calendar_name: カレンダー名 (Noneの場合はデフォルトカレンダー)

    Returns:
        イベント情報の辞書のリスト
    """
    if calendar_name is None:
        calendars = get_calendars()
        if calendars:
            calendar_name = calendars[0]
        else:
            return []

    script = f'''
    tell application "Calendar"
        tell calendar "{calendar_name}"
            set eventList to events whose start date is greater than or equal to date "{start_date}" and start date is less than or equal to date "{end_date}"
            set jsonEvents to "["
            repeat with i from 1 to count of eventList
                set currentEvent to item i of eventList
                set eventTitle to summary of currentEvent
                set eventStart to start date of currentEvent
                set eventEnd to end date of currentEvent
                set eventLoc to location of currentEvent
                if eventLoc is missing value then
                    set eventLoc to ""
                end if
                
                set jsonEvent to "{{\\"title\\":\\""
                set jsonEvent to jsonEvent & eventTitle & "\\","
                set jsonEvent to jsonEvent & "\\"start\\":\\""
                set jsonEvent to jsonEvent & eventStart & "\\","
                set jsonEvent to jsonEvent & "\\"end\\":\\""
                set jsonEvent to jsonEvent & eventEnd & "\\","
                set jsonEvent to jsonEvent & "\\"location\\":\\""
                set jsonEvent to jsonEvent & eventLoc & "\\"}}"
                
                set jsonEvents to jsonEvents & jsonEvent
                if i < count of eventList then
                    set jsonEvents to jsonEvents & ", "
                end if
            end repeat
            set jsonEvents to jsonEvents & "]"
            return jsonEvents
        end tell
    end tell
    '''
    result = run_applescript(script)
    if result:
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {result}")
            return []
    return []

# 時間関連の関数 (新機能)
def get_current_time():
    """
    現在の時刻を取得する。

    Returns:
        現在の時刻情報を含む辞書
    """
    now = datetime.datetime.now()
    return {
        "iso_format": now.isoformat(),
        "formatted": now.strftime("%Y年%m月%d日 %H時%M分%S秒"),
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "weekday": now.strftime("%A"),
        "weekday_jp": ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"][now.weekday()]
    }

# MCPサーバーの設定
mcp = FastMCP()

@mcp.tool("list_reminders")
async def list_reminders_mcp():
    """未完了のリマインダー一覧を取得します。"""
    return {"reminders": list_reminders()}

@mcp.tool("get_reminder")
async def get_reminder(name: str):
    """特定のリマインダーの詳細を取得します。"""
    return {"result": get(name)}

@mcp.tool("complete_reminder")
async def complete_reminder(name: str):
    """リマインダーを完了済みにマークします。"""
    return {"result": done(name)}

@mcp.tool("delete_reminder")
async def delete_reminder(name: str):
    """リマインダーを削除します。"""
    return {"result": delete(name)}

@mcp.tool("update_reminder")
async def update_reminder(old_name: str, new_name: str):
    """リマインダーの名前を更新します。"""
    return {"result": update(old_name, new_name)}

@mcp.tool("add_reminder")
async def add_reminder(name: str, body: str = ""):
    """新しいリマインダーを追加します。"""
    return {"result": add(name, body)}

# カレンダー関連のMCPツール (新機能)
@mcp.tool("list_calendars")
async def list_calendars_mcp():
    """利用可能なカレンダーの一覧を取得します。"""
    return {"calendars": get_calendars()}

@mcp.tool("create_calendar_event")
async def create_calendar_event_mcp(title: str, start_date: str, end_date: str, calendar_name: Optional[str] = None, location: str = "", notes: str = ""):
    """カレンダーにイベントを作成します。"""
    success = create_calendar_event(title, start_date, end_date, calendar_name, location, notes)
    return {"result": "Event created successfully" if success else "Failed to create event"}

@mcp.tool("get_calendar_events")
async def get_calendar_events_mcp(start_date: str, end_date: str, calendar_name: Optional[str] = None):
    """指定した期間のカレンダーイベントを取得します。"""
    events = get_calendar_events(start_date, end_date, calendar_name)
    return {"events": events}

# 時間関連のMCPツール (新機能)
@mcp.tool("get_current_time")
async def get_current_time_mcp():
    """現在時刻を取得します。"""
    return get_current_time()

def mcp_serve(port: int = 2501):
    """
    MCPサーバーを起動する。

    Args:
        port: サーバーのポート番号
    """
    # FastMCPのrunメソッドはportパラメータを直接受け取らないため、
    # sys.argvを使用してポート番号を設定
    sys.argv = ["reminder_mcp.py", "--port", str(port)]
    mcp.run()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Start the Reminder MCP server")
    parser.add_argument("--port", type=int, default=2501, help="Port to run the server on")
    args = parser.parse_args()
    
    mcp_serve(args.port)
