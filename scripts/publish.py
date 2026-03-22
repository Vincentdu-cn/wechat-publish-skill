#!/usr/bin/env python3
"""
WeChat Publish - Markdown to WeChat HTML converter with baoyu-md and image generation
使用 baoyu-markdown-to-html 进行 MD 转 HTML，支持 AI 图片生成和自动上传到微信草稿箱。
"""

import os
import re
import sys
import json
import requests
import argparse
import tempfile
import subprocess
from pathlib import Path

# 颜色输出
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

CONFIG_FILE = os.path.expanduser("~/.config/wechat-publish/config.json")
WECHAT_MD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wechat-md")

def load_config():
    """读取配置文件"""
    if not os.path.exists(CONFIG_FILE):
        print(f"{Colors.RED}错误：配置文件不存在：{CONFIG_FILE}{Colors.NC}")
        sys.exit(1)
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Colors.RED}错误：配置文件读取失败：{e}{Colors.NC}")
        sys.exit(1)

def log(msg, color=Colors.GREEN):
    print(f"{color}✓ {msg}{Colors.NC}")

def log_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.NC}")

def log_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.NC}")

# ============== 微信 API ==============

def get_wechat_token(appid, secret):
    """获取微信 Access Token"""
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"
    resp = requests.get(url, timeout=30).json()
    if 'access_token' in resp:
        return resp['access_token']
    log_error(f"获取 Token 失败：{resp}")
    return None

def upload_image_to_wechat(token, file_path):
    """上传图片到微信素材库（支持本地文件或 URL）"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
    
    # 判断是 URL 还是本地文件
    if file_path.startswith('http://') or file_path.startswith('https://'):
        # 下载 URL 图片到内存
        resp = requests.get(file_path, timeout=30)
        if resp.status_code != 200:
            log_error(f"下载图片失败：{file_path}")
            return None, None
        files = {'media': ('image.png', resp.content, 'image/png')}
    else:
        # 本地文件 - 读取内容到内存
        with open(file_path, 'rb') as f:
            file_content = f.read()
        files = {'media': ('image.png', file_content, 'image/png')}
    
    resp = requests.post(url, files=files, timeout=60).json()
    if 'media_id' in resp:
        return resp['media_id'], resp.get('url', '')
    log_error(f"上传图片失败：{resp}")
    return None, None

def create_wechat_draft(token, title, content, thumb_media_id):
    """创建微信草稿"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"
    data = {
        "articles": [{
            "title": title[:32],  # 标题最长 32 字符
            "content": content,
            "thumb_media_id": thumb_media_id
        }]
    }
    # 使用 ensure_ascii=False 避免中文被转义
    resp = requests.post(url, data=json.dumps(data, ensure_ascii=False).encode('utf-8'), 
                         headers={'Content-Type': 'application/json'}, timeout=30).json()
    if 'media_id' in resp:
        return resp['media_id']
    log_error(f"创建草稿失败：{resp}")
    return None

# ============== 图片生成 API ==============

def generate_image(config, prompt):
    """调用图片生成 API"""
    image_config = config.get('image', {})
    api_key = image_config.get('api_key', '')
    base_url = image_config.get('base_url', '').rstrip('/')
    model = image_config.get('default_model', '')
    size = image_config.get('default_size', '1024x1024')
    provider = image_config.get('provider', 'modelscope')
    
    if not api_key or not base_url:
        log_error("图片 API 配置不完整")
        return None
    
    url = f"{base_url}/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "n": 1
    }
    
    try:
        # ModelScope 需要异步模式
        if provider == 'modelscope':
            headers["X-ModelScope-Async-Mode"] = "true"
            
            # 提交任务
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            data = resp.json()
            
            task_id = data.get('task_id')
            if not task_id:
                log_error(f"未获取到 task_id: {data}")
                return None
            
            log_info(f"图片任务已提交：{task_id}")
            
            # 轮询任务状态
            task_url = f"{base_url}/v1/tasks/{task_id}"
            poll_headers = {
                "Authorization": f"Bearer {api_key}",
                "X-ModelScope-Task-Type": "image_generation"
            }
            
            import time
            for i in range(36):  # 最多等待 3 分钟
                time.sleep(5)
                try:
                    task_resp = requests.get(task_url, headers=poll_headers, timeout=30)
                    task_data = task_resp.json()
                    
                    status = task_data.get('task_status', '')
                    if status == 'SUCCEED':
                        images = task_data.get('output_images', [])
                        if images:
                            log("图片生成成功")
                            return images[0]
                        log_error("任务成功但无图片")
                        return None
                    elif status == 'FAILED':
                        log_error(f"任务失败：{task_data}")
                        return None
                    elif status == 'PROCESSING':
                        if i % 3 == 0:
                            log_info(f"图片生成中...")
                except Exception as e:
                    pass  # 继续轮询
            
            log_error("图片生成超时")
            return None
        
        # OpenAI 同步模式
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        data = resp.json()
        if 'data' in data and len(data['data']) > 0:
            return data['data'][0].get('url') or data['data'][0].get('b64_json')
        
        # 其他返回格式
        if 'images' in data and len(data['images']) > 0:
            return data['images'][0].get('url')
            
        log_error(f"图片生成失败：{data}")
    except Exception as e:
        log_error(f"图片生成异常：{e}")
    return None

def download_image(url, save_path):
    """下载图片"""
    try:
        resp = requests.get(url, timeout=60)
        with open(save_path, 'wb') as f:
            f.write(resp.content)
        return True
    except Exception as e:
        log_error(f"下载图片失败：{e}")
        return False

# ============== wechat-md HTML 生成 ==============

def generate_html_with_wechat_md(markdown_content, theme, keep_title=False):
    """使用内嵌的 wechat-md 生成 HTML"""
    # 创建临时文件
    temp_dir = tempfile.mkdtemp()
    md_path = os.path.join(temp_dir, "input.md")
    html_path = os.path.join(temp_dir, "input.html")  # render.ts 会在同一目录生成 .html
    
    # 写入 Markdown 内容
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    # 主题映射：将旧主题名映射到 wechat-md 主题
    theme_map = {
        "autumn-warm": "default",
        "spring-fresh": "grace",
        "ocean-calm": "modern",
        "default": "default",
    }
    wechat_theme = theme_map.get(theme, "default")
    
    try:
        # 调用 wechat-md CLI (不设置 cwd，让它在临时目录生成 HTML)
        cmd = [
            "npx", "tsx",
            os.path.join(WECHAT_MD_DIR, "src", "render.ts"),
            md_path,
            "--theme", wechat_theme,
        ]
        if keep_title:
            cmd.append("--keep-title")
        
        log_info(f"调用 wechat-md 生成 HTML (主题：{wechat_theme})")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            log_error(f"wechat-md 执行失败：{result.stderr}")
            return None
        
        # 读取生成的 HTML (render.ts 会在 .md 文件同一目录生成 .html)
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                html = f.read()
            log("HTML 生成成功 (wechat-md)")
            return html
        else:
            log_error(f"HTML 文件未生成：{html_path}")
            return None
            
    except subprocess.TimeoutExpired:
        log_error("wechat-md 执行超时")
        return None
    except Exception as e:
        log_error(f"wechat-md 调用异常：{e}")
        return None
    finally:
        # 清理临时文件
        try:
            if os.path.exists(md_path):
                os.remove(md_path)
            if os.path.exists(html_path):
                os.remove(html_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass

# ============== 图片处理 ==============

def extract_images(markdown_content):
    """提取 Markdown 中的图片"""
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    images = []
    for match in re.finditer(pattern, markdown_content):
        alt, url = match.groups()
        images.append({'alt': alt, 'url': url, 'type': classify_image(url)})
    return images

def classify_image(url):
    """判断图片类型"""
    if url.startswith('__generate:') or url.startswith('__GENERATE:') or url.startswith('{{GENERATE:'):
        return 'generate'
    elif url.startswith('http://') or url.startswith('https://'):
        return 'online'
    else:
        return 'local'

def process_images(config, images, token=None):
    """处理所有图片，返回微信 URL 列表"""
    results = []
    temp_dir = tempfile.mkdtemp()
    
    for i, img in enumerate(images):
        log_info(f"处理图片 {i+1}/{len(images)}: {img['type']}")
        
        if img['type'] == 'generate':
            # AI 生成图片
            prompt = img['url'].replace('__generate:', '').replace('__GENERATE:', '').replace('{{GENERATE:', '').rstrip('}')
            log_info(f"生成图片：{prompt[:50]}...")
            img_url = generate_image(config, prompt)
            if img_url:
                if img_url.startswith('http'):
                    # 下载生成的图片
                    temp_path = os.path.join(temp_dir, f"gen_{i}.png")
                    if download_image(img_url, temp_path):
                        if token:
                            media_id, wechat_url = upload_image_to_wechat(token, temp_path)
                            if wechat_url:
                                results.append(wechat_url)
                                continue
                        results.append(img_url)
                        continue
        elif img['type'] == 'online':
            # 在线图片
            temp_path = os.path.join(temp_dir, f"online_{i}.png")
            if download_image(img['url'], temp_path):
                if token:
                    media_id, wechat_url = upload_image_to_wechat(token, temp_path)
                    if wechat_url:
                        results.append(wechat_url)
                        continue
                results.append(img['url'])
                continue
        elif img['type'] == 'local':
            # 本地图片
            if os.path.exists(img['url']):
                if token:
                    media_id, wechat_url = upload_image_to_wechat(token, img['url'])
                    if wechat_url:
                        results.append(wechat_url)
                        continue
                results.append(img['url'])
                continue
        
        results.append('')  # 失败时添加空占位
    
    return results

def extract_html_body(html_content):
    """从 baoyu-md 生成的完整 HTML 中提取 body 内容"""
    # 匹配 <body>...</body> 之间的内容
    match = re.search(r'<body[^>]*>([\s\S]*?)</body>', html_content, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # 如果没有找到 body，返回原始内容
    return html_content

# ============== 主函数 ==============

def main():
    parser = argparse.ArgumentParser(description="WeChat Publish - Markdown to WeChat HTML converter")
    parser.add_argument("markdown_file", help="Markdown 文件路径")
    parser.add_argument("--theme", default="autumn-warm", help="主题 (默认：autumn-warm)")
    parser.add_argument("--draft", action="store_true", help="发送到微信草稿箱")
    parser.add_argument("--cover", help="封面图片路径")
    parser.add_argument("--title", help="文章标题")
    parser.add_argument("--save-draft", dest="save_file", help="保存 HTML 到文件")
    parser.add_argument("--keep-title", action="store_true", help="保留第一个标题")
    
    args = parser.parse_args()
    
    # 读取配置
    config = load_config()
    log("配置加载成功")
    
    # 读取 Markdown 文件
    if not os.path.exists(args.markdown_file):
        log_error(f"文件不存在：{args.markdown_file}")
        sys.exit(1)
    
    with open(args.markdown_file, 'r', encoding='utf-8') as f:
        original_markdown = f.read()
    log(f"读取文件：{args.markdown_file}")
    
    # 提取原始 Markdown 中的图片（包括 __generate: 语法）
    images = extract_images(original_markdown)
    log_info(f"检测到 {len(images)} 张图片")
    
    # 获取微信 Token（如果需要处理图片）
    token = None
    if args.draft or any(img['type'] == 'generate' for img in images):
        if args.draft:
            wechat_config = config.get('wechat', {})
            token = get_wechat_token(wechat_config.get('appid'), wechat_config.get('secret'))
            if not token:
                log_error("获取微信 Token 失败")
                sys.exit(1)
            log("微信 Token 获取成功")
    
    # 先处理 __generate: 图片，获取微信 URL
    markdown_content = original_markdown
    if images:
        temp_dir = tempfile.mkdtemp()
        for i, img in enumerate(images):
            if img['type'] == 'generate':
                prompt = img['url'].replace('__generate:', '').rstrip('_')
                log_info(f"生成图片 {i+1}/{len(images)}: {prompt[:50]}...")
                img_url = generate_image(config, prompt)
                if img_url and img_url.startswith('http'):
                    # 下载生成的图片
                    temp_path = os.path.join(temp_dir, f"gen_{i}.png")
                    if download_image(img_url, temp_path):
                        if token:
                            media_id, wechat_url = upload_image_to_wechat(token, temp_path)
                            if wechat_url:
                                # 替换 Markdown 中的图片 URL
                                old_pattern = f"![{img['alt']}](__generate:{prompt}__)"
                                markdown_content = markdown_content.replace(old_pattern, f"![{img['alt']}]({wechat_url})")
                                log(f"图片 {i+1} 已上传到微信")
                                continue
                # 如果上传失败，使用原始 URL（会在后续处理）
    
    # 生成 HTML (使用 wechat-md)
    html = generate_html_with_wechat_md(markdown_content, args.theme, args.keep_title)
    if not html:
        log_error("HTML 生成失败")
        sys.exit(1)
    
    # 提取 body 内容（去掉 html/head/body 包裹）
    html_body = extract_html_body(html)
    
    # 处理剩余的图片（本地和在线图片）
    remaining_images = [img for img in images if img['type'] != 'generate']
    if remaining_images and token:
        image_urls = process_images(config, remaining_images, token)
        # 替换 HTML 中的图片 src
        for i, url in enumerate(image_urls):
            count = 0
            def replace_img(match):
                nonlocal count
                if count == i:
                    count += 1
                    return match.group(1) + f'src="{url}"' + match.group(2)
                count += 1
                return match.group(0)
            html_body = re.sub(r'<img\s([^>]*?)src="[^"]*"([^>]*?)>', replace_img, html_body, count=1)
        log(f"处理了 {len(remaining_images)} 张图片")
    
    # 保存或发送
    if args.save_file:
        with open(args.save_file, 'w', encoding='utf-8') as f:
            f.write(html_body)
        log(f"HTML 已保存：{args.save_file}")
    
    if args.draft:
        title = args.title or Path(args.markdown_file).stem
        cover = args.cover
        
        # 如果没有封面，使用第一张图片
        # 优先使用 generate 图片（已经在 markdown_content 中替换为微信 URL）
        if not cover and images:
            log_info("未指定封面，使用第一张图片...")
            first_img = images[0]
            if first_img['type'] == 'generate':
                # 从 markdown_content 中提取微信 URL（支持 http 和 https）
                match = re.search(r'!\[.*?\]\((https?://mmbiz\.qpic\.cn/[^)]+)\)', markdown_content)
                if match:
                    cover = match.group(1)
            elif remaining_images and image_urls:
                cover = image_urls[0]
        
        if not cover:
            log_error("发送草稿需要封面图片，请使用 --cover 指定")
            sys.exit(1)
        
        # 上传封面
        media_id, _ = upload_image_to_wechat(token, cover)
        if not media_id:
            log_error("封面上传失败")
            sys.exit(1)
        log("封面上传成功")
        
        # 创建草稿
        draft_id = create_wechat_draft(token, title, html_body, media_id)
        if draft_id:
            log(f"草稿创建成功：{draft_id}")
        else:
            log_error("草稿创建失败")
            sys.exit(1)
    
    if not args.save_file and not args.draft:
        # 默认输出到控制台
        print("\n" + "="*50)
        print(html_body)

if __name__ == "__main__":
    main()
