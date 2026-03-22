#!/bin/bash
# WeChat Publish 快速测试脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/skills/wechat-publish/scripts/publish.py"
CONFIG_FILE="$HOME/.config/wechat-publish/config.json"

echo "╔════════════════════════════════════════════════╗"
echo "║       WeChat Publish Quick Test               ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 检查配置文件
if [ ! -f "$CONFIG_FILE" ]; then
    echo "⚠ 配置文件不存在: $CONFIG_FILE"
    echo "创建示例配置文件..."
    mkdir -p "$(dirname "$CONFIG_FILE")"
    cat > "$CONFIG_FILE" << 'EOF'
{
  "wechat": {
    "appid": "your_appid",
    "secret": "your_secret"
  },
  "image": {
    "provider": "modelscope",
    "api_key": "ms-486b384a-fb6b-404b-9d7a-fb87be106bb1",
    "base_url": "https://api-inference.modelscope.cn/",
    "default_size": "1024x1024",
    "default_model": "turbo"
  },
  "html": {
    "default_theme": "autumn-warm",
    "opencode_bin": "/root/.opencode/bin/opencode",
    "model": "opencode/gpt-5-nano"
  },
  "openai": {
    "enabled": false,
    "api_key": "",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4o-mini"
  }
}
EOF
    echo "✓ 配置文件已创建: $CONFIG_FILE"
    echo "请编辑配置文件填入您的微信 AppID 和 Secret"
    exit 0
fi

# 检查 Python 脚本
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "⚠ Python 脚本不存在: $PYTHON_SCRIPT"
    exit 1
fi

# 显示帮助信息
echo "测试命令:"
echo ""
echo "# 生成 HTML 文件"
echo "python3 $PYTHON_SCRIPT ${SCRIPT_DIR}/skills/wechat-publish/example_article.md --save-draft output.html"
echo ""
echo "# 生成 HTML 并发送到草稿箱"
echo "python3 $PYTHON_SCRIPT ${SCRIPT_DIR}/skills/wechat-publish/example_article.md --draft --title '测试文章'"
echo ""
echo "# 生成带封面的文章"
echo "python3 $PYTHON_SCRIPT article.md --draft --title '文章标题' --cover cover.png"
echo ""
echo "✓ 测试脚本准备就绪"