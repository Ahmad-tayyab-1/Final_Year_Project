from django.urls import path
from . import views
 
app_name = "documents"
 
urlpatterns = [
    path("",                               views.home,                          name="home"),
    path("upload/",                        views.upload_document,               name="upload"),
    path("youtube/",                       views.process_youtube,               name="process_youtube"),
    path("document/<int:doc_id>/",         views.document_detail,               name="document_detail"),
    path("document/<int:doc_id>/file/",    views.serve_document,                name="serve_document"),
    path("document/<int:doc_id>/view/",    views.serve_document_html,           name="serve_document_html"),
    path("chat/<int:doc_id>/",             views.chat,                          name="chat"),
    path("delete/<int:doc_id>/",           views.delete_document,               name="delete_document"),
    path("explain/<int:doc_id>/",          views.explain_selection,             name="explain_selection"),
    path("flashcards/<int:doc_id>/",       views.create_flashcards,             name="create_flashcards"),
    path("mcqs/<int:doc_id>/",             views.create_mcqs_from_text,         name="create_mcqs"),
    path("short-questions/<int:doc_id>/",  views.create_short_questions_from_text, name="create_short_questions"),
    path("highlight/<int:doc_id>/",        views.save_highlight,                name="save_highlight"),
    path("register/",                      views.register,                      name="register"),
    path("write/",                         views.writing_assistant,              name="writing_assistant"),
    path("write/ai/",                      views.writing_ai,                    name="writing_ai"),
]