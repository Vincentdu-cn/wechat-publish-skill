#!/bin/bash
# WeChat Publish 安装脚本

set -e

echo "╔════════════════════════════════════════════════╗"
echo "║      WeChat Publish Skill Installer           ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：需要 Python 3"
    exit 1
fi

echo "✓ Python 版本：$(python3 --version)"

# 检查依赖
echo ""
echo "检查依赖..."

if ! python3 -c "import requests" &> /dev/null; then
    echo "  安装 requests..."
    pip3 install requests -q
fi

if ! python3 -c "import yaml" &> /dev/null; then
    echo "  安装 PyYAML..."
    pip3 install PyYAML -q
fi

echo "✓ 依赖安装完成"

# 安装 wechat-md (内嵌的 Markdown 渲染引擎)
echo ""
echo "安装 wechat-md 渲染引擎..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/wechat-md"
if [ ! -d "node_modules" ]; then
    npm install --silent
    echo "✓ wechat-md 依赖已安装"
else
    echo "✓ wechat-md 依赖已存在"
fi
cd - > /dev/null

# 创建配置目录
echo ""
echo "创建配置目录..."
mkdir -p ~/.config/wechat-publish
echo "✓ 配置目录：~/.config/wechat-publish"

# 检查配置文件
CONFIG_FILE="$HOME/.config/wechat-publish/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo ""
    echo "⚠ 配置文件不存在，创建示例配置..."
    SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
    cp "$SCRIPT_DIR/example_config.json" "$CONFIG_FILE"
    echo "✓ 示例配置已创建：$CONFIG_FILE"
    echo ""
    echo "⚠ 请编辑配置文件，填入你的 API Keys"
fi

# 设置执行权限
chmod +x skills/wechat-publish/scripts/publish.py

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║              安装完成！                         ║"
echo "╚════════════════════════════════════════════════╝"
echo ""
echo "使用示例："
echo ""
echo "# 生成 HTML 文件"
echo "python3 skills/wechat-publish/scripts/publish.py article.md --save-draft output.html"
echo ""
echo "# 发送到微信草稿箱"
echo "python3 skills/wechat-publish/scripts/publish.py article.md --draft --title '文章标题'"
echo ""
