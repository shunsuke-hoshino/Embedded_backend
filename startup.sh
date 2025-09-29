#!/bin/bash

# Azure App Service用のスタートアップスクリプト
# api_serverディレクトリに移動してアプリケーションを起動
cd api_server
python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}