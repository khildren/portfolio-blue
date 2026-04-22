from django.db import models


class SiteSettings(models.Model):
    # ── Branding ──────────────────────────────────────────────────────────────
    site_name = models.CharField(
        max_length=100, default='Blue Solutions',
        help_text='Your business name — shows in browser tab and footer.')
    tagline = models.CharField(
        max_length=200, default='Architecture & Interior Design',
        help_text='Short description under your logo.')
    logo = models.ImageField(
        upload_to='site/', blank=True, null=True,
        help_text='Logo for dark backgrounds (white/light version). PNG with transparency works best.')
    logo_light = models.ImageField(
        upload_to='site/', blank=True, null=True,
        help_text='Logo for light/white backgrounds (dark version).')
    favicon = models.ImageField(
        upload_to='site/', blank=True, null=True,
        help_text='Tiny icon shown in browser tabs. Should be square, at least 32×32px.')

    # ── Homepage Hero ─────────────────────────────────────────────────────────
    hero_label = models.CharField(
        max_length=100, default='OUR WORKS',
        help_text='Small label above the main headline on the homepage.')
    hero_heading = models.CharField(
        max_length=200, default='AWESOME DESIGNS',
        help_text='Big headline on the homepage hero.')
    hero_video_url = models.URLField(
        blank=True, default='https://vimeo.com/175353205',
        help_text='Vimeo or YouTube link for the homepage background video.')
    years_experience = models.PositiveSmallIntegerField(
        default=25,
        help_text='Number shown in the "Years of Experience" counter.')
    projects_count = models.PositiveSmallIntegerField(
        default=50,
        help_text='Number shown in the "Projects Completed" counter.')

    # ── About Section ─────────────────────────────────────────────────────────
    about_label = models.CharField(
        max_length=100, default='About Studio',
        help_text='Small label above the about heading.')
    about_heading = models.CharField(
        max_length=200, default='Welcome! We are an architecture studio',
        help_text='Main heading in the About section.')
    about_text = models.TextField(
        blank=True,
        help_text='Paragraph describing your studio. Shown on homepage and About page.')
    about_image = models.ImageField(
        upload_to='site/', blank=True, null=True,
        help_text='Primary about/studio photo.')
    about_image2 = models.ImageField(
        upload_to='site/', blank=True, null=True,
        help_text='Secondary about/studio photo (shown alongside the first).')
    founded_year = models.PositiveSmallIntegerField(
        default=2000,
        help_text='Year your studio was founded.')

    # ── Process Steps ─────────────────────────────────────────────────────────
    process_1_title = models.CharField(max_length=100, default='Idea & Start')
    process_1_desc = models.TextField(blank=True, default='We listen to your vision and define the project goals.')
    process_2_title = models.CharField(max_length=100, default='Design & Create')
    process_2_desc = models.TextField(blank=True, default='Our team drafts concepts and refines them with your feedback.')
    process_3_title = models.CharField(max_length=100, default='Build & Finish')
    process_3_desc = models.TextField(blank=True, default='We bring the design to life with precision and care.')

    # ── Contact Info ──────────────────────────────────────────────────────────
    contact_phone = models.CharField(
        max_length=50, blank=True,
        help_text='Phone number shown on contact page and footer.')
    contact_email = models.EmailField(
        blank=True,
        help_text='Email address for the contact form destination and display.')
    contact_address = models.CharField(
        max_length=200, blank=True,
        help_text='Street address.')
    contact_city = models.CharField(
        max_length=100, blank=True,
        help_text='City, State ZIP — shown below address.')
    map_embed_url = models.URLField(
        blank=True,
        help_text=(
            'Google Maps embed URL. Go to maps.google.com → find your location '
            '→ Share → Embed a map → copy the src="..." URL.'
        ))

    # ── Social Media ──────────────────────────────────────────────────────────
    social_instagram = models.URLField(blank=True, help_text='Full URL e.g. https://instagram.com/yourstudio')
    social_facebook = models.URLField(blank=True, help_text='Full URL e.g. https://facebook.com/yourstudio')
    social_twitter = models.URLField(blank=True, help_text='Full URL e.g. https://twitter.com/yourstudio')
    social_linkedin = models.URLField(blank=True, help_text='Full URL e.g. https://linkedin.com/company/yourstudio')
    social_behance = models.URLField(blank=True, help_text='Full URL e.g. https://behance.net/yourstudio')
    social_dribbble = models.URLField(blank=True, help_text='Full URL e.g. https://dribbble.com/yourstudio')

    # ── Pages On/Off ─────────────────────────────────────────────────────────
    page_home = models.BooleanField(
        default=True, help_text='Show the homepage (/) with hero slider and featured projects.')
    page_about = models.BooleanField(
        default=True, help_text='Show the About page (/about/).')
    page_portfolio = models.BooleanField(
        default=True, help_text='Show the Portfolio page (/portfolio/).')
    page_contact = models.BooleanField(
        default=True, help_text='Show the Contact page (/contact/).')

    # ── Homepage Sections On/Off ──────────────────────────────────────────────
    section_about = models.BooleanField(
        default=True, help_text='Show the About Studio section on the homepage.')
    section_services = models.BooleanField(
        default=True, help_text='Show the Services/Features strip on the homepage.')
    section_works = models.BooleanField(
        default=True, help_text='Show the Our Works project slider on the homepage.')
    section_video = models.BooleanField(
        default=True, help_text='Show the video/awards block on the homepage.')
    section_testimonials = models.BooleanField(
        default=True, help_text='Show the client testimonials carousel on the homepage.')
    section_blog = models.BooleanField(
        default=False, help_text='Show the Latest News/Blog section on the homepage.')
    section_contact_cta = models.BooleanField(
        default=True, help_text='Show the "Let\'s Talk" contact call-to-action at the bottom of the homepage.')

    # ── Footer ────────────────────────────────────────────────────────────────
    footer_tagline = models.CharField(
        max_length=200, blank=True,
        help_text='Short line shown in the footer under your logo.')
    copyright_name = models.CharField(
        max_length=100, default='Blue Solutions',
        help_text='Name used in the footer copyright line.')

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.site_name

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
