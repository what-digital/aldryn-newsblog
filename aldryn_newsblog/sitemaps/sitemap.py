# -*- coding: utf-8 -*-

from cms.utils import get_current_site
from cms.utils.i18n import get_public_languages
from django.contrib.sitemaps import Sitemap

from ..models import Article


class NewsBlogSitemap(Sitemap):

    changefreq = "never"
    priority = 0.5

    def __init__(self, *args, **kwargs):
        self.namespace = kwargs.pop('namespace', None)
        super(NewsBlogSitemap, self).__init__(*args, **kwargs)

    def items(self):
        site = get_current_site()
        languages = get_public_languages(site_id=site.pk)
        qs = Article.objects.published().filter(translations__language_code__in=languages).distinct()
        if self.namespace is not None:
            qs = qs.filter(app_config__namespace=self.namespace)
        return qs

    def lastmod(self, obj):
        return obj.publishing_date
