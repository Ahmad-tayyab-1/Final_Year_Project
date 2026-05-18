from django.test import TestCase

from .models import Document
from .youtube import extract_youtube_video_id


class YouTubeVideoIdTests(TestCase):
    def test_document_extracts_standard_watch_url(self):
        doc = Document(source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        self.assertEqual(doc.youtube_video_id, "dQw4w9WgXcQ")

    def test_document_extracts_shortened_youtu_be_url(self):
        doc = Document(source_url="https://youtu.be/dQw4w9WgXcQ?si=abc123")

        self.assertEqual(doc.youtube_video_id, "dQw4w9WgXcQ")

    def test_helper_extracts_watch_url_with_query_params_before_video_id(self):
        video_id = extract_youtube_video_id(
            "https://www.youtube.com/watch?si=abc123&v=dQw4w9WgXcQ"
        )

        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_helper_extracts_embed_url(self):
        video_id = extract_youtube_video_id(
            "https://www.youtube.com/embed/dQw4w9WgXcQ"
        )

        self.assertEqual(video_id, "dQw4w9WgXcQ")

    def test_helper_extracts_shorts_url(self):
        video_id = extract_youtube_video_id(
            "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        )

        self.assertEqual(video_id, "dQw4w9WgXcQ")
