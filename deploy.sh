#!/bin/bash
set -e

REPO_URL="https://github.com/Kewen526/ai_product.git"
APP_DIR="/opt/ai_product"
SERVICE_NAME="ai_product"
PORT=8000

echo "===> 1. 安装系统依赖"
if command -v apt-get &>/dev/null; then
    apt-get update -y
    apt-get install -y python3 python3-pip python3-venv git
elif command -v yum &>/dev/null; then
    yum install -y python3 python3-pip git
fi

echo "===> 2. 拉取代码"
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull origin main
else
    git clone "$REPO_URL" "$APP_DIR"
fi

echo "===> 3. 安装 Python 依赖"
cd "$APP_DIR/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo "===> 4. 注册 systemd 服务"
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=AI Product Backend
After=network.target

[Service]
WorkingDirectory=${APP_DIR}/backend
ExecStart=${APP_DIR}/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port ${PORT}
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
echo "   接口地址：http://$(curl -s ifconfig.me 2>/dev/null || echo '服务器IP'):${PORT}"
echo "   API文档：http://$(curl -s ifconfig.me 2>/dev/null || echo '服务器IP'):${PORT}/docs"
