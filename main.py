import os
import re
import threading
from xml.dom import minidom

from lib import cover_creator as cover_creator_module
from lib import data_manager as data_manager_module
from lib import description_page as description_page_module
from lib import epub_zip as epub_zip_module
from lib import story_json as story_json_module
from lib import util as util_module
from lib import values as values_module


_EPUB_URL = "https://www.fimfiction.net/download_epub.php?story={story_id}"
_EPUB_LOCK = threading.Lock()
_PRINT_LOCK = threading.Lock()
_DATA_LOCK = threading.Lock()

_CONSUMER_NUM = 5 # Magic number for number of consumer threads.


class EpubProducer(threading.Thread):
    def __init__(self):
        super(EpubProducer, self).__init__()
        self.listOfEpubs = os.listdir(values_module.ORIGINALS_DIR)[::-1]
        
    def request(self):
        if len(self.listOfEpubs):
            return self.listOfEpubs.pop(-1)
        return ''
    
    def remaining(self):
        return len(self.listOfEpubs)
    
    def run(self):
        while self.listOfEpubs:
            pass
        

class EpubConsumer(threading.Thread):
    def __init__(self, producer, data_manager):
        super(EpubConsumer, self).__init__()
        self.producer = producer
        self.data_manager = data_manager
        
    def run(self):
        while self.producer.remaining():
            with _EPUB_LOCK:
                epub_filename = self.producer.request()
            
            if epub_filename:
#                 try:
                self.check_for_updates(epub_filename)
#                 except Exception as e:
#                     with _PRINT_LOCK:
#                         print (epub_filename + ' had an error.').upper()
#                         raise e
                    
    def check_for_updates(self, epub_filename):
        """Checks if the epub needs update and performs updates if necessary.
        
        Args:
            epub_filename: The filename of the epub.
        """
        original_epub_filepath = os.path.join(
            values_module.ORIGINALS_DIR, epub_filename)
        epub_dir = epub_zip_module.expand(
            original_epub_filepath, new_location=values_module.UPDATED_DIR)
        util_module.correct_meta(epub_dir)
        
        story_json = self.get_story_json(epub_dir)
        if story_json is None:
            return
        
        story_id = story_json.get_id()
        date_modified = story_json.get_date_modified()
        
        if not os.path.exists(
            os.path.join(values_module.UPDATED_DIR, epub_filename)):
            with _DATA_LOCK:
                self.data_manager.update_epub_binary(story_id, date_modified)
            self.update_story(epub_dir, story_json)
        else:
            with _DATA_LOCK:
                epub_needs_update = self.data_manager.does_epub_needs_update(
                    story_id, date_modified, update=True)
            if epub_needs_update:
                self.update_story(epub_dir, story_json)
            else:
                with _PRINT_LOCK:
                    print '%s is up to date.' % story_json.get_title()
                epub_zip_module.remove(epub_dir)
                
    def get_story_json(self, epub_dir):
        """Retrieves the Story JSON.
        
        Args:
            epub_dir (string): Directory of the unzipped epub.
            
        Returns:
            StoryJson object loaded with the story details.
        """
        story_id = None
        epub_opf = os.path.join(epub_dir, 'book.opf')
        
        try:
            epub_opf_doc = minidom.parse(epub_opf)
            identifier = epub_opf_doc.getElementsByTagName('dc:identifier')[0]
            story_url = identifier.childNodes[0].data
            story_id = re.match(
                r'https?://www.fimfiction.net/story/(\d+)/', story_url).group(1)
            return story_json_module.StoryJson(int(story_id))
        except story_json_module.InvalidStoryIdError:
            with _PRINT_LOCK:
                print 'Story does not exist.',
                print (story_id if story_id else 'Unknown Story Id.',
                       epub_dir.rsplit(os.sep, 1)[1])
            epub_zip_module.remove(epub_dir)
            
    def download_epub(self, epub_dir, story_id):
        """Downloads a fresh copy of the epub from fimfiction.net
        
        Args:
            epub_dir (str): Directory of the unzipped epub.
            story_id (int): ID of the story.
        """
        epub_url = _EPUB_URL.format(story_id=story_id)
        epub_filename = epub_dir + '.epub'
        
        response = util_module.http_get_request(epub_url)
        
        epub_zip_module.remove(epub_dir)
        epub_zip_module.remove(epub_filename)
        
        with open(epub_filename, 'wb') as epub_file:
            epub_file.write(response.read())
            
        epub_zip_module.expand(
            epub_filename, new_location=values_module.UPDATED_DIR)
        
        util_module.correct_meta(epub_dir)
        
    def update_story(self, epub_dir, story_json):
        """Updates the story with a cover and a description page.
        
        Args:
            epub_dir (str): Directory of the unzipped epub.
            story_json (StoryJson): Story JSON object.
        """
        self.download_epub(epub_dir, story_json.get_id())
        
        # Create the cover for the epub.
        cover_creator = (
            cover_creator_module.CoverCreator(epub_dir, story_json))
        cover_creator.create_cover()
        
        # Create the description page for the epub.
        description_page = (
            description_page_module.DescriptionPage(epub_dir, story_json))
        description_page.create_page()
        
        # Download images found in the description of the epub.
        story_json.download_images(epub_dir)

        epub_zip_module.compress(epub_dir, remove_dir=True)
        
        with _PRINT_LOCK:
            print '%s has been updated.' % story_json.get_title()



def setup():
    """Sets up the expected folders and cleans them of subfolders."""
    for directory in values_module.DIRECTORIES:
        # Create Originals and Updated directories
        if not os.path.exists(directory):
            os.makedirs(directory)
        # Remove folders from Originals and Updated directories
        for story in os.listdir(directory):
            epub = os.path.join(directory, story)
            if os.path.isdir(epub):
                epub_zip_module.remove(epub)

def main():
    """Runs through all of the epubs and updates them."""
    setup()
    data_manager = data_manager_module.DataManager()
    
    producer = EpubProducer()
    consumers = [
        EpubConsumer(producer, data_manager) for n in range(_CONSUMER_NUM)]
    
    producer.start()
    [consumer.start() for consumer in consumers]
    producer.join()
    [consumer.join() for consumer in consumers]
            
    data_manager.write_seen_blocks()
    
    print '\nAll stories updated.'


if __name__ == '__main__':
    main()
