# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import datetime
from collections import Counter
from django.db import models
from django.db.models import Count
from django.utils.timezone import now

from aldryn_apphooks_config.managers.base import ManagerMixin, QuerySetMixin
from aldryn_people.models import Person
from parler.managers import TranslatableManager, TranslatableQuerySet

from aldryn_newsblog.compat import toolbar_edit_mode_active


class ArticleQuerySet(QuerySetMixin, TranslatableQuerySet):
    def published(self):
        """
        Returns articles that are published AND have a publishing_date that
        has actually passed.
        """
        return self.filter(is_published=True, publishing_date__lte=now())


class RelatedManager(ManagerMixin, TranslatableManager):
    def get_queryset(self):
        qs = ArticleQuerySet(self.model, using=self.db)
        return qs.select_related('featured_image')

    def published(self):
        return self.get_queryset().published()

    def get_months(self, request, namespace):
        """
        Get months and years with articles count for given request and namespace
        string. This means how many articles there are in each month.

        The request is required, because logged-in content managers may get
        different counts.

        Return list of dictionaries ordered by article publishing date of the
        following format:
        [
            {
                'date': date(YEAR, MONTH, ARBITRARY_DAY),
                'num_articles': NUM_ARTICLES
            },
            ...
        ]
        """

        # TODO: check if this limitation still exists in Django 1.6+
        # This is done in a naive way as Django is having tough time while
        # aggregating on date fields
        if (request and hasattr(request, 'toolbar') and  # noqa: #W504
                request.toolbar and toolbar_edit_mode_active(request)):
            articles = self.namespace(namespace)
        else:
            articles = self.published().namespace(namespace)
        dates = articles.values_list('publishing_date', flat=True)
        dates = [(x.year, x.month) for x in dates]
        date_counter = Counter(dates)
        dates = set(dates)
        dates = sorted(dates, reverse=True)
        months = [
            # Use day=3 to make sure timezone won't affect this hacks'
            # month value. There are UTC+14 and UTC-12 timezones!
            {'date': datetime.date(year=year, month=month, day=3),
             'num_articles': date_counter[(year, month)]}
            for year, month in dates]
        return months

    def get_authors(self, namespace):
        """
        Get authors with articles count for given namespace string.

        Return Person queryset annotated with and ordered by 'num_articles'.
        """

        # This methods relies on the fact that Article.app_config.namespace
        # is effectively unique for Article models
        return Person.objects.filter(
            article__app_config__namespace=namespace,
            article__is_published=True).annotate(
                num_articles=models.Count('article')).order_by('-num_articles')

    def get_tags(self, request, namespace):
        """
        Get tags with articles count for given namespace string.

        Return list of Tag objects ordered by custom 'num_articles' attribute.
        """
        from aldryn_newsblog.models import ArticleTag

        if (request and hasattr(request, 'toolbar') and  # noqa: #W504
                request.toolbar and toolbar_edit_mode_active(request)):
            articles = self.namespace(namespace)
        else:
            articles = self.published().namespace(namespace)
        if not articles:
            # return empty iterable early not to perform useless requests
            return []

        article_tags = ArticleTag.objects.annotate(
            article_count=Count(
                'article', filter=Q(article__in=articles)
            )
        ).filter(article_count__gt=0).order_by('-article_count')

        if not request.user.is_superuser:
            article_tags = article_tags.filter(newsblog_config__in=request.user.blog_sections.all())
