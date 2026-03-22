---
name: wechat-publish
description: Publish Markdown articles to WeChat Official Account draft box. Use this skill whenever the user wants to convert a Markdown file to WeChat format and send it to the draft box. Automatically handles Markdown-to-HTML conversion, AI image generation, image upload to WeChat, and draft creation.
---

# WeChat Publish 📱

将 Markdown 文章发布到微信公众号草稿箱。

## 触发条件

当用户表达以下意图时，使用此技能：
- "将 article.md 发送到公众号"
- "把这篇 Markdown 发到微信草稿箱"
- "帮我发布这篇文章到微信公众号"
- "将 md 文件转换为微信格式并发送"

## 执行流程

### 1. 确认必要信息

在執行前，确保有以下信息：
- **Markdown 文件路径**：如 `article.md` 或 `~/workspace/my-article.md`
- **文章标题**：如果用户未提供，根据文章内容生成标题
- **主题风格**（可选）：默认 `autumn-warm`

### 2. 检查配置

确认配置文件 `~/.config/wechat-publish/config.json` 存在且包含：
- 微信 AppID 和 Secret（用于 API 调用）
- 图片生成 API 配置（ModelScope 或其他 OpenAI 兼容 API）

如果配置缺失，提示用户先配置。

### 3. 执行发布命令

运行以下命令：

```bash
python3 skills/wechat-publish/scripts/publish.py <markdown 文件路径> --draft --title "<文章标题>" --theme <主题名>
```

**参数说明：**
- `<markdown 文件路径>`：Markdown 文件的绝对或相对路径
- `--draft`：发送到微信草稿箱（必需）
- `--title "<标题>"`：文章标题（建议提供，否则使用文件名）
- `--theme <主题名>`：可选，支持 `autumn-warm`（默认）、`spring-fresh`、`ocean-calm`、`default`

**示例：**
```bash
# 基本用法
python3 skills/wechat-publish/scripts/publish.py article.md --draft --title "我的文章"

# 指定主题
python3 skills/wechat-publish/scripts/publish.py article.md --draft --title "我的文章" --theme spring-fresh

# 保存到本地 HTML（不发送）
python3 skills/wechat-publish/scripts/publish.py article.md --save-draft output.html
```

### 4. 内部处理流程（自动执行）

脚本会自动完成以下步骤，无需用户干预：

1. **读取 Markdown 文件**：解析文件内容
2. **提取图片**：识别文中的图片引用
   - 本地图片：`![alt](./path/to/image.png)`
   - 在线图片：`![alt](https://example.com/image.jpg)`
   - AI 生成图片：`![alt](__generate:prompt__)`
3. **处理 AI 生成图片**（如果有）：
   - 调用 ModelScope API 生成图片
   - 下载生成的图片
   - 上传到微信素材库
   - 替换 Markdown 中的 `__generate:` 语法为微信图片 URL
4. **生成 HTML**：
   - 调用内嵌的 wechat-md 引擎将 Markdown 转换为微信格式的 HTML
   - 应用选定的主题样式
5. **处理剩余图片**：
   - 下载本地/在线图片
   - 上传到微信素材库
   - 替换 HTML 中的图片链接为微信 CDN URL
6. **设置封面**：
   - 如果用户指定 `--cover`，使用指定图片
   - 否则自动使用第一张图片作为封面
   - 如果都没有，则根据文章内容调用API生成一张图片作为封面
7. **创建草稿**：
   - 调用微信 API 创建草稿
   - 返回草稿 ID

### 5. 输出结果

成功时输出：
```
✓ 配置加载成功
✓ 读取文件：article.md
✓ 微信 Token 获取成功
✓ 图片 1 已上传到微信
✓ HTML 生成成功
✓ 封面上传成功
✓ 草稿创建成功：<draft_id>
```

**草稿 ID** 是文章在微信后台的唯一标识，用户可以在微信公众号后台的"草稿箱"中找到文章。

## Markdown 图片语法

在 Markdown 文件中支持以下图片格式：

| 类型 | 语法 | 示例 |
|------|------|------|
| 本地图片 | `![描述](./路径)` | `![封面](./images/cover.png)` |
| 在线图片 | `![描述](https://...)` | `![产品](https://example.com/img.jpg)` |
| AI 生成 | `![描述](__generate:prompt__)` | `![概念图](__generate:A futuristic city with flying cars__)` |

**AI 生成图片提示：**
- 使用英文提示词效果更好
- 描述要具体，包含场景、风格、颜色等细节
- 示例：`__generate:A modern workspace with a developer creating AI skills, minimalist tech illustration style__`

## 主题选择

| 主题名 | 风格 | 适用场景 |
|--------|------|----------|
| `autumn-warm` | 温暖秋日风格（橙色/棕色系） | 通用、技术文章、故事 |
| `spring-fresh` | 清新春日风格（绿色/粉色系） | 生活、美食、旅行 |
| `ocean-calm` | 现代海洋风格（蓝色系） | 科技、商业、正式内容 |
| `default` | 简洁默认风格 | 任何场景 |

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| "配置加载失败" | 检查 `~/.config/wechat-publish/config.json` 是否存在且格式正确 |
| "获取微信 Token 失败" | 确认 AppID 和 Secret 正确，且公众号已认证 |
| "图片生成失败" | 检查 ModelScope API Key 是否有效，或更换图片生成服务 |
| "封面上传失败" | 确保文章至少有一张图片，或使用 `--cover` 指定封面 |
| "HTML 生成失败" | 检查 Node.js 是否安装，运行 `bash skills/wechat-publish/scripts/install.sh` 安装依赖 |

## 参考文档

| 文档 | 用途 |
|------|------|
| [HTML 排版指南](references/html-guide.md) | 自定义排版样式 |
| [图片语法说明](references/image-syntax.md) | 图片处理高级用法 |
| [主题参考](references/themes.md) | 主题样式预览 |
| [写作指南](references/writing-guide.md) | 公众号写作最佳实践 |

## 依赖

- Python 3.10+
- Node.js 18+（用于 wechat-md 渲染引擎）
- Python 库：`requests`（通过 `install.sh` 安装）

**首次使用前运行：**
```bash
bash skills/wechat-publish/scripts/install.sh
```
