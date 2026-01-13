import os

from .common import PostProcessor
from ..utils import PostProcessingError, replace_extension


class WriteChaptersPP(PostProcessor):
    """Write chapter information to external file for debugging/reference"""

    def __init__(self, downloader=None, force_embed=False):
        super().__init__(downloader)
        self._force_embed = force_embed

    def run(self, info):
        chapters = info.get('chapters')
        if not chapters:
            self.to_screen('No chapters found, skipping chapter file creation')
            return [], info

        filepath = info.get('filepath')
        if not filepath:
            self.report_warning('No filepath found, cannot write chapter file')
            return [], info

        # Write external chapter file
        # Use -chapters.txt naming to avoid safety checks that reject unusual extensions
        base_filename = os.path.splitext(filepath)[0]
        chapter_filename = f'{base_filename}-chapters.txt'
        try:
            self.to_screen(f'Writing {len(chapters)} chapters to {os.path.basename(chapter_filename)}')
            self._write_chapters_file(chapters, chapter_filename, info)
        except Exception as e:
            raise PostProcessingError(f'Failed to write chapter file: {e}')

        # Force chapter embedding if requested
        if self._force_embed:
            # Set flag to ensure FFmpegMetadataPP embeds chapters
            info['__chapters_embed_forced'] = True

        return [], info

    def _write_chapters_file(self, chapters, filename, info):
        """Write chapters to a human-readable text file"""
        with open(filename, 'w', encoding='utf-8') as f:
            # Write header with video information
            f.write('# Video Chapters\n')
            if info.get('title'):
                f.write(f'# Title: {info["title"]}\n')
            if info.get('webpage_url'):
                f.write(f'# URL: {info["webpage_url"]}\n')
            f.write(f'# Total Chapters: {len(chapters)}\n')
            f.write('#\n')
            f.write('# Format: [HH:MM:SS] - Chapter Title\n')
            f.write('#' + '=' * 70 + '\n\n')

            # Write each chapter
            for chapter in chapters:
                start_time = chapter.get('start_time', 0)
                title = chapter.get('title', 'Untitled')

                # Format timestamp as HH:MM:SS
                hours = int(start_time // 3600)
                minutes = int((start_time % 3600) // 60)
                seconds = int(start_time % 60)
                timestamp = f'{hours:02d}:{minutes:02d}:{seconds:02d}'

                f.write(f'[{timestamp}] {title}\n')

            f.write('\n# End of chapters\n')

        self.to_screen(f'Chapter file written successfully')
