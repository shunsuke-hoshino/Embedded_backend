# Azure App Service用デプロイ設定
import os
import sys

# パスを追加してmainモジュールをインポート可能にする
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app

# ポート番号を環境変数から取得（Azure App Service用）
port = int(os.environ.get("PORT", 8000))

if __name__ == "__main__":
    import uvicorn
    # Azure App Serviceでは0.0.0.0でバインドする必要がある
    uvicorn.run(app, host="0.0.0.0", port=port)