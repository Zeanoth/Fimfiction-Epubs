"""Collection of utility methods used by the modules."""

import os
import re
import urllib2

import values as values_module


class ContentType:
    JPG = 'image/jpeg'
    PNG = 'image/png'

    EXTENSIONS = {
        JPG: '.jpg',
        PNG: '.png',
    }


def create_images_dir(epub_dir):
    """Creates an images directory for an epub.
    
    Args:
        epub_dir (str): Directory of the unzipped epub.
    """
    images_dir = os.path.join(epub_dir, values_module.IMAGES_DIR)
    if not os.path.isdir(images_dir):
        os.mkdir(images_dir)
    return images_dir


def http_get_request(url):
    """Makes a GET request to the url.
    
    Args:
        url (str): URL to send GET request to.
        
    Returns:
        Response from the server.
    """
    request = urllib2.Request(url, headers={'User-Agent':'Mozilla'})
    return urllib2.urlopen(request)


def download_image(image_url, image_dir, image_filename=None):
    """Downloads an image to the specified URL.
    
    Args:
        image_url (str): URL of the image to download.
        image_dir (str): Directory to save the image to.
        image_filename (str): Filename of the image to save as.
        
    Returns:
        A dictionary containing the content/media type and the filename.
    """
    if not image_filename:
        image_filename = image_url.rsplit('/', 1)[1]
     
    response = http_get_request(image_url)
    
    content_type = response.headers.get('content-type')
    extension = ContentType.EXTENSIONS[content_type]
    
    # If the filename doesn't have an extension, add one.
    if not re.search('\.\w{3}$', image_filename):
        image_filename += extension
            
    with open(os.path.join(image_dir, image_filename), 'wb') as image_file:
        image_file.write(response.read())
        
    return {'content_type': content_type, 'filename': image_filename}

def encode(xml):
    return xml.encode('utf-8').strip()

def encode_xml(doc):
    return encode(doc.toxml())

def correct_meta(epub_dir):
    """Corrects common issues with epub meta files.
    
    Args:
        epub_dir (str): Directory of the unzipped epub.
    """ 
    def correct_common(filename):
        with open(filename, 'r+') as f:
            data = f.read()
            data = re.sub(r'(>[^\<]*?)&([^>]*?<)', r'\1&amp;\2', data)

            f.seek(0)
            f.write(data)
            f.truncate()
            
    for filename in ['book.ncx', 'book.opf']:
        correct_common(os.path.join(epub_dir, filename))
