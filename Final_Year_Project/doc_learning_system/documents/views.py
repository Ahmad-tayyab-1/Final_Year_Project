from django.shortcuts import render, redirect, get_object_or_404
# pyrefly: ignore [missing-import]
from .forms import CustomUserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.auth.decorators import login_required
import os
import re

# pyrefly: ignore [missing-import]
from .models import Document, ChatMessage, Highlight, Flashcard, ShortQuestion, MCQQuestion
# pyrefly: ignore [missing-import]
from .utils import DocumentProcessor, AIAssistant, YouTubeProcessor, WebSearch

GUEST_UPLOAD_LIMIT = 3


def _bounded_int(value, default, minimum=1, maximum=10):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(number, maximum))


def _casual_chat_response(message):
    """Handle greetings before sending the message into document Q&A."""
    normalized = re.sub(r"[^a-z0-9\s]", " ", message.lower()).strip()
    normalized = re.sub(r"\s+", " ", normalized)

    greetings = {
        "hi", "hii", "hello", "hey", "yo", "salam", "assalamualaikum",
        "assalamu alaikum", "good morning", "good afternoon", "good evening",
    }
    check_ins = {
        "how are you", "how r u", "how are u", "what s up", "whats up",
        "wassup", "sup", "how you doing",
    }
    thanks = {"thanks", "thank you", "thx", "ty"}
    vague = {"what", "hwat", "ok", "okay", "hmm", "huh"}

    if normalized in greetings:
        return (
            "Hey! I'm here with you. How are you doing? "
            "You can ask me anything about this document or video whenever you're ready."
        )
    if normalized in check_ins:
        return (
            "I'm doing well, thanks for asking. How are you? "
            "If you want, we can go through this material together."
        )
    if normalized in thanks:
        return "You're welcome. Ask me the next thing you want to understand from this material."
    if normalized in vague:
        return (
            "I'm here. Ask me a specific question about the document or video, "
            "or tell me what topic you want explained."
        )
    return None


def _should_use_live_web(message):
    """Use live search for current/general questions that may not be in the source."""
    normalized = re.sub(r"[^a-z0-9\s]", " ", message.lower()).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    live_terms = {
        "latest", "current", "today", "now", "news", "recent", "price",
        "weather", "president", "prime minister", "ceo", "released",
        "update", "live", "internet", "web", "search",
    }
    question_starts = (
        "who is", "who was", "what is", "what are", "when is", "when did",
        "where is", "where can", "how much", "how many",
    )
    return any(term in normalized for term in live_terms) or normalized.startswith(question_starts)


def _guest_doc_ids(request):
    """Return list of document IDs stored in the anonymous session."""
    return request.session.get('guest_doc_ids', [])


def _guest_can_upload(request):
    """Check whether an anonymous user still has free uploads remaining."""
    return len(_guest_doc_ids(request)) < GUEST_UPLOAD_LIMIT


def _guest_add_doc(request, doc_id):
    ids = _guest_doc_ids(request)
    ids.append(doc_id)
    request.session['guest_doc_ids'] = ids


def _get_doc_for_request(request, doc_id):
    """Return a Document if the current user (or anonymous session) owns it."""
    if request.user.is_authenticated:
        return get_object_or_404(Document, id=doc_id, user=request.user)

    # Check if doc_id is in guest_doc_ids (handling possible int/str mismatch from session)
    guest_ids = [str(i) for i in _guest_doc_ids(request)]
    if str(doc_id) in guest_ids:
        return get_object_or_404(Document, id=doc_id, user__isnull=True)
    return None


def home(request):
    if request.user.is_authenticated:
        documents = Document.objects.filter(user=request.user).prefetch_related(
            "chat_messages", "flashcards", "mcqs").all()
    else:
        ids = _guest_doc_ids(request)
        documents = Document.objects.filter(id__in=ids, user__isnull=True).prefetch_related(
            "chat_messages", "flashcards", "mcqs") if ids else []
    total_flashcards = sum(doc.flashcards.count() for doc in documents)
    total_mcqs = sum(doc.mcqs.count() for doc in documents)
    guest_remaining = max(0, GUEST_UPLOAD_LIMIT - len(_guest_doc_ids(request))
                          ) if not request.user.is_authenticated else None
    return render(request, "documents/home.html", {
        "documents": documents,
        "guest_remaining": guest_remaining,
        "total_flashcards": total_flashcards,
        "total_mcqs": total_mcqs,
    })


def upload_document(request):
    if not request.user.is_authenticated and not _guest_can_upload(request):
        messages.info(
            request, "You've used your 3 free uploads. Please create a free account to continue.")
        return redirect("documents:register")
    if request.method != "POST":
        guest_remaining = max(0, GUEST_UPLOAD_LIMIT - len(_guest_doc_ids(request))
                              ) if not request.user.is_authenticated else None
        return render(request, "documents/upload.html", {"guest_remaining": guest_remaining})

    file = request.FILES.get("file")
    if not file:
        messages.error(request, "No file selected.")
        return redirect("documents:upload")

    title = request.POST.get("title", "").strip() or file.name
    file_ext = file.name.rsplit(".", 1)[-1].lower()

    if file_ext not in ["pdf", "doc", "docx", "pptx", "xlsx", "txt"]:
        messages.error(request, f"Unsupported file type: .{file_ext}")
        return redirect("documents:upload")

    if file.size > 10 * 1024 * 1024:
        messages.error(request, "File too large. Maximum is 10 MB.")
        return redirect("documents:upload")

    doc = Document.objects.create(
        user=request.user if request.user.is_authenticated else None, title=title, file=file, file_type=file_ext)
    try:
        proc = DocumentProcessor()
        if file_ext == "pdf":
            text, pages, total_pages = proc.extract_text_with_pages(
                doc.file.path)
            doc.total_pages = total_pages
        elif file_ext in ["doc", "docx", "pptx", "xlsx"]:
            # Extract text for AI processing
            try:
                if file_ext in ["doc", "docx"]:
                    text = proc.extract_text_from_doc(
                        doc.file.path) if file_ext == "doc" else proc.extract_text_from_docx(doc.file.path)
                elif file_ext == "pptx":
                    text = proc.extract_text_from_pptx(doc.file.path)
                else:  # xlsx
                    text = proc.extract_text_from_xlsx(doc.file.path)
            except Exception as extract_err:
                # If text extraction fails, use a placeholder
                messages.warning(
                    request, f"Could not fully extract text from file: {extract_err}. File will still be processed.")
                text = f"[Document: {title}] - Text extraction encountered an issue."
        else:
            text = proc.extract_text_from_txt(doc.file.path)

        doc.text_content = proc.clean_text(text)
        doc.save()
        if not request.user.is_authenticated:
            _guest_add_doc(request, doc.id)
        messages.success(request, f'"{doc.title}" uploaded and processed.')
    except Exception as e:
        doc.delete()
        messages.error(request, f"Processing failed: {e}")
        return redirect("documents:upload")

    return redirect("documents:document_detail", doc_id=doc.id)


def process_youtube(request):
    """Fetch YouTube transcript and create a Document from it."""
    if not request.user.is_authenticated and not _guest_can_upload(request):
        messages.info(
            request, "You've used your 3 free uploads. Please create a free account to continue.")
        return redirect("documents:register")
    if request.method != "POST":
        return redirect("documents:upload")

    url = request.POST.get("youtube_url", "").strip()
    title = request.POST.get("title", "").strip()

    if not url:
        messages.error(request, "Please provide a YouTube URL.")
        return redirect("documents:upload")

    yt = YouTubeProcessor()
    video_id = yt.extract_video_id(url)

    if not video_id:
        messages.error(
            request, "Could not parse a video ID from that URL. Please use a standard YouTube link.")
        return redirect("documents:upload")

    try:
        transcript_text, video_title = yt.get_transcript(video_id)
    except RuntimeError as e:
        messages.error(request, str(e))
        return redirect("documents:upload")

    if not title:
        title = video_title or f"YouTube – {video_id}"

    doc = Document.objects.create(
        user=request.user if request.user.is_authenticated else None,
        title=title,
        file_type="youtube",
        source_url=url,
        text_content=transcript_text,
    )
    if not request.user.is_authenticated:
        _guest_add_doc(request, doc.id)

    messages.success(request, f'"{doc.title}"')
    return redirect("documents:document_detail", doc_id=doc.id)


def document_detail(request, doc_id):
    doc = _get_doc_for_request(request, doc_id)
    if doc is None:
        messages.error(request, "Please log in to view this document.")
        return redirect("login")
    return render(request, "documents/document_detail.html", {
        "document":        doc,
        "chat_messages":   doc.chat_messages.all(),
        "flashcards":      doc.flashcards.all(),
        "mcqs":            doc.mcqs.all(),
        "short_questions": doc.short_questions.all(),
        "highlights":      doc.highlights.all(),
    })


@xframe_options_exempt
def serve_document(request, doc_id):
    """Serve document file with framing allowed (supports guests)."""
    doc = _get_doc_for_request(request, doc_id)
    if doc is None:
        from django.http import Http404
        raise Http404("Document not found or access denied")
    if not doc.file:
        from django.http import Http404
        raise Http404("Document file not found")

    # Determine content type based on file extension
    content_type = 'application/octet-stream'  # default
    if doc.file_type == 'pdf':
        content_type = 'application/pdf'
    elif doc.file_type == 'docx':
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif doc.file_type == 'pptx':
        content_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    elif doc.file_type == 'xlsx':
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    response = FileResponse(doc.file.open(), content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{doc.title}.{doc.file_type}"'
    return response


@xframe_options_exempt
def serve_document_html(request, doc_id):
    """Serve Office documents as HTML for proper viewing (supports guests)."""
    doc = _get_doc_for_request(request, doc_id)
    if doc is None:
        from django.http import Http404
        raise Http404("Document not found or access denied")
    if not doc.file:
        from django.http import Http404
        raise Http404("Document file not found")

    if doc.file_type == 'pdf':
        # For PDFs, redirect to the file serving view
        from django.shortcuts import redirect
        return redirect('documents:serve_document', doc_id=doc_id)

    # Generate HTML content for Office documents
    proc = DocumentProcessor()
    html_content = proc.generate_office_html(doc)

    return render(request, 'documents/office_viewer.html', {
        'document': doc,
        'html_content': html_content,
    })


@require_http_methods(["POST"])
def chat(request, doc_id):
    doc = _get_doc_for_request(request, doc_id)
    if doc is None:
        return JsonResponse({"error": "Please log in to use this feature."}, status=403)
    user_message = request.POST.get("message", "").strip()
    if not user_message:
        return JsonResponse({"error": "Empty message"}, status=400)

    casual_response = _casual_chat_response(user_message)
    if casual_response:
        bot_response, page_ref = casual_response, None
    else:
        source_info = f"Title: {doc.title}\nType: {doc.file_type}"
        if doc.file_type == "youtube":
            metadata = YouTubeProcessor().get_video_metadata(doc.source_url)
            source_info = "\n".join([
                f"Video title: {metadata.get('title') or doc.title}",
                f"Channel/creator: {metadata.get('author_name') or 'Unknown'}",
                f"Channel URL: {metadata.get('author_url') or 'Unknown'}",
                f"Video URL: {metadata.get('video_url') or doc.source_url}",
            ])
        web_results = ""
        if _should_use_live_web(user_message):
            web = WebSearch()
            web_results = web.format_results(web.search(user_message))
        ai = AIAssistant()
        bot_response, page_ref = ai.answer_question(
            user_message, doc.text_content, source_info, web_results)

    ChatMessage.objects.create(
        document=doc, user_message=user_message,
        bot_response=bot_response, page_reference=page_ref,
    )
    return JsonResponse({
        "user_message": user_message,
        "bot_response": bot_response,
        "page_reference": page_ref,
    })


@require_http_methods(["POST"])
def explain_selection(request, doc_id):
    doc = _get_doc_for_request(request, doc_id)
    if doc is None:
        return JsonResponse({"error": "Please log in to use this feature."}, status=403)
    selected_text = request.POST.get("text", "").strip()[:2000]
    if not selected_text:
        return JsonResponse({"error": "No text selected"}, status=400)
    explanation = AIAssistant().explain_text(selected_text, doc.text_content)
    return JsonResponse({"selected_text": selected_text, "explanation": explanation})


@require_http_methods(["POST"])
def create_flashcards(request, doc_id):
    doc = _get_doc_for_request(request, doc_id)
    if doc is None:
        return JsonResponse({"error": "Please log in to use this feature."}, status=403)
    text = request.POST.get("text", doc.text_content)
    count = _bounded_int(request.POST.get("count"), 5, 1, 10)
    page_number = request.POST.get("page") or None

    created = []
    for fc_data in AIAssistant().generate_flashcards(text, count):
        fc = Flashcard.objects.create(
            document=doc, front=fc_data["front"], back=fc_data["back"],
            source_text=text[:500], page_number=page_number,
        )
        created.append({"id": fc.id, "front": fc.front, "back": fc.back})
    return JsonResponse({"flashcards": created, "count": len(created)})


@require_http_methods(["POST"])
def create_mcqs_from_text(request, doc_id):
    doc = _get_doc_for_request(request, doc_id)
    if doc is None:
        return JsonResponse({"error": "Please log in to use this feature."}, status=403)
    text = request.POST.get("text", doc.text_content)
    count = _bounded_int(request.POST.get("count"), 3, 3, 10)
    page_number = request.POST.get("page") or None

    created = []
    for m in AIAssistant().generate_mcqs(text, count):
        mcq = MCQQuestion.objects.create(
            document=doc,
            question=m["question"], option_a=m["option_a"], option_b=m["option_b"],
            option_c=m["option_c"], option_d=m["option_d"],
            correct_answer=m["correct_answer"], explanation=m.get(
                "explanation", ""),
            source_text=text[:500], page_number=page_number,
        )
        created.append({
            "id": mcq.id, "question": mcq.question,
            "options": {"a": mcq.option_a, "b": mcq.option_b, "c": mcq.option_c, "d": mcq.option_d},
            "correct": mcq.correct_answer, "explanation": mcq.explanation,
        })
    return JsonResponse({"mcqs": created, "count": len(created)})


@require_http_methods(["POST"])
def create_short_questions_from_text(request, doc_id):
    doc = _get_doc_for_request(request, doc_id)
    if doc is None:
        return JsonResponse({"error": "Please log in to use this feature."}, status=403)
    text = request.POST.get("text", doc.text_content)
    count = _bounded_int(request.POST.get("count"), 5, 1, 10)
    page_number = request.POST.get("page") or None

    created = []
    for q in AIAssistant().generate_short_questions(text, count):
        sq = ShortQuestion.objects.create(
            document=doc, question=q["question"], answer=q["answer"],
            source_text=text[:500], page_number=page_number,
        )
        created.append(
            {"id": sq.id, "question": sq.question, "answer": sq.answer})
    return JsonResponse({"questions": created, "count": len(created)})


@require_http_methods(["POST"])
def save_highlight(request, doc_id):
    doc = _get_doc_for_request(request, doc_id)
    if doc is None:
        return JsonResponse({"error": "Please log in to use this feature."}, status=403)
    highlight = Highlight.objects.create(
        document=doc,
        text=request.POST.get("text", ""),
        page_number=int(request.POST.get("page", 1)),
        color=request.POST.get("color", "yellow"),
    )
    return JsonResponse({"id": highlight.id, "text": highlight.text, "page": highlight.page_number})


def delete_document(request, doc_id):
    doc = _get_doc_for_request(request, doc_id)
    if doc is None:
        messages.error(request, "Please log in to manage documents.")
        return redirect("login")
    title = doc.title
    doc.delete()
    messages.success(request, f'"{title}" deleted.')
    return redirect("documents:home")


def register(request):
    if request.user.is_authenticated:
        return redirect("documents:home")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user,
                       backend='django.contrib.auth.backends.ModelBackend')
            messages.success(
                request, f"Registration successful. Welcome, {user.username}!")
            return redirect("documents:home")
    else:
        form = CustomUserCreationForm()

    return render(request, "registration/register.html", {"form": form})


# ── Writing Assistant ──────────────────────────────────────────────────────────

def writing_assistant(request):
    """Render the Writing Assistant page."""
    return render(request, "documents/writing_assistant.html")


@require_http_methods(["POST"])
def writing_ai(request):
    """AJAX endpoint: accepts prompt + article text, returns AI response."""
    import json
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    prompt   = (body.get("prompt") or "").strip()
    article  = (body.get("article") or "").strip()
    selected = (body.get("selected") or "").strip()

    if not prompt:
        return JsonResponse({"error": "No prompt provided"}, status=400)

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return JsonResponse({"error": "GROQ_API_KEY not configured"}, status=500)

    from groq import Groq
    client = Groq(api_key=api_key)

    # Build context for the model
    context_parts = []
    if selected:
        context_parts.append(f"Selected text the user is working on:\n\"\"\"\n{selected[:3000]}\n\"\"\"")
    if article:
        context_parts.append(f"Full article so far:\n\"\"\"\n{article[:6000]}\n\"\"\"")
    context = "\n\n".join(context_parts)

    system_prompt = (
        "You are an expert writing assistant embedded in a rich-text editor. "
        "Help the user write, improve, and refine their article. "
        "When asked to fix grammar or rewrite, return ONLY the corrected/rewritten text with no preamble. "
        "When asked to summarise, expand, or suggest ideas, be clear and concise. "
        "Never add meta-commentary like 'Here is the rewritten version:' unless the user asked for an explanation — "
        "just return the result directly."
    )

    user_message = f"{context}\n\nUser request: {prompt}" if context else prompt

    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2048,
            messages=[
                {"role": "system",  "content": system_prompt},
                {"role": "user",    "content": user_message},
            ],
        )
        response_text = resp.choices[0].message.content.strip()
        return JsonResponse({"response": response_text})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
