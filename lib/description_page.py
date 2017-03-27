"""Creates the description page to be included with the epub."""

import os
from xml.dom import minidom

import util as util_module


_PAGE_BOILERPLATE = ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" '
                     '"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">')

_PAGE_STRUCTURE = '''
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <link rel="stylesheet" type="text/css" href="styles.css" />
        <title>Test Book</title>
    </head>
    <body></body>
</html>
'''

class Genre(object):
    SECOND_PERSON = '2nd Person'
    ADVENTURE = 'Adventure'
    ALTERNATE_UNIVERSE = 'Alternate Universe'
    ANTHRO = 'Anthro'
    COMEDY = 'Comedy'
    CROSSOVER = 'Crossover'
    DARK = 'Dark'
    DRAMA = 'Drama'
    EQUESTRIA_GIRLS = 'Equestria Girls'
    GORE = 'Gore'
    HORROR = 'Horror'
    HUMAN = 'Human'
    MYSTERY = 'Mystery'
    RANDOM = 'Random'
    ROMANCE = 'Romance'
    SAD = 'Sad'
    SCI_FI = 'Sci-Fi'
    SEX = 'Sex'
    SLICE_OF_LIFE = 'Slice of Life'
    THRILLER = 'Thriller'
    TRAGEDY = 'Tragedy'
    
    COLORS = {  # Genre =   (Background, Border, Box Shadow)
        SECOND_PERSON:      ('#02a1db', '#0289ba', '#02c1ff'),
        ADVENTURE:          ('#45c950', '#3aaa44', '#52f160'),
        ALTERNATE_UNIVERSE: ('#808080', '#737373', '#a3a3a3'),
        ANTHRO:             ('#b5695a', '#99594c', '#d97e6c'),
        COMEDY:             ('#f5a900', '#d08f00', '#ffca00'),
        CROSSOVER:          ('#47b8a0', '#3c9c88', '#55dcc0'),
        DARK:               ('#b93737', '#9d2e2e', '#de4242'),
        DRAMA:              ('#ec50ca', '#c944ac', '#ff60f2'),
        EQUESTRIA_GIRLS:    ('#4d3281', '#412b6e', '#5c3c9b'),
        GORE:               ('#742828', '#622222', '#8b3030'),
        HORROR:             ('#6d232f', '#5d1e28', '#832a38'),
        HUMAN:              ('#b5835a', '#996f4c', '#d99d6c'),
        MYSTERY:            ('#444444', '#3a3a3a', '#525252'),
        RANDOM:             ('#3f74ce', '#3562af', '#4b8bf7'),
        ROMANCE:            ('#974bff', '#803fd8', '#b55aff'),
        SAD:                ('#bd42a7', '#a0388d', '#e24fc8'),
        SCI_FI:             ('#5d63a5', '#4f548c', '#7077c6'),
        SEX:                ('#992584', '#821f70', '#b72c9e'),
        SLICE_OF_LIFE:      ('#4b86ff', '#3f71d8', '#5aa0ff'),
        THRILLER:           ('#d62b2b', '#b62525', '#ff3434'),
        TRAGEDY:            ('#ffb54b', '#d8993f', '#ffd95a'),
        }


class DescriptionPage(object):
    def __init__(self, epub_dir, story_json):
        self.epub_dir = epub_dir
        self.story_json = story_json
        self.page_doc = minidom.parseString(_PAGE_STRUCTURE)
        
    def _update_opf(self):
        """Updates the book.opf to include the description page."""
        epub_opf = os.path.join(self.epub_dir, 'book.opf')
        epub_opf_doc = minidom.parse(epub_opf)
        
        item_xml = ('<item href="description.html" id="description" '
                    'media-type="application/xhtml+xml"/>')
        
        item = minidom.parseString(item_xml).documentElement
        
        manifest = epub_opf_doc.getElementsByTagName('manifest')[0]
        manifest.appendChild(item)
        
        itemref = epub_opf_doc.createElement('itemref')
        itemref.setAttribute('idref', 'description')

        spine = epub_opf_doc.getElementsByTagName('spine')[0]
        spine.insertBefore(itemref, spine.childNodes[0])
        
        with open(epub_opf, 'w') as epub_opf_file:
            epub_opf_file.write(util_module.encode_xml(epub_opf_doc))
        
    def _update_ncx(self):
        """Updates the book.ncx to include the description page."""
        epub_ncx = os.path.join(self.epub_dir, 'book.ncx')
        epub_ncx_doc = minidom.parse(epub_ncx)
        
        navpoint_xml = '''
            <navPoint id="description" playOrder="0">
                <navLabel><text>Story Description</text></navLabel>
                <content src="description.html" />
            </navPoint>
        '''
        navpoint = minidom.parseString(navpoint_xml).documentElement
        
        navmap = epub_ncx_doc.getElementsByTagName('navMap')[0]
        navmap.insertBefore(navpoint, navmap.childNodes[0])
        
        with open(epub_ncx, 'w') as epub_ncx_file:
            epub_ncx_file.write(util_module.encode_xml(epub_ncx_doc))
            
    def _update_meta_files(self):
        self._update_opf()
        self._update_ncx()
        
    def _create_category_div(self, genre):
        """Creates the div for the category as they appear on fimfiction.net.
        
        Args:
            genre (str): Category to create the div for.
        
        Returns:
            DOM div object.
        """
        background, border, box_shadow = Genre.COLORS[genre]
        
        div = self.page_doc.createElement('div')
        div.attributes['style'] = (
            'border-style:solid; border-width:1px; color:white; '
            'display:inline-block; font-family:Calibri,Arial; '
            'margin-bottom:5px; margin-right:5px; padding:8px 12px;'
            )
        
        div.attributes['style'].value += (
            'background-color:{background};').format(background=background)
        div.attributes['style'].value += (
            'text-shadow:-1px -1px {border}; '
            'border-color:{border};').format(border=border)
        div.attributes['style'].value += (
            'box-shadow:0px 1px 0px {box_shadow} inset;').format(
                box_shadow=box_shadow)
        
        div.appendChild(self.page_doc.createTextNode(genre))
        
        return div
    
    def _create_description_page(self):
        """Create the description page."""
        html = self.page_doc.getElementsByTagName('html')[0]
        body = html.getElementsByTagName('body')[0]
        
        center_paragraph = self.page_doc.createElement('p')
        center_paragraph.setAttribute('align', 'center')

        body.appendChild(center_paragraph)
        
        for category in self.story_json.get_categories():
            center_paragraph.appendChild(self._create_category_div(category))
            
        body.appendChild(self.page_doc.createElement('hr'))
        body.appendChild(self.page_doc.createElement('description'))
        
        description = util_module.encode(self.story_json.get_description())
        
        description_filename = os.path.join(self.epub_dir, 'description.html')
        with open(description_filename, 'w') as description_file:
            description_file.write(_PAGE_BOILERPLATE + (
                util_module.encode_xml(html).replace(
                    '<description/>', description)))
    
    def create_page(self):
        self._update_meta_files()
        self._create_description_page()