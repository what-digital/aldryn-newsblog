# -*- coding: utf-8 -*-

from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import get_language_from_request
from django.utils.translation import ugettext as _
from django.utils import feedgenerator

from aldryn_apphooks_config.utils import get_app_instance

from aldryn_newsblog.models import Category
from aldryn_newsblog.models import Article, ArticleTag
from aldryn_newsblog.utils.utilities import get_valid_languages


class LatestArticlesFeed(Feed):

    def __call__(self, request, *args, **kwargs):
        self.request = request
        self.namespace, self.config = get_app_instance(request)
        language = get_language_from_request(request)
        site_id = getattr(get_current_site(request), 'id', None)
        self.valid_languages = get_valid_languages(
            self.namespace,
            language_code=language,
            site_id=site_id)
        return super(LatestArticlesFeed, self).__call__(
            request, *args, **kwargs)

    def link(self):
        return reverse('{0}:article-list-feed'.format(self.namespace))

    def title(self):
        msgformat = {'site_name': Site.objects.get_current().name}
        return _('Articles on %(site_name)s') % msgformat

    def get_queryset(self):
        qs = Article.objects.published().namespace(self.namespace).translated(
            *self.valid_languages)
        return qs

    def items(self, obj):
        qs = self.get_queryset()
        return qs.order_by('-publishing_date')[:10]

    def item_title(self, item):
        return item.title

    def item_pubdate(self, item):
        return item.publishing_date

    def item_description(self, item):
        return item.lead_in

    def item_author_name(self, item):
        author = item.get_author()
        if author:
            return author.name

    def item_enclosures(self, item):
        if item.featured_image:
            return [
                feedgenerator.Enclosure(
                    self.request.build_absolute_uri(item.featured_image.url),
                    str(item.featured_image.size),
                    self.get_image_content_type(item.featured_image),
                )
            ]

    def get_image_content_type(self, featured_image):
        extension = featured_image.extension
        image_type = 'jpeg' if extension == 'jpg' else extension
        return 'image/{}'.format(image_type)


class TagFeed(LatestArticlesFeed):

    def get_object(self, request, tag):
        return tag

    def items(self, tag_slug):
        tag = get_object_or_404(
            ArticleTag, translations__slug=tag_slug, newsblog_config=self.config
        )
        return self.get_queryset().filter(article_tags=tag)[:10]


class CategoryFeed(LatestArticlesFeed):

    def get_object(self, request, category):
        language = get_language_from_request(request, check_path=True)
        return Category.objects.language(language).translated(
            *self.valid_languages, slug=category).get()

    def items(self, obj):
        return self.get_queryset().filter(categories=obj)[:10]
