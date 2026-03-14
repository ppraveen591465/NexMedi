

# Create your views here.
import os
from django.conf import settings
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .llm import summarize_from_text, summarize_from_file

def index(request):
    return render(request, "index.html")

@csrf_exempt  # quick for hackathon; CSRF token is in template
def summarize(request):
    result = ""
    if request.method == "POST":
        lab_file = request.FILES.get("lab_file")
        lab_text = request.POST.get("lab_text", "")
        mode = request.POST.get("mode", "medical")

        if lab_file:
            # Save uploaded file to disk
            upload_path = os.path.join(settings.MEDIA_ROOT, lab_file.name)
            os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
            with open(upload_path, "wb+") as dest:
                for chunk in lab_file.chunks():
                    dest.write(chunk)

            # Simple MIME detection
            name = lab_file.name.lower()
            if name.endswith(".pdf"):
                mime_type = "application/pdf"
            elif name.endswith(".png"):
                mime_type = "image/png"
            elif name.endswith(".jpg") or name.endswith(".jpeg"):
                mime_type = "image/jpeg"
            else:
                mime_type = "application/octet-stream"

            result = summarize_from_file(upload_path, mime_type, mode)
        else:
            # No file, just text
            result = summarize_from_text(lab_text, mode)

    return render(request, "index.html", {"result": result})
