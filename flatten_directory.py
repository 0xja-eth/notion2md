#!/usr/bin/env python3
"""
Directory Flattener

This script flattens a directory structure by copying all files from a source directory
(including all subdirectories) into a single target directory.

Usage:
    python flatten_directory.py <source_directory> <target_directory> [--rename-strategy]

Rename strategies:
    - 'path': Include full path in filename (default)
    - 'parent': Include only parent directory in filename
    - 'none': Keep original filenames (may cause conflicts)
"""

import os
import sys
import shutil
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def flatten_directory(source_dir, target_dir, rename_strategy='path'):
    """
    Flatten a directory structure by copying all files to a single directory.
    
    Args:
        source_dir (str): Path to the source directory
        target_dir (str): Path to the target directory
        rename_strategy (str): Strategy for renaming files ('path', 'parent', or 'none')
    """
    source_path = Path(source_dir).resolve()
    target_path = Path(target_dir).resolve()
    
    # Create target directory if it doesn't exist
    target_path.mkdir(parents=True, exist_ok=True)
    
    # Check if source directory exists
    if not source_path.exists() or not source_path.is_dir():
        logging.error(f"Source directory '{source_path}' does not exist or is not a directory")
        return False
    
    # Check if source and target are the same
    if source_path == target_path:
        logging.error("Source and target directories cannot be the same")
        return False
    
    # Check if target is a subdirectory of source
    if target_path.is_relative_to(source_path):
        logging.error("Target directory cannot be a subdirectory of source directory")
        return False
    
    file_count = 0
    conflict_count = 0
    
    # Walk through the source directory
    for root, _, files in os.walk(source_path):
        for file in files:
            source_file = Path(root) / file
            
            # Skip if not a file
            if not source_file.is_file():
                continue
            
            # Determine the new filename based on the rename strategy
            if rename_strategy == 'path':
                # Use the full path structure in the filename
                rel_path = source_file.relative_to(source_path)
                new_filename = str(rel_path).replace('/', '_').replace('\\', '_')
            elif rename_strategy == 'parent':
                # Use only the parent directory name in the filename
                parent_dir = source_file.parent.name
                if parent_dir:
                    new_filename = f"{parent_dir}_{file}"
                else:
                    new_filename = file
            else:  # 'none' or any other value
                new_filename = file
            
            target_file = target_path / new_filename
            
            # Handle filename conflicts
            if target_file.exists():
                if rename_strategy == 'none':
                    # For 'none' strategy, add a counter to avoid overwriting
                    counter = 1
                    name_parts = os.path.splitext(new_filename)
                    while target_file.exists():
                        new_filename = f"{name_parts[0]}_{counter}{name_parts[1]}"
                        target_file = target_path / new_filename
                        counter += 1
                    conflict_count += 1
                    logging.warning(f"Filename conflict: '{file}' renamed to '{new_filename}'")
            
            # Copy the file
            try:
                shutil.copy2(source_file, target_file)
                file_count += 1
                logging.debug(f"Copied: {source_file} -> {target_file}")
            except Exception as e:
                logging.error(f"Failed to copy {source_file}: {e}")
    
    logging.info(f"Flattening complete: {file_count} files copied to {target_dir}")
    if conflict_count > 0:
        logging.info(f"Resolved {conflict_count} filename conflicts")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Flatten a directory structure by copying all files to a single directory")
    parser.add_argument("source_dir", help="Source directory to flatten")
    parser.add_argument("target_dir", help="Target directory to copy files to")
    parser.add_argument("--rename-strategy", choices=['path', 'parent', 'none'], default='path',
                        help="Strategy for renaming files: 'path' (include full path), 'parent' (include parent dir), or 'none' (keep original names)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run the flattening process
    success = flatten_directory(args.source_dir, args.target_dir, args.rename_strategy)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
