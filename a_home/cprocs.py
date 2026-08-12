from django.conf import settings

def project_title(request):
    return {
        'Chat Application': settings.PROJECT_TITLE
    }