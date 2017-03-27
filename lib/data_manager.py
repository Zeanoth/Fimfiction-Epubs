"""Manages the binary data stored for the epubs."""

import os
import struct
import sys

import values as values_module

class Field:
    STORY_ID = 'story_id'
    DATE_MODIFIED = 'date_modified'
    
    ENCODINGS = {
        STORY_ID: ('>I', 4),
        DATE_MODIFIED: ('>I', 4),
    }


class DataManager(object):
    def __init__(self):
        if not os.path.isfile(values_module.DATA_FILE):
            open(values_module.DATA_FILE, 'wb').close()
        self.block_length = sum(
            [value[1] for value in Field.ENCODINGS.values()])

        self.epub_data_by_id = self._data_by_id()
        self.seen_story_ids = set()

    def _read(self):
        """Parses the data of the epub data file.
        
        Returns:
            List of dicts with epub data.
        """
        blocks = []
        with open(values_module.DATA_FILE, 'rb') as data_file:
            while True:
                block_binary_data = data_file.read(self.block_length)
                if len(block_binary_data) != self.block_length:
                    break
                block = {}
                block_length_read = 0
                for field in Field.ENCODINGS:
                    data_format, byte_count = Field.ENCODINGS.get(field)
                    block[field] = struct.unpack(
                        data_format,
                        block_binary_data[block_length_read:
                                          block_length_read + byte_count])[0]
                    block_length_read += byte_count
                blocks.append(block)
        return blocks

    def _data_by_id(self):
        return {
            block.get(Field.STORY_ID): block for block in self._read()
        }

    def _check_data_integrity(self, data_blocks):
        """Ensures that all data blocks have all their pieces.
        
        Args:
            data_blocks (list): Collection of data blocks.
        """
        for field in Field.ENCODINGS:
            for block in data_blocks:
                if field not in block:
                    raise ValueError(
                        'DataManager was called with missing data.')
        
    def _write(self, data_blocks):
        """Writes data back to the epub data file.
        
        Args:
            data_blocks (list): Colletion of data blocks to write back.
        """
        self._check_data_integrity(data_blocks)
        with open(values_module.DATA_FILE, 'wb') as data_file:
            for block in data_blocks:
                for field in Field.ENCODINGS:
                    data_format = Field.ENCODINGS.get(field)[0]
                    data_file.write(
                        struct.pack(data_format, block.get(field)))

    def does_epub_needs_update(self, story_id, date_modified, update=False):
        """Checks if a story is up to date.
        
        Args:
            story_id (int): ID of the story.
            date_modified (int)" last date the story was modified.
            update (bool): Whether to update the story if it needs updating.
            
        Returns:
            Whether the story needs updating.
        """
        epub_data = self.epub_data_by_id.get(story_id)
        epub_needs_update = (
            epub_data is None or
            date_modified > epub_data.get(Field.DATE_MODIFIED))

        if update:
            if epub_needs_update:
                self.update_epub_binary(story_id, date_modified)
            else:
                self.seen_story_ids.add(story_id)

        return epub_needs_update

    def update_epub_binary(self, story_id, date_modified):
        """Updates the block data with new data for a story.
        
        Args:
            story_id (int): ID of the story.
            date_modified (int): Last date story was modified.
        """
        self.seen_story_ids.add(story_id)
        self.epub_data_by_id[story_id] = {
            Field.STORY_ID: int(story_id),
            Field.DATE_MODIFIED: date_modified
        }

    def write_seen_blocks(self):
        """Writes all blocks that were seen back into the data file."""
        self._write([self.epub_data_by_id[story_id]
                     for story_id in self.seen_story_ids])

if __name__ == '__main__':
    data_manager = DataManager()
    data_manager.write([
        {Field.STORY_ID: 82359, Field.DATE_MODIFIED: 1434403951}
    ])
    print data_manager.read()
