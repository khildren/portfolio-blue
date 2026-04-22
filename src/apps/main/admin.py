from django.contrib import admin
from django.utils.html import format_html
from .models import SiteSettings


def _img_preview(url, label='', height=80):
    if not url:
        return '—'
    return format_html(
        '<img src="{}" height="{}" style="border-radius:6px;border:1px solid #ddd;padding:4px;background:#fff"/> '
        '<br><small style="color:#888">{}</small>',
        url, height, label
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    # ── Prevent adding more than one row ──────────────────────────────────────
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    # ── Auto-open the one settings record ────────────────────────────────────
    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.get_solo()
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(
            reverse('admin:main_sitesettings_change', args=[obj.pk])
        )

    readonly_fields = (
        'logo_preview', 'logo_light_preview', 'favicon_preview',
        'about_image_preview', 'about_image2_preview', 'updated_at',
    )

    fieldsets = (
        ('🎨  Branding', {
            'description': (
                '<strong>Start here.</strong> Upload your logos and set your business name. '
                'These appear on every page.'
            ),
            'fields': (
                'site_name', 'tagline',
                ('logo', 'logo_preview'),
                ('logo_light', 'logo_light_preview'),
                ('favicon', 'favicon_preview'),
            ),
        }),
        ('🏠  Homepage — Hero', {
            'description': 'The first thing visitors see when they land on your site.',
            'fields': (
                'hero_label', 'hero_heading', 'hero_video_url',
                'years_experience', 'projects_count',
            ),
        }),
        ('📖  About Your Studio', {
            'description': (
                'Describe your studio. This text appears on the homepage and About page. '
                'Keep it honest and personal — clients read it.'
            ),
            'fields': (
                'about_label', 'about_heading', 'about_text',
                ('about_image', 'about_image_preview'),
                ('about_image2', 'about_image2_preview'),
                'founded_year',
            ),
        }),
        ('🔢  Our Process (3 Steps)', {
            'description': 'Explain how you work in 3 simple steps shown on the homepage.',
            'classes': ('collapse',),
            'fields': (
                'process_1_title', 'process_1_desc',
                'process_2_title', 'process_2_desc',
                'process_3_title', 'process_3_desc',
            ),
        }),
        ('📞  Contact Info', {
            'description': 'Shown on the Contact page and in the footer.',
            'fields': (
                'contact_phone', 'contact_email',
                'contact_address', 'contact_city',
                'map_embed_url',
            ),
        }),
        ('🔀  Pages — Turn On / Off', {
            'description': (
                '<strong>Toggle entire pages on or off.</strong> '
                'Turned-off pages redirect visitors to the homepage. '
                'Nav links for disabled pages are hidden automatically.'
            ),
            'fields': ('page_home', 'page_about', 'page_portfolio', 'page_contact'),
        }),
        ('📐  Homepage Sections — Turn On / Off', {
            'description': 'Control which sections appear on your homepage. Changes take effect immediately.',
            'fields': (
                'section_about', 'section_services', 'section_works',
                'section_video', 'section_testimonials', 'section_blog',
                'section_contact_cta',
            ),
        }),
        ('🔗  Social Media', {
            'description': 'Paste full URLs (e.g. https://instagram.com/yourstudio). Leave blank to hide the icon.',
            'classes': ('collapse',),
            'fields': (
                'social_instagram', 'social_facebook',
                'social_twitter', 'social_linkedin',
                'social_behance', 'social_dribbble',
            ),
        }),
        ('📄  Footer', {
            'classes': ('collapse',),
            'fields': ('footer_tagline', 'copyright_name'),
        }),
        ('ℹ️  Last Saved', {
            'classes': ('collapse',),
            'fields': ('updated_at',),
        }),
    )

    # ── Preview helpers ───────────────────────────────────────────────────────
    def logo_preview(self, obj):
        return _img_preview(
            obj.logo.url if obj.logo else None,
            'Logo (dark background)',
        )
    logo_preview.short_description = 'Preview'

    def logo_light_preview(self, obj):
        return _img_preview(
            obj.logo_light.url if obj.logo_light else None,
            'Logo (light background)',
        )
    logo_light_preview.short_description = 'Preview'

    def favicon_preview(self, obj):
        return _img_preview(
            obj.favicon.url if obj.favicon else None,
            'Favicon', height=32,
        )
    favicon_preview.short_description = 'Preview'

    def about_image_preview(self, obj):
        return _img_preview(
            obj.about_image.url if obj.about_image else None,
            'About image 1',
        )
    about_image_preview.short_description = 'Preview'

    def about_image2_preview(self, obj):
        return _img_preview(
            obj.about_image2.url if obj.about_image2 else None,
            'About image 2',
        )
    about_image2_preview.short_description = 'Preview'
