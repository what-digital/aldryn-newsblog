# -*- coding: utf-8 -*-

from cms.utils.i18n import get_public_languages
from django.conf import settings
from django.contrib.sitemaps import Sitemap

from ..models import Article


class NewsBlogSitemap(Sitemap):

    changefreq = "never"
    priority = 0.5

    def __init__(self, *args, **kwargs):
        self.namespace = kwargs.pop('namespace', None)
        super(NewsBlogSitemap, self).__init__(*args, **kwargs)

    def items(self):
        site_id = getattr(settings, 'SITE_ID', None)
        languages = get_public_languages(site_id=site_id)
        qs = Article.objects.published().filter(
            translations__language_code__in=languages, app_config__site_id=site_id
        ).distinct()
        if self.namespace is not None:
            qs = qs.filter(app_config__namespace=self.namespace)
        return qs

    def lastmod(self, obj):
        return obj.publishing_date
