from django.contrib import admin
from .models import *

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_type', 'total_pages', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['document', 'user_message', 'page_reference', 'timestamp']
    list_filter = ['timestamp']

@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ['document', 'front', 'page_number', 'created_at']
    list_filter = ['document', 'created_at']

@admin.register(MCQQuestion)
class MCQQuestionAdmin(admin.ModelAdmin):
    list_display = ['document', 'question', 'correct_answer', 'page_number']
    list_filter = ['document', 'created_at']

@admin.register(ShortQuestion)
class ShortQuestionAdmin(admin.ModelAdmin):
    list_display = ['document', 'question', 'page_number']
    list_filter = ['document', 'created_at']

@admin.register(Highlight)
class HighlightAdmin(admin.ModelAdmin):
    list_display = ['document', 'text', 'page_number', 'color']
    list_filter = ['document', 'page_number', 'color']