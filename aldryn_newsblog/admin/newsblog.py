from aldryn_apphooks_config.admin import BaseAppHookConfig
from aldryn_translation_tools.admin import AllTranslationsMixin
from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.admin.placeholderadmin import PlaceholderAdminMixin
from django.contrib import admin
from django.contrib.admin.filters import RelatedFieldListFilter
from django.forms import forms
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import PermissionDenied
from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm

from aldryn_newsblog import models
from aldryn_newsblog.cms_appconfig import NewsBlogConfig
from aldryn_newsblog.models import Article, ArticleTag, Category
from aldryn_newsblog.utils.utilities import get_person_by_user_model_instance


def make_published(modeladmin, request, queryset):
    queryset.update(is_published=True)


make_published.short_description = _(
    "Mark selected articles as published")


def make_unpublished(modeladmin, request, queryset):
    queryset.update(is_published=False)


make_unpublished.short_description = _(
    "Mark selected articles as not published")


def make_featured(modeladmin, request, queryset):
    queryset.update(is_featured=True)


make_featured.short_description = _(
    "Mark selected articles as featured")


def make_not_featured(modeladmin, request, queryset):
    queryset.update(is_featured=False)


make_not_featured.short_description = _(
    "Mark selected articles as not featured")


class ArticleAdminForm(TranslatableModelForm):

    class Meta:
        model = models.Article
        fields = [
            'app_config',
            'categories',
            'featured_image',
            'is_featured',
            'is_published',
            'lead_in',
            'meta_description',
            'meta_keywords',
            'meta_title',
            'related',
            'slug',
            'article_tags',
            'title',
        ]

    def __init__(self, *args, **kwargs):
        super(ArticleAdminForm, self).__init__(*args, **kwargs)

        related_qs = models.Article.objects
        if self.instance.app_config_id:
            related_qs = models.Article.objects.filter(
                app_config=self.instance.app_config)
        elif 'initial' in kwargs and 'app_config' in kwargs['initial']:
            related_qs = models.Article.objects.filter(
                app_config=kwargs['initial']['app_config'])

        if self.instance.pk:
            related_qs = related_qs.exclude(pk=self.instance.pk)

        if 'related' in self.fields:
            self.fields['related'].queryset = related_qs

        if 'app_config' in self.fields:
            # Don't allow app_configs to be added here. The correct way to add an
            # apphook-config is to create an apphook on a cms Page.
            self.fields['app_config'].widget.can_add_related = False
        # Don't allow related articles to be added here.
        # doesn't makes much sense to add articles from another article other
        # than save and add another.
        if ('related' in self.fields and  # noqa: W504
            hasattr(self.fields['related'], 'widget')):
            self.fields['related'].widget.can_add_related = False

    def clean(self):
        _is_app_config_in_request = 'app_config' in self.request_data.keys()
        _is_app_config_in_form = 'app_config' in self.data.keys()
        if not _is_app_config_in_request and not _is_app_config_in_form:
            raise forms.ValidationError("App Config is required")


class NewsBlogConfigFilter(RelatedFieldListFilter):

    def field_choices(self, field, request, model_admin):
        if request.user.is_superuser:
            return super().field_choices(field, request, model_admin)

        choices = field.get_choices(
            include_blank=True,
            limit_choices_to={
                'pk__in': request.user.blog_sections.all().values_list('pk', flat=True),
                'site': request.site,
            }
        )
        return choices


class ArticleAdmin(
    AllTranslationsMixin,
    PlaceholderAdminMixin,
    FrontendEditableAdminMixin,
    TranslatableAdmin
):
    form = ArticleAdminForm
    list_display = ('title', 'app_config', 'slug', 'is_featured',
                    'is_published')
    list_filter = [
        ('app_config', NewsBlogConfigFilter),
        'categories',
    ]
    actions = (
        make_featured, make_not_featured,
        make_published, make_unpublished,
    )
    fieldsets = (
        (None, {
            'fields': (
                'title',
                'author_override',
                'author',
                'publishing_date',
                'is_published',
                'is_featured',
                'featured_image',
                'lead_in',
            )
        }),
        (_('Meta Options'), {
            'classes': ('collapse',),
            'fields': (
                'slug',
                'meta_title',
                'meta_description',
                'meta_keywords',
            )
        }),
        (_('Advanced Settings'), {
            'classes': ('collapse',),
            'fields': (
                'article_tags',
                'categories',
                'related',
            )
        }),
    )

    filter_horizontal = [
        'categories', 'article_tags'
    ]
    app_config_values = {
        'default_published': 'is_published'
    }
    app_config_selection_title = ''
    app_config_selection_desc = ''

    def save_model(self, request, obj, form, change):
        app_config = self._get_appconfig_from_form_or_request(request, form)
        if app_config:
            obj.app_config = app_config
        return super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        self._article_instance = obj if obj else None
        if self._article_instance:
            self._article_instance.app_config = NewsBlogConfig.objects.get(id= self._get_appconfig_id(request))
        form = super().get_form(request, obj=obj, **kwargs)
        form.request_data = request.GET.copy()
        form._request = request
        return form

    def _get_appconfig_from_form_or_request(self, request, form):
        if 'app_config' in form.data.keys():
            app_config_id = form.data.get('app_config', None)
        else:
            app_config_id = self._get_appconfig_id(request)
        return NewsBlogConfig.objects.get(id=app_config_id)

    def _get_appconfig_id(self, request):
        if 'app_config' in request.GET:
            if request.user.is_superuser or request.user.blog_sections.filter(id=request.GET['app_config']).exists():
                return request.GET['app_config']
        elif self._article_instance and self._article_instance.app_config:
            return self._article_instance.app_config.id
        else:
            app_config = request.user.blog_sections.order_by('id').first()
            if not app_config and request.user.is_superuser:
                app_config = NewsBlogConfig.objects.filter(site=request.site).order_by('id').first()
            if app_config:
                return app_config.id
        raise PermissionDenied()

    def add_view(self, request, *args, **kwargs):
        data = request.GET.copy()
        data['author'] = get_person_by_user_model_instance(user=request.user).pk
        request.GET = data
        return super().add_view(request, *args, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "app_config":
            if request.user.is_superuser:
                qs = NewsBlogConfig.objects.filter(site=request.site)
            else:
                qs = request.user.blog_sections.filter(site=request.site)
            kwargs["queryset"] = qs
            kwargs["initial"] = NewsBlogConfig.objects.get(id=self._get_appconfig_id(request))
        if db_field.name == "author_override":
            self._limit_author_queryset(request, kwargs)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def _limit_author_queryset(self, request, kwargs):
        app_config_id = self._get_appconfig_id(request)
        kwargs["queryset"] = models.Author.objects.filter(app_config_id=app_config_id)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "categories":
            self._limit_categories_queryset(request, kwargs)
        elif db_field.name == "article_tags":
            self._limit_article_tags_queryset(request, kwargs)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def _limit_categories_queryset(self, request, kwargs):
        app_config_id = self._get_appconfig_id(request)
        kwargs['queryset'] = Category.objects.filter(newsblog_config_id=app_config_id)

    def _limit_article_tags_queryset(self, request, kwargs):
        app_config_id = self._get_appconfig_id(request)
        kwargs['queryset'] = ArticleTag.objects.filter(newsblog_config_id=app_config_id)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(app_config__in=request.user.blog_sections.all())

    def get_fieldsets(self, request, obj):
        fieldsets = list(super().get_fieldsets(request, obj))
        adding_from_toolbar = request.GET.get('adding_from_toolbar', None)
        if not adding_from_toolbar:
            fieldsets.append(
                (_('App Config'), {'classes': ('collapse',), 'fields': ('app_config',)})
            )
        return fieldsets


admin.site.register(models.Article, ArticleAdmin)


class NewsBlogConfigAdmin(
    AllTranslationsMixin,
    PlaceholderAdminMixin,
    BaseAppHookConfig,
    TranslatableAdmin
):
    def get_config_fields(self):
        return (
            'app_title', 'permalink_type', 'non_permalink_handling',
            'template_prefix', 'paginate_by', 'pagination_pages_start',
            'pagination_pages_visible', 'exclude_featured',
            'create_authors', 'search_indexed', 'config.default_published'
        )

    def get_fieldsets(self, request, obj):
        fieldsets = list(super().get_fieldsets(request, obj))
        if request.user.is_superuser:
            fieldsets.append((_('Site'), {'fields': ('site',)}))
        return fieldsets

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(site=request.site, pk__in=request.user.blog_sections.all().values_list('pk', flat=True))

    def save_model(self, request, obj, form, change):
        if not request.POST.get('site', None):
            obj.site = request.site
        return super().save_model(request, obj, form, change)

    def add_view(self, request, *args, **kwargs):
        if request.user.is_superuser:
            data = request.GET.copy()
            data['site'] = request.site.pk
            request.GET = data
        return super().add_view(request, *args, **kwargs)


admin.site.register(NewsBlogConfig, NewsBlogConfigAdmin)


class BlogSectionInline(admin.TabularInline):
    model = NewsBlogConfig.users.through
    extra = 1


class BlogUserAdminBase:
    """
    To be inherited in a model extending the user admin
    """
    inlines = (BlogSectionInline,)


class AuthorAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',), }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(app_config__site=request.site, app_config__in=request.user.blog_sections.all())

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "app_config":
            if request.user.is_superuser:
                qs = NewsBlogConfig.objects.filter(site=request.site)
            else:
                qs = request.user.blog_sections.filter(site=request.site)
            kwargs["queryset"] = qs
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ArticleTagAdmin(TranslatableAdmin):
    list_display = ('name', 'newsblog_config',)
    fieldsets = (
        (None, {
            'fields': (
                'name',
                'slug',
                'newsblog_config',
            )
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "newsblog_config":
            if request.user.is_superuser:
                qs = NewsBlogConfig.objects.filter(site=request.site)
            else:
                qs = request.user.blog_sections.filter(site=request.site)
            kwargs["queryset"] = qs
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(newsblog_config__in=request.user.blog_sections.all(), newsblog__site=request.site)


admin.site.register(models.Author, AuthorAdmin)
admin.site.register(models.ArticleTag, ArticleTagAdmin)
