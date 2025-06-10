#!/usr/bin/env python3
"""
Notion Page to Markdown Converter
This script downloads a Notion page and its subpages and converts them to Markdown files.
"""

import os
import re
import json
import time
import requests
import argparse
from urllib.parse import urlparse, unquote, quote
from bs4 import BeautifulSoup
from slugify import slugify
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 设置请求头，模拟浏览器访问
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.notion.so/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

# 请求延迟（秒），可通过命令行参数修改
REQUEST_DELAY = 1.0

class NotionToMarkdown:
    def __init__(self, output_dir, single_mode=False):
        self.output_dir = output_dir
        self.visited_pages = set()
        self.page_data = {}
        self.single_mode = single_mode
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Initialized NotionToMarkdown with output_dir: {output_dir}, single_mode: {single_mode}")
        
    def sanitize_filename(self, name):
        """将标题转换为有效的文件名"""
        # 使用 slugify 创建有效的文件名
        return slugify(name, allow_unicode=True)
    
    def extract_page_id(self, url):
        """从 Notion URL 中提取页面 ID"""
        # 解析 URL
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # 从路径中提取最后一部分作为页面 ID
        if path.endswith('/'):
            path = path[:-1]
        
        page_id = path.split('/')[-1]
        
        # 如果 ID 包含连字符，提取最后一部分
        if '-' in page_id:
            page_id = page_id.split('-')[-1]
        
        return page_id
    
    def download_page(self, url, max_retries=3, retry_delay=2):
        """下载 Notion 页面内容，支持重试机制"""
        retries = 0
        while retries < max_retries:
            try:
                print(f"Downloading page: {url} (attempt {retries + 1}/{max_retries})")
                response = requests.get(url, headers=HEADERS, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Error downloading page {url}: {e}")
                retries += 1
                if retries < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避策略
                else:
                    print(f"Failed to download page after {max_retries} attempts")
                    return None
            except Exception as e:
                print(f"Unexpected error downloading page {url}: {e}")
                return None
    
    def extract_json_data(self, html_content):
        """从 HTML 中提取 Notion 页面数据的 JSON"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 查找包含页面数据的脚本标签
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and '__notion_html_async.push("serverSidePrefetchData"' in script.string:
                # 提取 JSON 数据
                json_str = script.string.split('__notion_html_async.push("serverSidePrefetchData",', 1)[1]
                json_str = json_str.rsplit(')', 1)[0]
                
                try:
                    data = json.loads(json_str)
                    return data
                except json.JSONDecodeError:
                    continue
        
        return None

    def process_block(self, url, root_page_id, blocks, block_id, block_data):
        """处理块数据，包括子块和子页面"""
        if "value" not in block_data:
            return []

        block = block_data['value'].get('value', {})
        block_type = block.get('type')
        block_properties = block.get('properties', {})
        block_content_ids = block.get('content', [])

        print(f"Processing block ID: {block_id}, Type: {block_type}")

        content = []

        # 根据块类型处理内容
        if block_type == 'text':
            text = self.extract_formatted_text(block_properties.get('title', []))
            content.append(text)
        elif block_type == 'header':
            text = self.extract_formatted_text(block_properties.get('title', []))
            content.append(f"# {text}")
        elif block_type == 'sub_header':
            text = self.extract_formatted_text(block_properties.get('title', []))
            content.append(f"## {text}")
        elif block_type == 'sub_sub_header':
            text = self.extract_formatted_text(block_properties.get('title', []))
            content.append(f"### {text}")
        elif block_type == 'bulleted_list':
            text = self.extract_formatted_text(block_properties.get('title', []))
            content.append(f"- {text}")
        elif block_type == 'numbered_list':
            text = self.extract_formatted_text(block_properties.get('title', []))
            content.append(f"1. {text}")
        elif block_type == 'to_do':
            text = self.extract_formatted_text(block_properties.get('title', []))
            checked = block.get('checked', False)
            checkbox = "[x]" if checked else "[ ]"
            content.append(f"{checkbox} {text}")
        elif block_type == 'toggle':
            text = self.extract_formatted_text(block_properties.get('title', []))
            toggle_content = []

            # 处理 toggle 内的内容
            for child_id in block_content_ids:
                if child_id in blocks:
                    toggle_content += self.process_block(url, root_page_id, blocks, child_id, blocks[child_id])

            # 将 toggle 内的内容合并
            toggle_content_str = '\n\n'.join(toggle_content) if toggle_content else ''
            toggle_md = f"<details>\n<summary>{text}</summary>\n\n{toggle_content_str}\n</details>"
            content.append(toggle_md)
        elif block_type == 'callout':
            text = self.extract_formatted_text(block_properties.get('title', []))
            content.append(f"> {text}")
        elif block_type == 'quote':
            text = self.extract_formatted_text(block_properties.get('title', []))
            content.append(f"> {text}")
        elif block_type == 'divider':
            content.append("---")
        elif block_type == 'code':
            code = self.extract_text_from_property(block_properties.get('title', []))
            language = self.extract_text_from_property(block_properties.get('language', []))
            language = language.lower() if language else ""
            content.append(f"```{language}\n{code}\n```")
        elif block_type == 'image':
            # 处理图片
            source = block_properties.get('source', [])
            caption = block_properties.get('caption', []) # self.extract_formatted_text()

            while source and type(source) == list: source = source[0] if len(source) > 0 else None
            while caption and type(caption) == list: caption = caption[0] if len(caption) > 0 else None

            space_id = blocks.get(root_page_id, {}).get('spaceId', '')
            source = f"https://mask.notion.site/image/{quote(source, '')}?table=block&id={block_id}&spaceId={space_id}&width=1420&userId=&cache=v2"

            if source:
                content.append(f"![{caption}]({source})")
                if caption:
                    content.append(f"*{caption}*")
        elif block_type == 'bookmark':
            # 处理书签/链接
            link = block.get('link', '')
            title = self.extract_formatted_text(block_properties.get('title', []))
            description = self.extract_formatted_text(block_properties.get('description', []))
            if link:
                content.append(f"[{title or link}]({link})")
                if description:
                    content.append(f"> {description}")
        elif block_type == 'table':
            # 简单处理表格
            table_rows = []
            header_row = []

            # 获取表格行
            for child_id in block_content_ids:
                if child_id in blocks:
                    row_block = blocks[child_id].get('value', {}).get('value', {})
                    row_content_ids = row_block.get('content', [])
                    row_cells = []

                    # 获取行中的单元格
                    for cell_id in row_content_ids:
                        if cell_id in blocks:
                            cell_block = blocks[cell_id].get('value', {}).get('value', {})
                            cell_text = self.extract_formatted_text(cell_block.get('properties', {}).get('title', []))
                            row_cells.append(cell_text)

                    if not header_row and row_cells:  # 第一行作为表头
                        header_row = row_cells
                    else:
                        table_rows.append(row_cells)

            # 生成 Markdown 表格
            if header_row:
                table_md = [' | '.join(header_row)]
                table_md.append(' | '.join(['---'] * len(header_row)))
                for row in table_rows:
                    # 确保行与表头有相同数量的单元格
                    while len(row) < len(header_row):
                        row.append('')
                    table_md.append(' | '.join(row))
                content.append('\n'.join(table_md))
        elif block_type == 'page':
            # 子页面链接
            page_title = self.extract_formatted_text(block_properties.get('title', []))
            page_id = block_id

            # 处理子页面 (单页模式)
            if self.single_mode:
                parsed_url = urlparse(url)
                domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
                subpage_url = f"{domain}/{page_title}-{block_id.replace('-', '')}"
                pages_content = self.process_page(subpage_url, save_content=False, recursive=False)

                if len(pages_content) > 0:
                    content.append(f"# {page_title}")
                    content.append(pages_content[0]["content"])

            else:
                content.append(
                    f"[{page_title}](./{self.sanitize_filename(page_title)}/{self.sanitize_filename(page_title)}.md)")

            # 保存子页面 ID 以便后续处理
            self.page_data[page_id] = {
                'title': page_title,
                'parent_id': root_page_id
            }
        elif block_type == 'column_list' or block_type == 'column':
            # 处理 column_list 块
            column_content = []

            # 处理每个列
            for column_id in block_content_ids:
                if column_id in blocks:
                    column_content += self.process_block(url, root_page_id, blocks, column_id, blocks[column_id])

            # 将所有列内容合并为一个字符串
            if column_content:
                content.append('\n\n'.join(column_content))

        return content

    def extract_page_content(self, url, data):
        """从 JSON 数据中提取页面内容"""
        if not data or 'recordMap' not in data:
            logging.error("Missing 'recordMap' in data")
            return None
        
        record_map = data['recordMap']
        if 'block' not in record_map:
            logging.error("Missing 'block' in recordMap")
            return None
        
        blocks = record_map['block']
        
        # 查找根页面块
        root_page_id = data.get('pageId')
        if not root_page_id or root_page_id not in blocks:
            # 尝试找到类型为 page 的块
            for block_id, block_data in blocks.items():
                if 'value' in block_data and block_data['value'].get('type') == 'page':
                    root_page_id = block_id
                    break
        
        if not root_page_id:
            logging.error("No root page ID found")
            return None
        
        # 提取页面标题和内容
        root_block = blocks.get(root_page_id, {}).get('value', {}).get('value', {})
        title = self.extract_text_from_property(root_block.get('properties', {}).get('title', []))
        
        # 提取页面内容块 ID 列表
        content_ids = root_block.get('content', [])
        
        # 构建页面内容
        content = []
        for block_id in content_ids:
            if block_id in blocks:
                content += self.process_block(url, root_page_id, blocks, block_id, blocks[block_id])

        return {
            'title': title,
            'content': '\n\n'.join(content),
            'subpages': [key for key in self.page_data]

            # [block_id for block_id in content_ids if blocks.get(block_id, {}).get('value', {}).get('value', {}).get('type') == 'page']
        }
    
    def _process_column_list(self, column_ids, blocks):
        """递归处理 column_list 块"""
        column_content = []
        
        # 处理每个列
        for column_id in column_ids:
            if column_id in blocks:
                column_block = blocks[column_id].get('value', {}).get('value', {})
                column_type = column_block.get('type')
                
                # 确保这是一个列块
                if column_type == 'column':
                    column_content_ids = column_block.get('content', [])
                    column_items = []
                    
                    # 处理列中的每个项目
                    for item_id in column_content_ids:
                        if item_id in blocks:
                            item_block = blocks[item_id].get('value', {}).get('value', {})
                            item_type = item_block.get('type')
                            item_properties = item_block.get('properties', {})
                            
                            # 根据项目类型处理
                            if item_type == 'text':
                                item_text = self.extract_formatted_text(item_properties.get('title', []))
                                column_items.append(item_text)
                            elif item_type == 'bulleted_list':
                                item_text = self.extract_formatted_text(item_properties.get('title', []))
                                column_items.append(f"- {item_text}")
                            elif item_type == 'numbered_list':
                                item_text = self.extract_formatted_text(item_properties.get('title', []))
                                column_items.append(f"1. {item_text}")
                            # 可以根据需要添加更多类型的处理
                    
                    # 将列内容添加到列表中
                    if column_items:
                        column_content.append('\n\n'.join(column_items))
        
        # 将所有列内容合并为一个字符串
        return '\n\n'.join(column_content) if column_content else ''
    
    def extract_text_from_property(self, property_value):
        """从属性值中提取纯文本内容"""
        if not property_value:
            return ""
        
        result = []
        for item in property_value:
            if isinstance(item, list):
                if len(item) > 0:
                    result.append(item[0])
            elif isinstance(item, str):
                result.append(item)
        
        return ''.join(result)
        
    def extract_formatted_text(self, property_value):
        """从属性值中提取带格式的文本内容"""
        if not property_value:
            return ""
            
        result = []
        for item in property_value:
            if not isinstance(item, list):
                continue
                
            if len(item) >= 1:
                text = item[0]
                
                # 检查是否有格式信息
                if len(item) > 1 and isinstance(item[1], list):
                    formats = item[1]
                    # 处理各种格式
                    for fmt in formats:
                        if fmt == 'b':  # 粗体
                            text = f"**{text}**"
                        elif fmt == 'i':  # 斜体
                            text = f"*{text}*"
                        elif fmt == 's':  # 删除线
                            text = f"~~{text}~~"
                        elif fmt == 'c':  # 代码
                            text = f"`{text}`"
                        elif isinstance(fmt, list) and fmt[0] == 'a' and len(fmt) > 1:  # 链接
                            text = f"[{text}]({fmt[1]})"
                            
                result.append(text)
            
        return ''.join(result)
    
    def process_page(self, url, parent_path="", save_content=True, recursive=True):
        if url in self.visited_pages:
            logging.debug(f"Skipping already visited page: {url}")
            return []
        
        self.visited_pages.add(url)
        logging.info(f"Processing page: {url}")
        
        # 下载页面内容
        html_content = self.download_page(url)
        if not html_content:
            logging.error(f"Failed to download page content from {url}")
            return []
        
        # 提取 JSON 数据
        data = self.extract_json_data(html_content)
        if not data:
            logging.error(f"Failed to extract JSON data from {url}")
            return []

        # 提取页面内容
        page_content = self.extract_page_content(url, data)
        if not page_content:
            logging.error(f"Failed to extract page content from {url}")
            return []

        # 创建页面目录
        page_title = page_content['title'] or "Untitled"
        safe_title = self.sanitize_filename(page_title)

        if save_content:
            page_dir = os.path.join(self.output_dir, parent_path, safe_title)
            os.makedirs(page_dir, exist_ok=True)

            # 保存页面内容为 Markdown 文件
            md_file_path = os.path.join(page_dir, f"{safe_title}.md")
            with open(md_file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {page_title}\n\n")
                f.write(page_content['content'])

            logging.info(f"Saved page to {md_file_path}")

        pages_content = [page_content]

        if recursive:
            for subpage_id in page_content['subpages']:
                if subpage_id in data['recordMap']['block']:
                    subpage_block = data['recordMap']['block'][subpage_id].get('value', {}).get('value', {})
                    subpage_title = self.extract_text_from_property(
                        subpage_block.get('properties', {}).get('title', []))
                    parsed_url = urlparse(url)
                    domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    subpage_url = f"{domain}/{subpage_title}-{subpage_id.replace('-', '')}"
                    pages_content += self.process_page(subpage_url, os.path.join(parent_path, safe_title), save_content)
                    time.sleep(REQUEST_DELAY)

        return pages_content

def main():
    parser = argparse.ArgumentParser(description='Convert Notion pages to Markdown')
    parser.add_argument('url', help='URL of the Notion page')
    parser.add_argument('--output', '-o', default='./notion_export', help='Output directory')
    parser.add_argument('--delay', '-d', type=float, default=1.0, help='Delay between requests in seconds')
    parser.add_argument('--max-retries', '-r', type=int, default=3, help='Maximum number of retries for failed requests')
    parser.add_argument('--single', '-s', action='store_true', help='Merge all pages into a single file')
    args = parser.parse_args()
    
    try:
        parsed_url = urlparse(args.url)
        if not parsed_url.scheme or not parsed_url.netloc:
            logging.error("Invalid URL format")
            return 1
        
        global REQUEST_DELAY
        REQUEST_DELAY = args.delay
        
        logging.info(f"Starting Notion to Markdown conversion with URL: {args.url}")
        converter = NotionToMarkdown(args.output, single_mode=args.single)
        converter.process_page(args.url, recursive=not args.single)
        logging.info(f"Conversion complete. Output saved to {args.output}")
        return 0
    except KeyboardInterrupt:
        logging.warning("Conversion interrupted by user.")
        return 130
    except Exception as e:
        logging.error(f"Error during conversion: {e}")
        return 1

if __name__ == "__main__":
    main()
