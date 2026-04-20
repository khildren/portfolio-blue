from django.shortcuts import render
from apps.portfolio.models import Project


def home(request):
    featured = Project.objects.filter(
        is_active=True, is_featured=True
    ).select_related('cover_image')[:6]
    # Fall back to most recent if nothing is featured
    if not featured:
        featured = Project.objects.filter(
            is_active=True
        ).select_related('cover_image')[:6]
    return render(request, 'pages/index.html', {'featured': featured})


def about(request):
    return render(request, 'pages/about.html')


def contact(request):
    return render(request, 'pages/contact.html')
