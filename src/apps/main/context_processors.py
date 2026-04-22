from .models import SiteSettings


def site_settings(request):
    return {'ss': SiteSettings.get_solo()}
