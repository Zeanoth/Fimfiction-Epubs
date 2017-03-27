"""Classes for creating a cover for an epub."""

import os
from xml.dom import minidom

import cv2
import numpy

import story_json as story_json_module
import util as util_module
import values as values_module


FONT_FACE = cv2.FONT_HERSHEY_COMPLEX
TITLE_FONT_SCALE = 3
AUTHOR_FONT_SCALE = 2
RATING_FONT_SCALE = 1
THICKNESS = 2

BORDER_RATIO = .04
STRIPE_RATIO = .036


class _Color(object):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    DARK_GREY = (50, 50, 50)

    EVERYONE = (56, 199, 137)
    TEEN = (56, 130, 199)
    MATURE = (56, 56, 199)

    RATING = {
        story_json_module.Rating.EVERYONE: EVERYONE,
        story_json_module.Rating.TEEN: TEEN,
        story_json_module.Rating.MATURE: MATURE
    }


class CoverCreator(object):
    def __init__(self, epub_dir, story_json):
        self.epub_dir = epub_dir
        self.story_json = story_json
        self.images_dir = None
        self.image_filename = None
        self.content_type = None

    @property
    def image_path(self):
        return os.path.join(
            self.images_dir, self.image_filename)

    def _grab_image(self):
        """Grabs the existing cover image for an epub if it exists."""
        cover_url = self.story_json.get_cover_image()
        if not cover_url:
            return
         
        response = util_module.download_image(cover_url, self.images_dir)
        self.content_type = response['content_type']
        self.image_filename = response['filename']
        
    def _origin(self, image_width, image_height, text_size, baseline=0,
                height_factor=1):
        """Calculates the origin of the text.
        
        Args:
            image_width (int): Width of the image.
            image_height (int): Height of the image.
            text_size (tuple): Size of the text (width, height).
            baseline (int): Fffset for the height of the text.
            height_factor (float): Divisor of the calculated height.
            
        Returns:
            Tuple with the x,y coordinates of the text.
        """
        return tuple(map(int, (
            (image_width - text_size[0]) / 2,
            (image_height + text_size[1] - baseline) / height_factor
            )))
        
    def _put_text(self, image_array, text, origin, font_scale,
                  thickness_delta=8):
        """Puts white text with a black border onto the image.
        
        Args:
            image_array (numpy.array): Image to apply text to.
            text (str): Text to apply.
            origin (tuple): Coordinates to place text at.
            font_scale (int): Scale of the text.
            thickness_delta (int): How much thicker the black border should be.
        """
        def put_text(color, thickness):
            cv2.putText(image_array, text, origin, FONT_FACE, font_scale, color,
                        thickness)
            
        put_text(_Color.BLACK, THICKNESS + thickness_delta)
        put_text(_Color.WHITE, THICKNESS)
        
    def _put_underline(self, image_array, origin, text_width, baseline):
        """Puts a text underline on the image.
        
        Args:
            image_array (numpy.array): Image to apply underline to.
            origin (tuple): Coordinaes of the underline.
            text_width (int): Width of the text being underlined.
            baseline (int): Offset of the height of the underline.
        """
        def put_underline(color, thickness):
            cv2.line(image_array,
                     (origin[0], origin[1] + baseline),
                     (origin[0] + text_width,
                      origin[1] + baseline),
                     color, thickness)
            
        put_underline(_Color.BLACK, THICKNESS + 8)
        put_underline(_Color.WHITE, THICKNESS)

    def _create_image(self):
        """Creates a new cover image for the epub."""
        def put_title():
            title_origin = self._origin(
                image_width, image_height, title_text_size, baseline_y, 3.2)
            
            self._put_text(image_array, title, title_origin, TITLE_FONT_SCALE)
            self._put_underline(
                image_array, title_origin, title_text_size[0], baseline_y)

        def put_author():
            author_origin = self._origin(
                image_width, image_height, author_text_size, 0, 2.5)
            self._put_text(image_array, author, author_origin,
                           AUTHOR_FONT_SCALE, thickness_delta=6)

        title = self.story_json.get_title()
        author = 'By: ' + self.story_json.get_author()

        title_text_size, baseline_y = (
            cv2.getTextSize(title, FONT_FACE, TITLE_FONT_SCALE, THICKNESS))
        author_text_size, _ = (
            cv2.getTextSize(author, FONT_FACE, AUTHOR_FONT_SCALE, THICKNESS))

        image_width = int(max(title_text_size[0], author_text_size[0]) * 1.2)
        image_height = int(image_width * 1.5)

        # Create image array and set background color to dark grey.
        image_array = numpy.empty((image_height, image_width, 3), numpy.uint8)
        image_array.fill(_Color.DARK_GREY)

        # Add title and author to the image.
        put_title()
        put_author()

        # cv2.imwrite(epub+"/cover.jpg",image_array)
        self.image_filename = 'cover.jpg'
        self.content_type = util_module.ContentType.JPG
        cv2.imwrite(self.image_path, image_array)
        
    def _add_stripes(self, image_array):
        """Add stripes to an image, going from top right to bottom left.
        
        Args:
            image_array (numpy.array): Image to apply stripes to.
        """
        shape = image_array.shape[:2]
        
        horizontal_array = numpy.array([numpy.arange(0, shape[0])]).T
        vertical_array = numpy.array([numpy.arange(0, shape[1])])        
        
        # sum_array[x, y] = x + y
        sum_array = numpy.add(horizontal_array, vertical_array)

        stripes_array = numpy.zeros(shape, dtype=bool)
        step = int(STRIPE_RATIO * min(shape))

        # Create stripes by layering alternating triangles.
        for i in range(0, sum(shape), step):
            if (i // step) & 1:
                stripes_array |= (sum_array >= i)
            else:
                stripes_array &= (sum_array < i)
                
        image_array[stripes_array] = 0
        
    def _add_rating_text(self, image_array):
        """Adds the rating in text at the top of the page.
        
        Args:
            image_array (numpy.array): Image to add rating text to.
        """
        rating_text_size, baseline_y = (
            cv2.getTextSize(rating, FONT_FACE, RATING_FONT_SCALE, THICKNESS))
        
        image_height = image_array.shape[0]
        rating_origin = self._origin(image_width, 0, rating_text_size,
                                     baseline=-rating_text_size[1] / 10)
        
        self._put_text(image_array, rating, rating_origin,
                        RATING_FONT_SCALE, thickness_delta=4)
            
    def _create_border(self):
        """Creates a border for the cover to indicate status and rating."""
        image_array = cv2.imread(self.image_path)
        height, width, depth = image_array.shape

        # Resize the image to under 3000 x 3000.
        if height > 3000 or width > 3000:
            maxDim = float(max(height, width)) / 3000
            height = int(height / maxDim)
            width = int(width / maxDim)
            image_array = cv2.resize(image_array, (width, height))

        border_height = int(BORDER_RATIO * height)
        border_width = int(BORDER_RATIO * width)

        new_image_array = numpy.zeros((
            height + (border_height * 2), width + (border_width * 2), depth))

        rating = self.story_json.get_rating()
        rating_color = _Color.RATING[rating]
        new_image_array[:, :] = rating_color
        
        # Add "Under Construction" stripes for incomplete stories.
        if not self.story_json.is_complete():
            self._add_stripes(new_image_array)

        new_image_array[border_height:-border_height,
                        border_width:-border_width] = image_array
        
        cv2.imwrite(self.image_path, new_image_array)

    def _update_opf(self):
        """Updates the book.opf file to include the cover."""
        epub_opf = os.path.join(self.epub_dir, 'book.opf')
        epub_opf_doc = minidom.parse(epub_opf)
        
        meta_cover_xml = '<meta content="coverImage" name="cover"/>'
        meta_cover = minidom.parseString(meta_cover_xml).documentElement 

        item_cover = epub_opf_doc.createElement('item')
        item_cover.setAttribute('id', 'coverImage')
        item_cover.setAttribute(
            'href', values_module.IMAGES_DIR + '/' + self.image_filename)
        item_cover.setAttribute('media-type', self.content_type)

        manifest = epub_opf_doc.getElementsByTagName('manifest')[0]
        manifest.appendChild(item_cover)

        metadata = epub_opf_doc.getElementsByTagName('metadata')[0]
        metadata.appendChild(meta_cover)

        with open(epub_opf, 'w') as epub_opf_file:
            epub_opf_file.write(util_module.encode_xml(epub_opf_doc))

    def create_cover(self):
        """Creates a new cover for the epub."""
        self.images_dir = util_module.create_images_dir(self.epub_dir)
        
        self._grab_image()
        # If no image exists, or the downloaded image cannot be read.
        if not self.image_filename or cv2.imread(self.image_path) is None:
            self._create_image()

        self._create_border()
        self._update_opf()
        

if __name__ == '__main__':
    story_json = story_json_module.StoryJson(291019)
    cover_creator = CoverCreator('', story_json)
    cover_creator.create_cover()