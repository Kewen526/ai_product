#!/bin/bash
set -e

REPO_URL="https://github.com/Kewen526/ai_product.git"
APP_DIR="/opt/ai_product"
SERVICE_NAME="ai_product"
PORT=8000

echo "===> 1. 安装系统依赖（含 Python 3.9）"
if command -v apt-get &>/dev/null; then
    apt-get update -y
    apt-get install -y python3.9 python3.9-venv python3-pip git
elif command -v yum &>/dev/null; then
    yum install -y python39 python39-pip git
fi

# 确定可用的 Python 3.9+ 可执行文件
if command -v python3.9 &>/dev/null; then
    PYTHON=python3.9
elif command -v python3.11 &>/dev/null; then
    PYTHON=python3.11
elif command -v python3 &>/dev/null; then
    PYTHON=python3
else
    echo "❌ 未找到 Python 3，请手动安装 python3.9+" && exit 1
fi
echo "使用 Python：$($PYTHON --version)"

echo "===> 2. 拉取代码"
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull origin main
else
    git clone "$REPO_URL" "$APP_DIR"
fi

echo "===> 3. 安装 Python 依赖"
cd "$APP_DIR/backend"
$PYTHON -m venv .venv
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
