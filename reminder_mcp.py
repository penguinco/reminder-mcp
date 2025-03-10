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
        start_date: 開始日時 (YYYY-MM-DDThh:mm:ss形式)
        end_date: 終了日時 (YYYY-MM-DDThh:mm:ss形式)
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

    # ISO形式の日付文字列をAppleScriptで扱える形式に変換
    try:
        start_date_obj = datetime.datetime.fromisoformat(start_date)
        end_date_obj = datetime.datetime.fromisoformat(end_date)
        
        # 日付のコンポーネントを取得
        start_year = start_date_obj.year
        start_month = start_date_obj.month
        start_day = start_date_obj.day
        start_hour = start_date_obj.hour
        start_minute = start_date_obj.minute
        
        end_year = end_date_obj.year
        end_month = end_date_obj.month
        end_day = end_date_obj.day
        end_hour = end_date_obj.hour
        end_minute = end_date_obj.minute
        
        print(f"Creating event: {title} from {start_date_obj} to {end_date_obj} in calendar '{calendar_name}'")
    except ValueError:
        print(f"Invalid date format: start_date={start_date}, end_date={end_date}")
        return False

    # AppleScriptで日付コンポーネントを直接設定
    script = f'''
    tell application "Calendar"
        tell calendar "{calendar_name}"
            -- 開始日時の設定
            set startDate to current date
            set year of startDate to {start_year}
            set month of startDate to {start_month}
            set day of startDate to {start_day}
            set hours of startDate to {start_hour}
            set minutes of startDate to {start_minute}
            set seconds of startDate to 0
            
            -- 終了日時の設定
            set endDate to current date
            set year of endDate to {end_year}
            set month of endDate to {end_month}
            set day of endDate to {end_day}
            set hours of endDate to {end_hour}
            set minutes of endDate to {end_minute}
            set seconds of endDate to 0
            
            -- イベントの作成
            make new event with properties {{summary:"{title}", start date:startDate, end date:endDate, location:"{location}", description:"{notes}"}}
            return "Event created successfully in {calendar_name} from " & (startDate as string) & " to " & (endDate as string)
        end tell
    end tell
    '''
    result = run_applescript(script)
    print(f"AppleScript result: {result}")  # デバッグ用
    return result is not None and "successfully" in result

def get_calendar_events(start_date, end_date, calendar_name=None):
    """
    指定した期間のイベントを取得する。

    Args:
        start_date: 開始日時 (YYYY-MM-DDThh:mm:ss形式)
        end_date: 終了日時 (YYYY-MM-DDThh:mm:ss形式)
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

    # ISO形式の日付文字列をdatetimeオブジェクトに変換
    try:
        start_date_obj = datetime.datetime.fromisoformat(start_date)
        end_date_obj = datetime.datetime.fromisoformat(end_date)
        
        # 日付のコンポーネントを取得
        start_year = start_date_obj.year
        start_month = start_date_obj.month
        start_day = start_date_obj.day
        
        end_year = end_date_obj.year
        end_month = end_date_obj.month
        end_day = end_date_obj.day
        
        print(f"Searching for events from {start_date_obj.date()} to {end_date_obj.date()} in calendar '{calendar_name}'")
    except ValueError:
        print(f"Invalid date format: start_date={start_date}, end_date={end_date}")
        return []

    # 日付範囲を指定してイベントを取得するAppleScript
    script = f'''
    tell application "Calendar"
        tell calendar "{calendar_name}"
            -- 開始日時の設定
            set startDate to current date
            set year of startDate to {start_year}
            set month of startDate to {start_month}
            set day of startDate to {start_day}
            set hours of startDate to 0
            set minutes of startDate to 0
            set seconds of startDate to 0
            
            -- 終了日時の設定
            set endDate to current date
            set year of endDate to {end_year}
            set month of endDate to {end_month}
            set day of endDate to {end_day}
            set hours of endDate to 23
            set minutes of endDate to 59
            set seconds of endDate to 59
            
            -- 日付範囲内のイベントを取得
            set matchingEvents to (events whose start date ≥ startDate and start date ≤ endDate)
            
            set eventData to ""
            repeat with e in matchingEvents
                set eventTitle to summary of e
                set eventStart to start date of e as string
                set eventEnd to end date of e as string
                set eventLoc to ""
                try
                    set eventLoc to location of e
                    if eventLoc is missing value then
                        set eventLoc to ""
                    end if
                end try
                
                -- 区切り文字として使用しない特殊な文字を使用
                set eventData to eventData & eventTitle & "§§§" & eventStart & "§§§" & eventEnd & "§§§" & eventLoc & "\\n"
            end repeat
            return eventData
        end tell
    end tell
    '''
    result = run_applescript(script)
    print(f"AppleScript result: {result}")  # デバッグ用
    
    events = []
    
    if result and result.strip():
        lines = result.strip().split("\\n")
        for line in lines:
            if not line.strip():
                continue
            parts = line.split("§§§")
            if len(parts) >= 3:
                event = {
                    "title": parts[0],
                    "start": parts[1],
                    "end": parts[2],
                    "location": parts[3] if len(parts) > 3 else ""
                }
                events.append(event)
                print(f"Event: {event['title']} - {event['start']} to {event['end']}")
    
    print(f"Found {len(events)} events in calendar '{calendar_name}' from {start_date_obj.date()} to {end_date_obj.date()}")
    return events

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
async def create_calendar_event_mcp(title: str, start_date: str, end_date: str, calendar_name=None, location: str = "", notes: str = ""):
    """カレンダーにイベントを作成します。"""
    success = create_calendar_event(title, start_date, end_date, calendar_name, location, notes)
    return {"result": "Event created successfully" if success else "Failed to create event"}

@mcp.tool("get_calendar_events")
async def get_calendar_events_mcp(start_date: str, end_date: str, calendar_name=None):
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
