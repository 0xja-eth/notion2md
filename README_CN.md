# Notion 到 Markdown 转换工具

一个用于将 Notion 页面导出为 Markdown 格式的 Python 工具，支持各种块类型，包括折叠块、列表、图片等。

## 功能特点

- 将 Notion 页面转换为 Markdown 格式
- 支持递归处理子页面
- 处理多种块类型：
  - 文本、标题、列表
  - 折叠块（Toggle）及其嵌套内容
  - 列表块（Column lists）和列
  - 图片、书签、表格
  - 代码块（支持语法高亮）
- 单文件模式，可将所有页面合并为一个文档
- 目录扁平化工具，用于组织导出的文件

## 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/notion-to-markdown.git
cd notion-to-markdown

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python notion_to_md.py <notion页面URL> --output ./输出目录
```

### 可选参数

```
用法: notion_to_md.py [-h] [--output OUTPUT] [--delay DELAY] [--max-retries MAX_RETRIES] [--single] url

将 Notion 页面转换为 Markdown

位置参数:
  url                   Notion 页面 URL

可选参数:
  -h, --help            显示帮助信息并退出
  --output OUTPUT, -o OUTPUT
                        输出目录 (默认: ./notion_export)
  --delay DELAY, -d DELAY
                        请求之间的延迟时间（秒）(默认: 1.0)
  --max-retries MAX_RETRIES, -r MAX_RETRIES
                        请求失败时的最大重试次数 (默认: 3)
  --single, -s          将所有页面合并为单个文件
```

### 扁平化目录结构

项目包含一个用于扁平化目录结构的实用脚本：

```bash
python flatten_directory.py <源目录> <目标目录> [--rename-strategy 重命名策略] [--verbose]
```

重命名策略：
- `path`：在文件名中包含完整路径（默认）
- `parent`：在文件名中仅包含父目录名称
- `none`：保留原始文件名（有冲突时会自动解决）

## 使用示例

### 转换带有子页面的 Notion 页面

```bash
python notion_to_md.py https://www.notion.so/yourpage -o ./my_export
```

### 将 Notion 页面转换为单个文件

```bash
python notion_to_md.py https://www.notion.so/yourpage -o ./my_export --single
```

### 扁平化导出的目录结构

```bash
python flatten_directory.py ./my_export ./flattened_export --rename-strategy parent
```

## 依赖项

- requests
- beautifulsoup4
- python-slugify

## 许可证

[MIT](LICENSE)
