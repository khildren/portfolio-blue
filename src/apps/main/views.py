from django.shortcuts import render, redirect
from apps.portfolio.models import Project
from .models import SiteSettings


def _settings():
    return SiteSettings.get_solo()


def home(request):
    ss = _settings()
    if not ss.page_home:
        return redirect('portfolio:project_list')
    featured = Project.objects.filter(
        is_active=True, is_featured=True
    ).select_related('cover_image')[:6]
    if not featured:
        featured = Project.objects.filter(is_active=True).select_related('cover_image')[:6]
    return render(request, 'pages/index.html', {'featured': featured})


def about(request):
    ss = _settings()
    if not ss.page_about:
        return redirect('main:home')
    return render(request, 'pages/about.html')


def contact(request):
    ss = _settings()
    if not ss.page_contact:
        return redirect('main:home')
    return render(request, 'pages/contact.html')
