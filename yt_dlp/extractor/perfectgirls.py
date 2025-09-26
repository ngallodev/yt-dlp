import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
    strip_or_none,
    url_or_none,
)


class PerfectGirlsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?perfectgirls\.xxx/video/(?P<id>\d+)/?'
    _TESTS = [{
        'url': 'https://www.perfectgirls.xxx/video/623534/',
        'info_dict': {
            'id': '623534',
            'ext': 'mp4',
            'title': 'Big tits smut with tempting Susy Gala and Tommy Cabrio from Enjoyx',
            'description': 'Big tits smut with tempting Susy Gala and Tommy Cabrio from Enjoyx',
            'thumbnail': r're:https?://.*\.jpg$',
            'age_limit': 18,
        },
        'params': {
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # Extract title from various possible locations
        title = (
            self._og_search_title(webpage, default=None)
            or self._html_search_regex(
                r'<title>([^<]+)', webpage, 'title', default=None)
            or self._html_search_regex(
                r'<h1[^>]*>([^<]+)</h1>', webpage, 'title', fatal=False)
        )

        # Extract video sources - search for all source tags directly
        formats = []

        # Extract all source elements directly from the entire webpage
        source_matches = re.findall(
            r'<source[^>]+src=["\']([^"\']+\.mp4[^"\']*)["\'][^>]*(?:title=["\']([^"\']*)["\'])?[^>]*>',
            webpage, re.MULTILINE | re.DOTALL)

        for source_url, quality_label in source_matches:
            if not source_url:
                continue

            # Clean and validate URL
            source_url = url_or_none(source_url.strip())
            if not source_url:
                continue

            # Extract quality information
            height = None
            format_id = 'unknown'

            # First try to get quality from title/label
            if quality_label and quality_label != 'Auto':
                format_id = quality_label
                height = int_or_none(self._search_regex(
                    r'(\d+)p?', quality_label, 'height', default=None))

            # If no quality from label, try URL
            if not height:
                height_match = self._search_regex(
                    r'_(\d+)p\.mp4', source_url, 'height', default=None)
                if height_match:
                    height = int_or_none(height_match)
                    format_id = f'{height}p'
                elif '_720p' not in source_url and '.' in source_url:
                    # This might be the base quality version (usually 480p)
                    if source_url.endswith(('.mp4/', '.mp4')):
                        height = 480
                        format_id = '480p'

            # The URLs appear to be HLS master playlists, not direct MP4s
            # Try to extract HLS formats
            hls_formats = self._extract_m3u8_formats(
                source_url, video_id, 'mp4', entry_protocol='m3u8_native',
                m3u8_id=format_id, fatal=False)

            if hls_formats:
                formats.extend(hls_formats)
            else:
                # Fallback to direct URL if HLS extraction fails
                formats.append({
                    'url': source_url,
                    'format_id': format_id,
                    'height': height,
                    'ext': 'mp4',
                    'quality': height if height else 0,
                })

        # Fallback: look for direct video URL patterns in JavaScript/page source
        if not formats:
            # Look for common video URL patterns
            video_url_matches = re.findall(
                r'(?:video_url|mp4_url|file)["\'\s]*:["\'\s]*([^"\']+\.mp4[^"\']*)',
                webpage, re.IGNORECASE)

            for video_url in video_url_matches:
                video_url = url_or_none(video_url.strip())
                if video_url:
                    formats.append({
                        'url': video_url,
                        'format_id': 'mp4',
                        'ext': 'mp4',
                    })

        if not formats:
            self.report_warning('No video formats found')

        # Extract metadata
        description = (
            self._og_search_description(webpage, default=None)
            or self._html_search_meta('description', webpage, default=None)
            or self._html_search_regex(
                r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)',
                webpage, 'description', fatal=False)
        )

        duration = (
            parse_duration(self._html_search_meta('duration', webpage, default=None))
            or parse_duration(self._search_regex(
                r'duration["\'\s]*:["\'\s]*["\']?(\d+)["\']?',
                webpage, 'duration', default=None))
        )

        view_count = int_or_none(self._search_regex(
            r'(?:views?|watch)["\'\s]*:["\'\s]*["\']?(\d+)',
            webpage, 'view count', default=None))

        # Extract thumbnail
        thumbnail = (
            self._og_search_thumbnail(webpage)
            or self._html_search_meta('thumbnail', webpage, default=None)
        )

        # Set age limit for adult content
        age_limit = self._rta_search(webpage) or 18

        return {
            'id': video_id,
            'title': strip_or_none(title),
            'description': strip_or_none(description),
            'formats': formats,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'age_limit': age_limit,
        }
