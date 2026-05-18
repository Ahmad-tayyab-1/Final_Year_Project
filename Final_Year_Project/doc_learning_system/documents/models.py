from django.db import models
from django.contrib.auth.models import User
from .youtube import extract_youtube_video_id
 
 
class Document(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title        = models.CharField(max_length=255)
    file         = models.FileField(upload_to="documents/", blank=True)   # blank=True for YouTube
    file_type    = models.CharField(max_length=10)
    source_url   = models.URLField(blank=True, default="")                # NEW: YouTube URL
    uploaded_at  = models.DateTimeField(auto_now_add=True)
    text_content = models.TextField(blank=True)
    total_pages  = models.IntegerField(default=0)
 
    def __str__(self):
        return self.title
 
    class Meta:
        ordering = ["-uploaded_at"]
 
    @property
    def is_youtube(self):
        return self.file_type == "youtube"
 
    @property
    def youtube_video_id(self):
        """Extract YouTube video ID from source_url"""
        return extract_youtube_video_id(self.source_url)
 
 
class ChatMessage(models.Model):
    document       = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chat_messages")
    user_message   = models.TextField()
    bot_response   = models.TextField()
    page_reference = models.IntegerField(null=True, blank=True)
    timestamp      = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["timestamp"]
 
 
class Highlight(models.Model):
    document   = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="highlights")
    text       = models.TextField()
    page_number = models.IntegerField()
    color      = models.CharField(max_length=20, default="yellow")
    created_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["page_number", "created_at"]
 
 
class Flashcard(models.Model):
    document    = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="flashcards")
    front       = models.TextField()
    back        = models.TextField()
    source_text = models.TextField(blank=True)
    page_number = models.IntegerField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["-created_at"]
 
 
class ShortQuestion(models.Model):
    document    = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="short_questions")
    question    = models.TextField()
    answer      = models.TextField()
    source_text = models.TextField(blank=True)
    page_number = models.IntegerField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["-created_at"]
 
 
class MCQQuestion(models.Model):
    document       = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="mcqs")
    question       = models.TextField()
    option_a       = models.CharField(max_length=500)
    option_b       = models.CharField(max_length=500)
    option_c       = models.CharField(max_length=500)
    option_d       = models.CharField(max_length=500)
    correct_answer = models.CharField(max_length=1)
    explanation    = models.TextField(blank=True)
    source_text    = models.TextField(blank=True)
    page_number    = models.IntegerField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        ordering = ["-created_at"]
