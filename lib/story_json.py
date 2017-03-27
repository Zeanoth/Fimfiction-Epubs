"""Organizes and prepares the JSON data for a story."""

import json
import os
import re
from xml.dom import minidom

import util as util_module
import values as values_module


_URL_PREFIX = "http://www.fimfiction.net/api/story.php?story="


class InvalidStoryIdError(Exception):
    """Exception raised when the story id does not match anything."""


class IncompleteJsonError(Exception):
    """Exception raised when the response JSON is incomplete."""


class Rating(object):
    EVERYONE = 'Everyone'
    TEEN = 'Teen'
    MATURE = 'Mature'


class Status(object):
    INCOMPLETE = 'Incomplete'
    COMPLETE = 'Complete'
    HIATUS = 'Hiatus'
    CANCELLED = 'Cancelled'
    

class StoryJson(object):
    def __init__(self, story_id):
        self._story_id = str(story_id)
        self.load()

    def load(self):
        """Requests the story JSON from fimfiction.net."""
        url = _URL_PREFIX + self._story_id
        
        response = json.load(util_module.http_get_request(url))

        if 'error' in response:
            raise InvalidStoryIdError(response['error'] + ' ' + self._story_id)
        elif 'story' not in response:
            raise IncompleteJsonError(
                self._story_id + ' returned with incomplete JSON.')

        self._story = response['story']
        self._format_description()

    def _format_description(self):
        """Calls the methods that clean up the description."""
        self._description = self._story.get('description', '')
        self._convert_bbc_to_html()
        self._extract_images()

    def _convert_bbc_to_html(self):
        """Converts the description from bbcode to HTML."""
        code = self._description
        for tag in ['b', 'i', 'u']:
            code = code.replace('[%s]' % tag, '<%s>' % tag)
            code = code.replace('[/%s]' % tag, '</%s>' % tag)
            
        code = '<p class="indented">' + code + '</p>'
        code = re.sub('\r\n', '</p><p class="indented">', code)

        code = re.sub(r'\[color=([^\]]*?)\](.*?)\[/color\]',
                      r'<span style="color:\1">\2</span>', code)
        code = re.sub(r'\[size=([^\]]*?)\](.*?)\[/size\]',
                      r'<span style="font-size:\1">\2</span>', code)
        code = re.sub(r'\[url=([^\]]*?)\](.*?)\[/url\]',
                      r'<a href="\1">\2</a>', code)

        code = re.sub(r'\[img\](.*?)\[/img\]', r'<img src="\1" />', code)
        code = re.sub(
            r'\[center\](.*?)\[/center\]', r'<p align="center">\1</p>', code)
        
        code = re.sub(r'\[quote\](.*?)\[/quote\]', (
            '<blockquote style="padding:10px; border:1px solid; '
            'margin:10px 0px; background:#f5f5f5; '
            r'border-radius:5px;">\1</blockquote>'), code)

        code = re.sub(r'\[hr\]', '<hr/>', code)
        
        self._description = code

    def _extract_images(self):
        """Extracts the images in the description."""
        code = self._description
        images = list(set(re.findall('img src="(.*?)" />', code)))
        image_dict = {}
        for i in range(len(images)):
            image_filename = images[i].rsplit('/', 1)[1]
            image_dict[image_filename] = images[i]
            code = code.replace(
                images[i], values_module.IMAGES_DIR + '/' + image_filename)
        self._description = code
        self._images = image_dict

    def download_images(self, epub_dir):
        """Downloads the images in the description.
        
        Args:
            epub_dir (str): Directory of the unzipped epub.
        """
        images_dir = util_module.create_images_dir(epub_dir)
        
        epub_opf = os.path.join(epub_dir, 'book.opf')
        epub_opf_doc = minidom.parse(epub_opf)
        
        manifest = epub_opf_doc.getElementsByTagName('manifest')[0]
        
        image_count = 0
        for image_filename, image_url in self._images.iteritems():
            image_count += 1
            response = util_module.download_image(
                image_url, images_dir, image_filename)
            
            item = epub_opf_doc.createElement('item')
            item.setAttribute(
                'href', values_module.IMAGES_DIR + '/' + image_filename)
            item.setAttribute(
                'id', 'description-image-%d' % image_count)
            item.setAttribute('media-type', response['content_type'])
            
            manifest.appendChild(item)
            
        with open(epub_opf, 'w') as epub_opf_file:
            epub_opf_file.write(util_module.encode_xml(epub_opf_doc))
    
    def get_title(self):
        return self._story.get('title', '')

    def get_description(self):
        return self._description

    def get_date_modified(self):
        return int(self._story.get('date_modified', -1))

    def get_rating(self):
        return self._story.get('content_rating_text', '')

    def get_categories(self):
        categories = self._story.get('categories', {})
        return [key for key, value in categories.iteritems() if value]

    def get_images(self):
        return self._images

    def get_status(self):
        return self._story.get('status', '')
    
    def is_complete(self):
        return self.get_status() == Status.COMPLETE

    def get_author(self):
        return self._story.get('author', {'name': ''}).get('name', '')

    def get_cover_image(self):
        return self._story.get('full_image') or self._story.get('image', '')

    def get_id(self):
        return int(self._story.get('id', -1))

if __name__ == '__main__':
    story = StoryJson(192047)
    code = story.get_description()
    if '[' in code or ']' in code:
        print re.findall(r'\[.*?\]', code)
