# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from datetime import date
from datetime import datetime

from aldryn_apphooks_config.mixins import AppConfigMixin
from aldryn_people.models import Person
from dateutil.relativedelta import relativedelta
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponsePermanentRedirect
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import translation
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from menus.utils import set_language_changer
from parler.views import TranslatableSlugMixin
from parler.views import ViewUrlMixin

from aldryn_newsblog.compat import toolbar_edit_mode_active
from aldryn_newsblog.utils.utilities import get_valid_languages_from_request
from .models import Article, ArticleTag
from .models import Category, Author
from .utils import add_prefix_to_path


class TemplatePrefixMixin(object):

    def prefix_template_names(self, template_names):
        if (hasattr(self.config, 'template_prefix') and  # noqa: W504
                self.config.template_prefix):
            prefix = self.config.template_prefix
            return [
                add_prefix_to_path(template, prefix)
                for template in template_names]
        return template_names

    def get_template_names(self):
        template_names = super(TemplatePrefixMixin, self).get_template_names()
        return self.prefix_template_names(template_names)


class EditModeMixin(object):
    """
    A mixin which sets the property 'edit_mode' with the truth value for
    whether a user is logged-into the CMS and is in edit-mode.
    """
    edit_mode = False

    def dispatch(self, request, *args, **kwargs):
        self.edit_mode = (
            self.request.toolbar and toolbar_edit_mode_active(self.request))
        return super(EditModeMixin, self).dispatch(request, *args, **kwargs)


class PreviewModeMixin(EditModeMixin):
    """
    If content editor is logged-in, show all articles. Otherwise, only the
    published articles should be returned.
    """
    def get_queryset(self):
        qs = super(PreviewModeMixin, self).get_queryset()
        # check if user can see unpublished items. this will allow to switch
        # to edit mode instead of 404 on article detail page. CMS handles the
        # permissions.
        user = self.request.user
        user_can_edit = user.is_staff or user.is_superuser
        if not (self.edit_mode or user_can_edit):
            qs = qs.published()
        language = translation.get_language()
        qs = qs.active_translations(language).namespace(self.namespace)
        return qs


class AppHookCheckMixin(object):

    def dispatch(self, request, *args, **kwargs):
        self.valid_languages = get_valid_languages_from_request(
            self.namespace, request)
        return super(AppHookCheckMixin, self).dispatch(
            request, *args, **kwargs)

    def get_queryset(self):
        # filter available objects to contain only resolvable for current
        # language. IMPORTANT: after .translated - we cannot use .filter
        # on translated fields (parler/django limitation).
        # if your mixin contains filtering after super call - please place it
        # after this mixin.
        qs = super(AppHookCheckMixin, self).get_queryset()
        return qs.translated(*self.valid_languages)


class ArticleDetail(AppConfigMixin, AppHookCheckMixin, PreviewModeMixin,
                    TranslatableSlugMixin, TemplatePrefixMixin, DetailView):
    model = Article
    slug_field = 'slug'
    year_url_kwarg = 'year'
    month_url_kwarg = 'month'
    day_url_kwarg = 'day'
    slug_url_kwarg = 'slug'
    pk_url_kwarg = 'pk'

    def get(self, request, *args, **kwargs):
        """
        This handles non-permalinked URLs according to preferences as set in
        NewsBlogConfig.
        """
        if not hasattr(self, 'object'):
            self.object = self.get_object()
        set_language_changer(request, self.object.get_absolute_url)
        url = self.object.get_absolute_url()
        if self.config.non_permalink_handling == 200 or request.path == url:
            # Continue as normal
            return super(ArticleDetail, self).get(request, *args, **kwargs)

        # Check to see if the URL path matches the correct absolute_url of
        # the found object
        if self.config.non_permalink_handling == 302:
            return HttpResponseRedirect(url)
        elif self.config.non_permalink_handling == 301:
            return HttpResponsePermanentRedirect(url)
        else:
            raise Http404('This is not the canonical uri of this object.')

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """
        Supports ALL of the types of permalinks that we've defined in urls.py.
        However, it does require that either the id and the slug is available
        and unique.
        """
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg, None)
        pk = self.kwargs.get(self.pk_url_kwarg, None)

        if pk is not None:
            # Let the DetailView itself handle this one
            return DetailView.get_object(self, queryset=queryset)
        elif slug is not None:
            # Let the TranslatedSlugMixin take over
            return super(ArticleDetail, self).get_object(queryset=queryset)

        raise AttributeError('ArticleDetail view must be called with either '
                             'an object pk or a slug')

    def get_context_data(self, **kwargs):
        context = super(ArticleDetail, self).get_context_data(**kwargs)
        context['prev_article'] = self.get_prev_object(
            self.queryset, self.object)
        context['next_article'] = self.get_next_object(
            self.queryset, self.object)
        return context

    def get_prev_object(self, queryset=None, object=None):
        if queryset is None:
            queryset = self.get_queryset()
        if object is None:
            object = self.get_object(self)
        prev_objs = queryset.filter(
            publishing_date__lt=object.publishing_date
        ).order_by(
            '-publishing_date'
        )[:1]
        if prev_objs:
            return prev_objs[0]
        else:
            return None

    def get_next_object(self, queryset=None, object=None):
        if queryset is None:
            queryset = self.get_queryset()
        if object is None:
            object = self.get_object(self)
        next_objs = queryset.filter(
            publishing_date__gt=object.publishing_date
        ).order_by(
            'publishing_date'
        )[:1]
        if next_objs:
            return next_objs[0]
        else:
            return None


class ArticleListBase(AppConfigMixin, AppHookCheckMixin, TemplatePrefixMixin,
                      PreviewModeMixin, ViewUrlMixin, ListView):
    model = Article
    show_header = False

    def get_paginate_by(self, queryset):
        if self.paginate_by is not None:
            return self.paginate_by
        else:
            try:
                return self.config.paginate_by
            except AttributeError:
                return 10  # sensible failsafe

    def get_pagination_options(self):
        # Django does not handle negative numbers well
        # when using variables.
        # So we perform the conversion here.
        if self.config:
            options = {
                'pages_start': self.config.pagination_pages_start,
                'pages_visible': self.config.pagination_pages_visible,
            }
        else:
            options = {
                'pages_start': 10,
                'pages_visible': 4,
            }

        pages_visible_negative = -options['pages_visible']
        options['pages_visible_negative'] = pages_visible_negative
        options['pages_visible_total'] = options['pages_visible'] + 1
        options['pages_visible_total_negative'] = pages_visible_negative - 1
        return options

    def get_context_data(self, **kwargs):
        context = super(ArticleListBase, self).get_context_data(**kwargs)
        context['pagination'] = self.get_pagination_options()
        return context


class ArticleList(ArticleListBase):
    """A complete list of articles."""
    show_header = True

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super(ArticleList, self).get_queryset()
        # exclude featured articles from queryset, to allow featured article
        # plugin on the list view page without duplicate entries in page qs.
        exclude_count = self.config.exclude_featured
        if exclude_count:
            featured_qs = Article.objects.all().filter(is_featured=True)
            if not self.edit_mode:
                featured_qs = featured_qs.published()
            exclude_featured = list(featured_qs.values_list('pk', flat=True))[:exclude_count]
            qs = qs.exclude(pk__in=exclude_featured)
        return qs


class ArticleSearchResultsList(ArticleListBase):
    model = Article
    http_method_names = ['get', 'post', ]
    partial_name = 'aldryn_newsblog/includes/search_results.html'
    template_name = 'aldryn_newsblog/article_list.html'

    def get(self, request, *args, **kwargs):
        self.query = request.GET.get('q')
        try:
            self.max_articles = int(request.GET.get('max_articles', 0))
        except ValueError:
            self.max_articles = 0
        self.edit_mode = (request.toolbar and toolbar_edit_mode_active(request))
        return super(ArticleSearchResultsList, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_paginate_by(self, queryset):
        """
        If a max_articles was set (by a plugin), use that figure, else,
        paginate by the app_config's settings.
        """
        return self.max_articles or super(
            ArticleSearchResultsList, self).get_paginate_by(self.get_queryset())

    def get_queryset(self):
        qs = super(ArticleSearchResultsList, self).get_queryset()
        if not self.edit_mode:
            qs = qs.published()
        if self.query:
            return qs.filter(
                Q(translations__title__icontains=self.query) |  # noqa: #W504
                Q(translations__lead_in__icontains=self.query) |  # noqa: #W504
                Q(translations__search_data__icontains=self.query)
            ).distinct()
        else:
            return qs.none()

    def get_context_data(self, **kwargs):
        cxt = super(ArticleSearchResultsList, self).get_context_data(**kwargs)
        cxt['query'] = self.query
        return cxt

    def get_template_names(self):
        if self.request.is_ajax:
            template_names = [self.partial_name]
        else:
            template_names = [self.template_name]
        return self.prefix_template_names(template_names)


class AuthorArticleList(ArticleListBase):
    """A list of articles written by a specific author."""
    def get_queryset(self):
        author_override_matches_q = Q(
            author_override__isnull=False, author_override=self.author_override
        )
        author_matches_q = Q(
            author_override__isnull=True,
            author__isnull=False,
            author=self.author
        )
        return super(AuthorArticleList, self).get_queryset().filter(
            author_override_matches_q | author_matches_q
        )

    def get(self, request, author, *args, **kwargs):
        language = translation.get_language_from_request(
            request, check_path=True)
        self.author_override = Author.objects.filter(
            slug=author, app_config=self.config
        ).first()
        self.author = Person.objects.language(language).active_translations(
            language, slug=author).first()
        if not self.author_override and not self.author:
            raise Http404('Author not found')
        return super(AuthorArticleList, self).get(request, *args, **kwargs)

    def post(self, request, author, *args, **kwargs):
        return self.get(request, author, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['newsblog_author'] = self.author_override or self.author
        return super(AuthorArticleList, self).get_context_data(**kwargs)


class CategoryArticleList(ArticleListBase):
    """A list of articles filtered by categories."""
    def get_queryset(self):
        return super(CategoryArticleList, self).get_queryset().filter(
            categories=self.category
        )

    def get(self, request, category, *args, **kwargs):
        self.category = get_object_or_404(
            Category, translations__slug=category)
        return super(CategoryArticleList, self).get(request, *args, **kwargs)

    def post(self, request, category, *args, **kwargs):
        return self.get(request, category, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['newsblog_category'] = self.category
        ctx = super(CategoryArticleList, self).get_context_data(**kwargs)
        ctx['newsblog_category'] = self.category
        return ctx


class TagArticleList(ArticleListBase):
    """A list of articles filtered by tags."""
    def get_queryset(self):
        return super(TagArticleList, self).get_queryset().filter(
            article_tags=self.tag
        )

    def get(self, request, tag, *args, **kwargs):
        self.tag = get_object_or_404(
            ArticleTag, translations__slug=tag, newsblog_config=self.config
        )
        return super(TagArticleList, self).get(request, *args, **kwargs)

    def post(self, request, tag, *args, **kwargs):
        return self.get(request, tag, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['newsblog_tag'] = self.tag
        return super(TagArticleList, self).get_context_data(**kwargs)


class DateRangeArticleList(ArticleListBase):
    """A list of articles for a specific date range"""
    def get_queryset(self):
        return super(DateRangeArticleList, self).get_queryset().filter(
            publishing_date__gte=self.date_from,
            publishing_date__lt=self.date_to
        )

    def _daterange_from_kwargs(self, kwargs):
        raise NotImplementedError('Subclasses of DateRangeArticleList need to'
                                  'implement `_daterange_from_kwargs`.')

    def get(self, request, *args, **kwargs):
        self.date_from, self.date_to = self._daterange_from_kwargs(kwargs)
        return super(DateRangeArticleList, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['newsblog_day'] = (
            int(self.kwargs.get('day')) if 'day' in self.kwargs else None)
        kwargs['newsblog_month'] = (
            int(self.kwargs.get('month')) if 'month' in self.kwargs else None)
        kwargs['newsblog_year'] = (
            int(self.kwargs.get('year')) if 'year' in self.kwargs else None)
        if kwargs['newsblog_year']:
            kwargs['newsblog_archive_date'] = date(
                kwargs['newsblog_year'],
                kwargs['newsblog_month'] or 1,
                kwargs['newsblog_day'] or 1)
        return super(DateRangeArticleList, self).get_context_data(**kwargs)


class YearArticleList(DateRangeArticleList):
    def _daterange_from_kwargs(self, kwargs):
        date_from = datetime(int(kwargs['year']), 1, 1)
        date_to = date_from + relativedelta(years=1)
        return date_from, date_to


class MonthArticleList(DateRangeArticleList):
    def _daterange_from_kwargs(self, kwargs):
        date_from = datetime(int(kwargs['year']), int(kwargs['month']), 1)
        date_to = date_from + relativedelta(months=1)
        return date_from, date_to


class DayArticleList(DateRangeArticleList):
    def _daterange_from_kwargs(self, kwargs):
        date_from = datetime(
            int(kwargs['year']), int(kwargs['month']), int(kwargs['day']))
        date_to = date_from + relativedelta(days=1)
        return date_from, date_to
