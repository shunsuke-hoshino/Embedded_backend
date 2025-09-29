# 組み込みボード制御API - Azure App Service デプロイガイド

## 概要
このバックエンドAPIは、Webアプリからの描画パスを受信し、ESP32ボードに制御信号を送信するシステムです。

## Azure App Service デプロイ手順

### 1. 前提条件
- Azure CLI がインストール済み
- Azure サブスクリプション
- Git リポジトリが設定済み

### 2. Azure リソース作成

```bash
# リソースグループ作成
az group create --name embedded-board-rg --location "Japan East"

# App Service プラン作成
az appservice plan create --name embedded-board-plan --resource-group embedded-board-rg --sku B1 --is-linux

# Web App 作成（Python 3.9）
az webapp create --resource-group embedded-board-rg --plan embedded-board-plan --name embedded-board-api --runtime "PYTHON:3.9"
```

### 3. 環境変数設定

```bash
# フロントエンドURL設定
az webapp config appsettings set --resource-group embedded-board-rg --name embedded-board-api --settings FRONTEND_URL="https://your-frontend-app.azurestaticapps.net"

# ESP32 IP アドレス設定（必要に応じて）
az webapp config appsettings set --resource-group embedded-board-rg --name embedded-board-api --settings ESP32_IP="192.168.1.100"
```

### 4. デプロイ

```bash
# ローカルGitデプロイを有効化
az webapp deployment source config-local-git --name embedded-board-api --resource-group embedded-board-rg

# Git リモート追加
git remote add azure https://<deployment-username>@embedded-board-api.scm.azurewebsites.net/embedded-board-api.git

# デプロイ実行
git push azure main
```

### 5. 動作確認

デプロイ完了後、以下のURLでAPI稼働確認：
- `https://embedded-board-api.azurewebsites.net/` 

## API エンドポイント

### POST /api/path
描画パスデータを受信し、ESP32に送信

**リクエスト:**
```json
{
  "path": [
    {"x": 100, "y": 150},
    {"x": 120, "y": 180}
  ],
  "timestamp": "2025-09-29T10:00:00Z"
}
```

**レスポンス:**
```json
{
  "success": true,
  "message": "パスデータを受信し、ボードに送信しました",
  "points_received": 2,
  "board_response": {...},
  "timestamp": "2025-09-29T10:00:01Z"
}
```

### GET /api/status
現在のシステム状態を取得

### GET /api/path/current
現在保存されているパス情報を取得

### POST /api/esp32/config
ESP32の接続設定を更新

## トラブルシューティング

### ログ確認
```bash
az webapp log tail --name embedded-board-api --resource-group embedded-board-rg
```

### アプリケーション設定確認
```bash
az webapp config appsettings list --name embedded-board-api --resource-group embedded-board-rg
```

## セキュリティ考慮事項

- CORS設定は本番環境では適切なドメインのみに制限
- ESP32との通信はVPN経由を推奨
- API認証の実装を検討

## 料金について

- App Service Basic B1: 約 ¥1,300/月
- 無料枠での運用も可能（制限あり）