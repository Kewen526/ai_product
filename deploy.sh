#!/bin/bash
set -e

GITHUB_API="https://api.github.com/repos/Kewen526/ai_product/tarball/main"
APP_DIR="/opt/ai_product"
SERVICE_NAME="ai_product"
PORT=8001
UVICORN=/usr/local/bin/uvicorn

echo "===> 1. 安装系统依赖"
if command -v apt-get &>/dev/null; then
    apt-get update -y
    apt-get install -y python3 python3-pip git curl tar
elif command -v yum &>/dev/null; then
    yum install -y python3 python3-pip git curl tar
fi

echo "===> 2. 下载代码（GitHub API）"
curl -fsSL "$GITHUB_API" -o /tmp/ai_product.tar.gz
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"
tar -xzf /tmp/ai_product.tar.gz -C "$APP_DIR" --strip-components=1
rm -f /tmp/ai_product.tar.gz

echo "===> 3. 安装 Python 依赖"
pip3 install --upgrade pip -q
pip3 install -r "$APP_DIR/backend/requirements.txt" -q

echo "===> 4. 注册 systemd 服务"
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=AI Product Backend
After=network.target

[Service]
WorkingDirectory=${APP_DIR}/backend
ExecStart=${UVICORN} main:app --host 0.0.0.0 --port ${PORT}
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

echo ""
echo "✅ 部署完成！"
echo "   服务状态：systemctl status $SERVICE_NAME"
echo "   接口地址：http://47.104.72.198:${PORT}"
echo "   API文档：http://47.104.72.198:${PORT}/docs"
