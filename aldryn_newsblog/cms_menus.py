# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.urls import NoReverseMatch, reverse
from django.utils.translation import get_language_from_request, override
from django.utils.translation import ugettext_lazy as _

from cms.apphook_pool import apphook_pool
from cms.menu_bases import CMSAttachMenu
from menus.base import NavigationNode
from menus.menu_pool import menu_pool

from aldryn_newsblog.compat import toolbar_edit_mode_active

from .models.articles import Article, ArticleTranslation


class NewsBlogMenu(CMSAttachMenu):
    name = _('Aldryn NewsBlog Menu')

    def get_queryset(self, request):
        """Returns base queryset with support for preview-mode."""
        queryset = Article.objects
        if not (request.toolbar and toolbar_edit_mode_active(request)):
            queryset = queryset.published()
        return queryset

    def get_nodes(self, request):
        nodes = []
        language = get_language_from_request(request, check_path=True)
        articles = self.get_queryset(request).active_translations(language)

        if hasattr(self, 'instance') and self.instance:
            app = apphook_pool.get_apphook(self.instance.application_urls)

        if app:
            config = app.get_config(self.instance.application_namespace)

            if config:
                articles = articles.filter(app_config=config)
        else:
            config = None

        translations_qs = ArticleTranslation.objects.filter(master__in=articles, language_code=language).all()
        translations = {}
        for trans in translations_qs:
            translations[trans.master_id] = trans

        for article in articles:
            if config is None:
                config = article.app_config

            trans = translations[article.pk]

            try:
                url = get_absolute_url(config, article, trans, language)
            except NoReverseMatch:
                url = None

            if url:
                node = NavigationNode(trans.title, url, article.pk)
                nodes.append(node)
        return nodes


# Copy of .models.articles.Article#get_absolute_url()
def get_absolute_url(config, article, trans, language):
    kwargs = {}
    permalink_type = config.permalink_type
    if 'y' in permalink_type:
        kwargs.update(year=article.publishing_date.year)
    if 'm' in permalink_type:
        kwargs.update(month="%02d" % article.publishing_date.month)
    if 'd' in permalink_type:
        kwargs.update(day="%02d" % article.publishing_date.day)
    if 'i' in permalink_type:
        kwargs.update(pk=article.pk)
    if 's' in permalink_type:
        kwargs.update(slug=trans.slug)
    if config.namespace:
        namespace = '{0}:'.format(config.namespace)
    else:
        namespace = ''

    with override(language):
        return reverse('{0}article-detail'.format(namespace), kwargs=kwargs)


menu_pool.register_menu(NewsBlogMenu)
