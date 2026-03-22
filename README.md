# WeChat Publish Skill

将 Markdown 文章发布到微信公众号草稿箱的 skill。

## 功能特点

- ✅ Markdown → HTML 转换
- ✅ AI 图片生成（使用 `__generate:prompt__` 语法）
- ✅ 图片自动上传到微信服务器
- ✅ 自动设置封面图片
- ✅ 创建草稿（非直接发布）
- ✅ 支持多种主题样式

## 安装依赖

```bash
# 安装 Node.js 依赖
cd scripts/wechat-md
npm install

# 安装 Python 依赖
pip install requests
```

## 配置

在 `~/.config/wechat-publish/config.json` 中配置：

```json
{
  "wechat": {
    "appid": "你的微信公众号 AppID",
    "secret": "你的微信公众号 AppSecret"
  },
  "modelscope": {
    "api_key": "你的 ModelScope API Key"
  }
}
```

## 使用方法

```bash
# 基本用法
python3 scripts/publish.py article.md --draft --title "文章标题"

# 指定主题
python3 scripts/publish.py article.md --draft --title "文章标题" --theme autumn-warm

# 测试运行
bash scripts/quick_test.sh
```

## 图片语法

- **本地图片**: `![alt](./path/to/image.png)`
- **在线图片**: `![alt](https://example.com/image.png)`
- **AI 生成图片**: `![alt](__generate:prompt__)`

## 可用主题

- `autumn-warm`（默认）
- `spring-fresh`
- `ocean-calm`

## 文件结构

```
wechat-publish/
├── SKILL.md                 # nanobot skill 定义
├── scripts/
│   ├── publish.py          # 主发布脚本
│   ├── install.sh          # 安装脚本
│   └── wechat-md/          # Markdown 渲染引擎
│       ├── src/
│       ├── package.json
│       └── ...
├── references/              # 参考文档
│   ├── html-guide.md
│   ├── image-syntax.md
│   ├── themes.md
│   └── ...
└── example_config.json      # 配置示例
```

## 依赖

- Node.js + npm
- Python 3.x + requests 库
- 微信公众号 AppID 和 Secret
- ModelScope API Key（用于 AI 图片生成）

## License

MIT
