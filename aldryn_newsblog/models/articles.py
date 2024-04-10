import django.core.validators
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, models
from django.db.models import ManyToManyField, Count, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.encoding import force_text
from django.utils.timezone import now
from django.utils.translation import override, ugettext
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.html import escape

from cms.models import Title
from cms.models.fields import PlaceholderField
from cms.models.pluginmodel import CMSPlugin
from cms.utils.i18n import get_current_language, get_redirect_on_fallback

from aldryn_apphooks_config.fields import AppHookConfigField
from aldryn_people.models import Person
from aldryn_translation_tools.models import (
    TranslatedAutoSlugifyMixin, TranslationHelperMixin,
)
from djangocms_text_ckeditor.fields import HTMLField
from filer.fields.image import FilerImageField
from parler.models import TranslatableModel, TranslatedFields
from sortedm2m.fields import SortedManyToManyField
from taggit.managers import TaggableManager
from taggit.models import Tag

from aldryn_newsblog.compat import toolbar_edit_mode_active
from aldryn_newsblog.utils.utilities import get_valid_languages_from_request

from .categoreis import Category
from aldryn_newsblog.cms_appconfig import NewsBlogConfig
from aldryn_newsblog.managers import RelatedManager
from aldryn_newsblog.utils import get_plugin_index_data, get_request, strip_tags
from aldryn_newsblog.utils.utilities import get_person_by_user_model_instance

if settings.LANGUAGES:
    LANGUAGE_CODES = [language[0] for language in settings.LANGUAGES]
elif settings.LANGUAGE:
    LANGUAGE_CODES = [settings.LANGUAGE]
else:
    raise ImproperlyConfigured(
        'Neither LANGUAGES nor LANGUAGE was found in settings.')


# At startup time, SQL_NOW_FUNC will contain the database-appropriate SQL to
# obtain the CURRENT_TIMESTAMP.
SQL_NOW_FUNC = {
    'mssql': 'GetDate()', 'mysql': 'NOW()', 'postgresql': 'now()',
    'sqlite': 'CURRENT_TIMESTAMP', 'oracle': 'CURRENT_TIMESTAMP'
}[connection.vendor]

SQL_IS_TRUE = {
    'mssql': '== TRUE', 'mysql': '= 1', 'postgresql': 'IS TRUE',
    'sqlite': '== 1', 'oracle': 'IS TRUE'
}[connection.vendor]


class Article(TranslatedAutoSlugifyMixin,
              TranslationHelperMixin,
              TranslatableModel):

    # TranslatedAutoSlugifyMixin options
    slug_source_field_name = 'title'
    slug_default = _('untitled-article')
    # when True, updates the article's search_data field
    # whenever the article is saved or a plugin is saved
    # on the article's content placeholder.
    update_search_on_save = getattr(
        settings,
        'ALDRYN_NEWSBLOG_UPDATE_SEARCH_DATA_ON_SAVE',
        False
    )

    translations = TranslatedFields(
        title=models.CharField(_('title'), max_length=234),
        slug=models.SlugField(
            verbose_name=_('slug'),
            max_length=255,
            db_index=True,
            blank=True,
            help_text=_(
                'Used in the URL. If changed, the URL will change. '
                'Clear it to have it re-created automatically.'),
        ),
        lead_in=HTMLField(
            verbose_name=_('lead'), default='',
            help_text=_(
                'The lead gives the reader the main idea of the story, this '
                'is useful in overviews, lists or as an introduction to your '
                'article.'
            ),
            blank=True,
        ),
        meta_title=models.CharField(
            max_length=255, verbose_name=_('meta title'),
            blank=True, default=''),
        meta_description=models.TextField(
            verbose_name=_('meta description'), blank=True, default=''),
        meta_keywords=models.TextField(
            verbose_name=_('meta keywords'), blank=True, default=''),
        meta={'unique_together': (('language_code', 'slug', ), )},

        search_data=models.TextField(blank=True, editable=False)
    )

    content = PlaceholderField('newsblog_article_content',
                               related_name='newsblog_article_content')
    author = models.ForeignKey(
        Person,
        null=True,
        blank=True,
        verbose_name='Author (Django CMS User)',
        on_delete=models.SET_NULL,
        help_text=_("Only used if AUTHOR is not set.")
    )
    author_override = models.ForeignKey(
        'Author',
        null=True,
        blank=True,
        verbose_name=_('author'),
        on_delete=models.SET_NULL,
    )
    app_config = AppHookConfigField(
        NewsBlogConfig,
        verbose_name=_('Section'),
        help_text='',
    )

    categories = ManyToManyField('aldryn_newsblog.Category',
                                 verbose_name=_('categories'),
                                 blank=True)

    publishing_date = models.DateTimeField(_('publishing date'),
                                           default=now)
    is_published = models.BooleanField(_('is published'), default=False,
                                       db_index=True)
    is_featured = models.BooleanField(_('is featured'), default=False,
                                      db_index=True)
    featured_image = FilerImageField(
        verbose_name=_('featured image'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    tags = TaggableManager(blank=True)

    # Setting "symmetrical" to False since it's a bit unexpected that if you
    # set "B relates to A" you immediately have also "A relates to B". It have
    # to be forced to False because by default it's True if rel.to is "self":
    #
    # https://github.com/django/django/blob/1.8.4/django/db/models/fields/related.py#L2144
    #
    # which in the end causes to add reversed releted-to entry as well:
    #
    # https://github.com/django/django/blob/1.8.4/django/db/models/fields/related.py#L977
    related = SortedManyToManyField(
        'self', verbose_name=_('related articles'), blank=True, symmetrical=False
    )

    article_tags = ManyToManyField(
        'ArticleTag', verbose_name=_('tags'), blank=True
    )

    objects = RelatedManager()

    class Meta:
        ordering = ['-publishing_date']

    @property
    def owner(self):
        return self.author.user

    @owner.setter
    def owner(self, user):
        person = get_person_by_user_model_instance(user)
        self.author = person
        self.save()

    @property
    def published(self):
        """
        Returns True only if the article (is_published == True) AND has a
        published_date that has passed.
        """
        return self.is_published and self.publishing_date <= now()

    @property
    def future(self):
        """
        Returns True if the article is published but is scheduled for a
        future date/time.
        """
        return self.is_published and self.publishing_date > now()

    def get_absolute_url(self, language=None):
        """Returns the url for this Article in the selected permalink format."""
        if not language:
            language = get_current_language()
        kwargs = {}
        permalink_type = self.app_config.permalink_type
        if 'y' in permalink_type:
            kwargs.update(year=self.publishing_date.year)
        if 'm' in permalink_type:
            kwargs.update(month="%02d" % self.publishing_date.month)
        if 'd' in permalink_type:
            kwargs.update(day="%02d" % self.publishing_date.day)
        if 'i' in permalink_type:
            kwargs.update(pk=self.pk)
        if 's' in permalink_type:
            slug, lang = self.known_translation_getter(
                'slug', default=None, language_code=language)
            if slug and lang:
                site_id = getattr(settings, 'SITE_ID', None)
                if get_redirect_on_fallback(language, site_id):
                    language = lang
                kwargs.update(slug=slug)

        if self.app_config and self.app_config.namespace:
            namespace = '{0}:'.format(self.app_config.namespace)
        else:
            namespace = ''

        with override(language):
            return reverse('{0}article-detail'.format(namespace), kwargs=kwargs)

    def get_search_data(self, language=None, request=None):
        """
        Provides an index for use with Haystack, or, for populating
        Article.translations.search_data.
        """
        if not self.pk:
            return ''
        if language is None:
            language = get_current_language()
        if request is None:
            request = get_request(language=language)
        description = self.safe_translation_getter('lead_in', '')
        text_bits = [strip_tags(description)]
        for category in self.categories.all():
            text_bits.append(
                force_text(category.safe_translation_getter('name')))
        for tag in self.article_tags.all():
            text_bits.append(force_text(tag.name))
        if self.content:
            plugins = self.content.cmsplugin_set.filter(language=language)
            for base_plugin in plugins:
                plugin_text_content = ' '.join(
                    get_plugin_index_data(base_plugin, request))
                text_bits.append(plugin_text_content)
        return ' '.join(text_bits)

    def save(self, *args, **kwargs):
        # Update the search index
        if self.update_search_on_save:
            self.search_data = self.get_search_data()

        # slug would be generated by TranslatedAutoSlugifyMixin
        super(Article, self).save(*args, **kwargs)

    def __str__(self):
        try:
            return self.safe_translation_getter('title', any_language=True)
        except ValueError:
            default_language = settings.LANGUAGE_CODE
            return self.safe_translation_getter('title', language_code=default_language, any_language=True)

    def get_author(self):
        return self.author_override or self.author

    def clean(self):
        if not self.author_override and not self.author:
            raise ValidationError(
                _("You must specify either AUTHOR or AUTHOR (DJANGO CMS USER)."),
                code='missing'
            )

    def _slug_exists(self, slug, slug_filter=None, qs=None):
        """
        Overriding TranslatedAutoSlugifyMixin
        _slug_exists method to account for CMS pages slugs.
        """
        return super()._slug_exists(slug, slug_filter, qs) or self.cms_page_exists(slug)

    def cms_page_exists(self, slug):
        return Title.objects.filter(slug=slug, language=get_current_language()).exists()


    def add_tag(self, tag_slug, tag_name=None):
        cleaned_slug = slugify(tag_slug)
        if not cleaned_slug in self.article_tags.all().values_list('translations__slug', flat=True):
            article_tag = ArticleTag.objects.get_or_create(
                translations__slug=cleaned_slug,
                newsblog_config=self.app_config,
                defaults={
                    'slug': cleaned_slug,
                    'name': tag_name or tag_slug,
                    'newsblog_config': self.app_config,
                }
            )[0]
            self.article_tags.add(article_tag)

    def add_tags(self, tags):
        for tag in tags:
            self.add_tag(tag)


class Author(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(
        verbose_name=_('slug'),
        max_length=255,
        db_index=True,
        blank=True,
        help_text=_(
            'Used in the URL. If changed, the URL will change. '
            'Clear it to have it re-created automatically.'),
    )
    function = models.CharField(max_length=255, blank=True, default='')
    visual = FilerImageField(
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
        related_name='author_override'
    )
    app_config = models.ForeignKey(
        NewsBlogConfig,
        verbose_name=_('Apphook configuration'),
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = [
            ['slug', 'app_config']
        ]

    def __str__(self) -> str:
        return self.name


class ArticleTag(TranslatedAutoSlugifyMixin, TranslationHelperMixin, TranslatableModel):
    slug_source_field_name = 'name'

    translations = TranslatedFields(
        name=models.CharField(
            _('name'),
            blank=False,
            default='',
            max_length=255,
        ),
        slug=models.SlugField(
            _('slug'),
            blank=True,
            default='',
            help_text=_('Provide a “slug” or leave blank for an automatically '
                        'generated one.'),
            max_length=255,
        ),
        meta={'unique_together': (('language_code', 'slug', ), )}
    )

    newsblog_config = models.ForeignKey(NewsBlogConfig, on_delete=models.PROTECT)

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')

    def delete(self, **kwargs):
        # INFO: There currently is a bug in parler where it will pass along
        #       'using' as a positional argument, which does not work in
        #       Djangos implementation. So we skip it.
        self.__class__.objects.filter(pk=self.pk).delete(**kwargs)
        from parler.cache import _delete_cached_translations
        _delete_cached_translations(self)
        models.Model.delete(self, **kwargs)

    def __str__(self):
        name = self.safe_translation_getter('name', any_language=True)
        return escape(name)


class PluginEditModeMixin(object):
    def get_edit_mode(self, request):
        """
        Returns True only if an operator is logged-into the CMS and is in
        edit mode.
        """
        return (
            hasattr(request, 'toolbar') and request.toolbar and  # noqa: W504
            toolbar_edit_mode_active(request)
        )


class AdjustableCacheModelMixin(models.Model):
    # NOTE: This field shouldn't even be displayed in the plugin's change form
    # if using django CMS < 3.3.0
    cache_duration = models.PositiveSmallIntegerField(
        default=0,  # not the most sensible, but consistent with older versions
        blank=False,
        help_text=_(
            "The maximum duration (in seconds) that this plugin's content "
            "should be cached.")
    )

    class Meta:
        abstract = True


class NewsBlogCMSPlugin(CMSPlugin):
    """AppHookConfig aware abstract CMSPlugin class for Aldryn Newsblog"""
    # avoid reverse relation name clashes by not adding a related_name
    # to the parent plugin
    cmsplugin_ptr = models.OneToOneField(
        CMSPlugin,
        related_name='+',
        parent_link=True,
        on_delete=models.CASCADE,
    )

    app_config = models.ForeignKey(
        NewsBlogConfig,
        verbose_name=_('Apphook configuration'),
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True

    def copy_relations(self, old_instance):
        self.app_config = old_instance.app_config


class NewsBlogArchivePlugin(PluginEditModeMixin, AdjustableCacheModelMixin,
                            NewsBlogCMSPlugin):
    # NOTE: the PluginEditModeMixin is eventually used in the cmsplugin, not
    # here in the model.
    def __str__(self):
        return ugettext('%s archive') % (self.app_config.get_app_title(), )


class NewsBlogArticleSearchPlugin(NewsBlogCMSPlugin):
    max_articles = models.PositiveIntegerField(
        _('max articles'), default=10,
        validators=[django.core.validators.MinValueValidator(1)],
        help_text=_('The maximum number of found articles display.')
    )

    def __str__(self):
        return ugettext('%s archive') % (self.app_config.get_app_title(), )


class NewsBlogAuthorsPlugin(PluginEditModeMixin, NewsBlogCMSPlugin):
    def get_authors(self, request):
        """
        Returns a list of authors (people who have published an article),
        annotated by the number of articles (article_count) that are visible to
        the current user. If this user is anonymous, then this will be all
        articles that are published and whose publishing_date has passed. If the
        user is a logged-in cms operator, then it will be all articles.
        """

        aldryn_authors = self.get_aldryn_authors(request)
        author_overrides = self.get_author_overrides(request)
        combined_authors = self.combine_authors_without_duplicates(
            aldryn_authors, author_overrides
        )
        return sorted(
            combined_authors, key=lambda x: x.article_count, reverse=True
        )

    def get_aldryn_authors(self, request):
        # The basic subquery (for logged-in content managers in edit mode)
        subquery = """
            SELECT COUNT(*)
            FROM aldryn_newsblog_article
            WHERE
                aldryn_newsblog_article.author_id =
                    aldryn_people_person.id AND
                    aldryn_newsblog_article.author_override_id IS NULL AND
                aldryn_newsblog_article.app_config_id = %d"""

        # For other users, limit subquery to published articles
        user_can_edit = request.user.is_staff or request.user.is_superuser
        if not self.get_edit_mode(request) and not user_can_edit:
            subquery += """ AND
                aldryn_newsblog_article.is_published %s AND
                aldryn_newsblog_article.publishing_date <= %s
            """ % (SQL_IS_TRUE, SQL_NOW_FUNC, )

        # Now, use this subquery in the construction of the main query.
        query = """
            SELECT (%s) as article_count, aldryn_people_person.*
            FROM aldryn_people_person
        """ % (subquery % (self.app_config.pk, ), )

        raw_authors = list(Person.objects.raw(query))
        authors = [author for author in raw_authors if author.article_count]
        return authors

    def get_author_overrides(self, request) -> list:
        user_can_edit = request.user.is_staff or request.user.is_superuser
        if self.get_edit_mode(request) or user_can_edit:
            authors_qs = Author.objects.all()
        else:
            authors_qs = Author.objects.filter(
                article__is_published=True,
                article__publishing_date__lte=now()
            )
        authors_qs = authors_qs.annotate(article_count=Count('article')).filter(
            article_count__gt=0, app_config=self.app_config
        )
        return list(authors_qs)

    @staticmethod
    def combine_authors_without_duplicates(aldryn_authors, author_overrides):
        authors_combined_dict = {
            author.slug: author for author in author_overrides
        }
        for aldryn_author in aldryn_authors:
            if not aldryn_author.slug in authors_combined_dict:
                authors_combined_dict[aldryn_author.slug] = aldryn_author
            else:
                authors_combined_dict[
                    aldryn_author.slug
                ].article_count += aldryn_author.article_count
        return list(authors_combined_dict.values())

    def __str__(self):
        return ugettext('%s authors') % (self.app_config.get_app_title(), )


class NewsBlogCategoriesPlugin(PluginEditModeMixin, NewsBlogCMSPlugin):
    def __str__(self):
        return ugettext('%s categories') % (self.app_config.get_app_title(), )

    def get_categories(self, request):
        """
        Returns a list of categories, annotated by the number of articles
        (article_count) that are visible to the current user. If this user is
        anonymous, then this will be all articles that are published and whose
        publishing_date has passed. If the user is a logged-in cms operator,
        then it will be all articles.
        """

        subquery = """
            SELECT COUNT(*)
            FROM aldryn_newsblog_article, aldryn_newsblog_article_categories
            WHERE
                aldryn_newsblog_article_categories.category_id =
                    aldryn_newsblog_category.id AND
                aldryn_newsblog_article_categories.article_id =
                    aldryn_newsblog_article.id AND
                aldryn_newsblog_article.app_config_id = %d
        """ % (self.app_config.pk, )

        if not self.get_edit_mode(request):
            subquery += """ AND
                aldryn_newsblog_article.is_published %s AND
                aldryn_newsblog_article.publishing_date <= %s
            """ % (SQL_IS_TRUE, SQL_NOW_FUNC, )

        query = """
            SELECT (%s) as article_count, aldryn_newsblog_category.*
            FROM aldryn_newsblog_category
        """ % (subquery, )

        raw_categories = list(Category.objects.raw(query))
        categories = [
            category for category in raw_categories if category.article_count]
        return sorted(categories, key=lambda x: x.article_count, reverse=True)


class NewsBlogFeaturedArticlesPlugin(PluginEditModeMixin, NewsBlogCMSPlugin):
    article_count = models.PositiveIntegerField(
        default=1,
        validators=[django.core.validators.MinValueValidator(1)],
        help_text=_('The maximum number of featured articles display.')
    )

    def get_articles(self, request):
        if not self.article_count:
            return Article.objects.none()
        queryset = Article.objects
        if not self.get_edit_mode(request):
            queryset = queryset.published()
        languages = get_valid_languages_from_request(
            self.app_config.namespace, request)
        if self.language not in languages:
            return queryset.none()
        queryset = queryset.translated(*languages).filter(
            app_config=self.app_config,
            is_featured=True)
        return queryset[:self.article_count]

    def __str__(self):
        if not self.pk:
            return 'featured articles'
        prefix = self.app_config.get_app_title()
        if self.article_count == 1:
            title = ugettext('featured article')
        else:
            title = ugettext('featured articles: %(count)s') % {
                'count': self.article_count,
            }
        return '{0} {1}'.format(prefix, title)


class NewsBlogLatestArticlesPlugin(PluginEditModeMixin,
                                   AdjustableCacheModelMixin,
                                   NewsBlogCMSPlugin):
    latest_articles = models.IntegerField(
        default=5,
        help_text=_('The maximum number of latest articles to display.')
    )
    exclude_featured = models.PositiveSmallIntegerField(
        default=0,
        blank=True,
        help_text=_(
            'The maximum number of featured articles to exclude from display. '
            'E.g. for uses in combination with featured articles plugin.')
    )

    def get_articles(self, request):
        """
        Returns a queryset of the latest N articles. N is the plugin setting:
        latest_articles.
        """
        queryset = Article.objects
        featured_qs = Article.objects.all().filter(is_featured=True)
        if not self.get_edit_mode(request):
            queryset = queryset.published()
            featured_qs = featured_qs.published()
        languages = get_valid_languages_from_request(
            self.app_config.namespace, request)
        if self.language not in languages:
            return queryset.none()
        queryset = queryset.translated(*languages).filter(
            app_config=self.app_config)
        featured_qs = featured_qs.translated(*languages).filter(
            app_config=self.app_config)
        exclude_featured = list(featured_qs.values_list(
            'pk', flat=True))[:self.exclude_featured]
        queryset = queryset.exclude(pk__in=list(exclude_featured))
        return queryset[:self.latest_articles]

    def __str__(self):
        return ugettext('%(app_title)s latest articles: %(latest_articles)s') % {
            'app_title': self.app_config.get_app_title(),
            'latest_articles': self.latest_articles,
        }


class NewsBlogRelatedPlugin(PluginEditModeMixin, AdjustableCacheModelMixin,
                            CMSPlugin):
    # NOTE: This one does NOT subclass NewsBlogCMSPlugin. This is because this
    # plugin can really only be placed on the article detail view in an apphook.
    cmsplugin_ptr = models.OneToOneField(
        CMSPlugin,
        related_name='+',
        parent_link=True,
        on_delete=models.CASCADE,
    )

    def get_articles(self, article, request):
        """
        Returns a queryset of articles that are related to the given article.
        """
        languages = get_valid_languages_from_request(
            article.app_config.namespace, request)
        if self.language not in languages:
            return Article.objects.none()
        qs = article.related.translated(*languages)
        if not self.get_edit_mode(request):
            qs = qs.published()
        return qs

    def __str__(self):
        return ugettext('Related articles')


class NewsBlogTagsPlugin(PluginEditModeMixin, NewsBlogCMSPlugin):

    def get_tags(self, request):
        """
        Returns a queryset of tags, annotated by the number of articles
        (article_count) that are visible to the current user. If this user is
        anonymous, then this will be all articles that are published and whose
        publishing_date has passed. If the user is a logged-in cms operator,
        then it will be all articles.
        """

        return ArticleTag.objects.annotate(
            article_count=Count(
                'article', filter=self.get_article_filter(request)
            )
        ).filter(
            newsblog_config_id=self.app_config.pk, article_count__gt=0
        ).order_by('-article_count')

    def get_article_filter(self, request):
        if not self.get_edit_mode(request):
            article_filter = Q(
                article__is_published=True, article__publishing_date__lte=now()
            )
        else:
            article_filter = Q()
        return article_filter

    def __str__(self):
        return ugettext('%s tags') % (self.app_config.get_app_title(), )


@receiver(post_save, dispatch_uid='article_update_search_data')
def update_search_data(sender, instance, **kwargs):
    """
    Upon detecting changes in a plugin used in an Article's content
    (PlaceholderField), update the article's search_index so that we can
    perform simple searches even without Haystack, etc.
    """
    is_cms_plugin = issubclass(instance.__class__, CMSPlugin)

    if Article.update_search_on_save and is_cms_plugin:
        placeholder = (getattr(instance, '_placeholder_cache', None) or  # noqa: W504
                       instance.placeholder)
        if hasattr(placeholder, '_attached_model_cache'):
            if placeholder._attached_model_cache == Article:
                article = placeholder._attached_model_cache.objects.language(
                    instance.language).get(content=placeholder.pk)
                article.search_data = article.get_search_data(instance.language)
                article.save()
