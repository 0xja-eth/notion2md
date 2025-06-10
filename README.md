# Notion to Markdown Converter

A Python tool for exporting Notion pages to Markdown format with support for various block types, including toggles, columns, images, and more.
**Without using Notion API**

## Features

- Convert Notion pages to Markdown format
- Support for recursive page processing
- Handle various block types:
  - Text, headers, lists
  - Toggle blocks with nested content
  - Column lists and columns
  - Images, bookmarks, tables
  - Code blocks with syntax highlighting
- Single-file mode to merge all pages into one document
- Directory flattening utility to organize exported files

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/notion-to-markdown.git
cd notion-to-markdown

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python notion_to_md.py <notion_page_url> --output ./output_directory
```

### Options

```
usage: notion_to_md.py [-h] [--output OUTPUT] [--delay DELAY] [--max-retries MAX_RETRIES] [--single] url

Convert Notion pages to Markdown

positional arguments:
  url                   Notion page URL

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Output directory (default: ./notion_export)
  --delay DELAY, -d DELAY
                        Delay between requests in seconds (default: 1.0)
  --max-retries MAX_RETRIES, -r MAX_RETRIES
                        Maximum number of retries for failed requests (default: 3)
  --single, -s          Merge all pages into a single file
```

### Flatten Directory Structure

The project includes a utility script to flatten directory structures:

```bash
python flatten_directory.py <source_directory> <target_directory> [--rename-strategy strategy] [--verbose]
```

Rename strategies:
- `path`: Include full path in filename (default)
- `parent`: Include only parent directory name in filename
- `none`: Keep original filenames (with conflict resolution)

## Examples

### Convert a Notion page with subpages

```bash
python notion_to_md.py https://www.notion.so/yourpage -o ./my_export
```

### Convert a Notion page into a single file

```bash
python notion_to_md.py https://www.notion.so/yourpage -o ./my_export --single
```

### Flatten the exported directory structure

```bash
python flatten_directory.py ./my_export ./flattened_export --rename-strategy parent
```

## Dependencies

- requests
- beautifulsoup4
- python-slugify

## License

[MIT](LICENSE)
