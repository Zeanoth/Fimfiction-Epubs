"""Manages epub files and folders."""

import os
import shutil
import zipfile


def expand(epub, new_location=''):
    """Expands a .epub file into a directory

    Args:
        epub (str): Path to .epub file.
        new_location (str): Directory to unzip epub into.
    
    Returns:
        Path to unzipped epub.
    """
    old_location, epub_file = epub.rsplit(os.path.sep, 1)
    if not new_location:
        new_location = old_location
    
    epub_dir = os.path.join(new_location, epub_file[:-len('.epub')])
    
    with zipfile.ZipFile(epub) as epubZip:
        epubZip.extractall(epub_dir)
    return epub_dir

def compress(epub_dir, remove_dir=False):
    """Compress a directory back into a .epub file

    Args:
        epub_dir (str): Directory of the unzipped epub.
        remove_dir (bool): Whether to remove the unzipped epub after
            compressing.
    """
    epub = epub_dir + '.epub'
    remove(epub)
    with zipfile.ZipFile(epub, 'w', zipfile.ZIP_DEFLATED) as epubZip:
        for root, dirs, files in os.walk(epub_dir):
            for file in files:
                filepath = os.path.join(root, file)
                trimmedpath = filepath.replace(epub_dir + os.path.sep, '')
                epubZip.write(filepath, trimmedpath)
    if remove_dir:
        remove(epub_dir)

def remove(epub_path):
    """Removes epub directory, epub file, or zip file if it exists.

    Args:
        epub_path (str): Path to .epub, .zip, or epub directory
    """
    if os.path.exists(epub_path):
        if os.path.isdir(epub_path):
            shutil.rmtree(epub_path)
        else:
            os.remove(epub_path)
