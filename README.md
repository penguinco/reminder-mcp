# リマインダー・カレンダー MCP サーバー

macOSのリマインダーアプリとカレンダーアプリに連携するMCPサーバーを提供するツールです。このサーバーを使用することで、リマインダーの管理、カレンダーイベントの作成・取得、現在時刻の取得などの機能をAPI経由で利用できます。


## 機能

- **リマインダー関連**
  - 未完了のリマインダー一覧を取得
  - 特定のリマインダーの詳細を取得
  - リマインダーを完了済みにマーク
  - リマインダーを削除
  - リマインダー名を更新
  - 新しいリマインダーを追加

- **カレンダー関連**
  - 利用可能なカレンダーの一覧を取得
  - カレンダーにイベントを作成
  - 指定した期間のカレンダーイベントを取得

- **時間関連**
  - 現在時刻を様々なフォーマットで取得（ISO形式、日本語形式、各要素など）

## 必要条件

- macOS（AppleScriptを使用するため）
- Python 3.8以上
- macOSのリマインダーアプリとカレンダーアプリ

## インストール

1. リポジトリをクローン
```bash
git clone https://github.com/yourusername/reminder-mcp.git
cd reminder-mcp
```

2. 必要なライブラリをインストール
```bash
pip install -r requirements.txt
```

## 使い方

### MCPサーバーの起動

```bash
python reminder_mcp.py
```

デフォルトでは、ポート2501でサーバーが起動します。別のポートを指定する場合：

```bash
python reminder_mcp.py --port 3000
```

### APIエンドポイント

MCPサーバーは以下のエンドポイントを提供します：

#### リマインダー関連

- `list_reminders`: 未完了のリマインダー一覧を取得
- `get_reminder`: 特定のリマインダーの詳細を取得（パラメータ: `name`）
- `complete_reminder`: リマインダーを完了済みにマーク（パラメータ: `name`）
- `delete_reminder`: リマインダーを削除（パラメータ: `name`）
- `update_reminder`: リマインダー名を更新（パラメータ: `old_name`, `new_name`）
- `add_reminder`: 新しいリマインダーを追加（パラメータ: `name`, `body`(オプション)）

#### カレンダー関連

- `list_calendars`: 利用可能なカレンダーの一覧を取得
- `create_calendar_event`: カレンダーにイベントを作成（パラメータ: `title`, `start_date`, `end_date`, `calendar_name`(オプション), `location`(オプション), `notes`(オプション)）
- `get_calendar_events`: 指定した期間のカレンダーイベントを取得（パラメータ: `start_date`, `end_date`, `calendar_name`(オプション)）

#### 時間関連

- `get_current_time`: 現在時刻を様々なフォーマットで取得

### 使用例

#### リマインダー一覧の取得

```python
import requests

response = requests.post("http://localhost:2501/mcp", json={
    "name": "list_reminders",
    "arguments": {}
})
print(response.json())
```

#### 新しいリマインダーの追加

```python
import requests

response = requests.post("http://localhost:2501/mcp", json={
    "name": "add_reminder",
    "arguments": {
        "name": "買い物に行く",
        "body": "牛乳、卵、パンを買う"
    }
})
print(response.json())
```

#### カレンダーイベントの作成

```python
import requests

response = requests.post("http://localhost:2501/mcp", json={
    "name": "create_calendar_event",
    "arguments": {
        "title": "会議",
        "start_date": "2023-12-25 14:00:00",
        "end_date": "2023-12-25 15:00:00",
        "location": "会議室A",
        "notes": "プロジェクトの進捗確認"
    }
})
print(response.json())
```

#### 現在時刻の取得

```python
import requests

response = requests.post("http://localhost:2501/mcp", json={
    "name": "get_current_time",
    "arguments": {}
})
print(response.json())
```

## 注意事項

- このツールはmacOSのAppleScriptを使用しているため、macOSでのみ動作します。
- リマインダーアプリとカレンダーアプリへのアクセス権限が必要です。初回実行時に権限を求められる場合があります。
- 日付形式は `YYYY-MM-DD HH:MM:SS` 形式で指定してください。

## ライセンス

MIT