from django.shortcuts import get_object_or_404, render
from .models import Project


def project_list(request):
    projects = Project.objects.filter(is_active=True).select_related('cover_image')
    categories = sorted(set(
        p.category for p in projects if p.category
    ))
    return render(request, 'pages/work.html', {
        'projects': projects,
        'categories': categories,
    })


def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug, is_active=True)
    images = project.images.all()
    related = Project.objects.filter(
        is_active=True, category=project.category
    ).exclude(pk=project.pk).select_related('cover_image')[:3]
    return render(request, 'pages/project.html', {
        'project': project,
        'images': images,
        'related': related,
    })
