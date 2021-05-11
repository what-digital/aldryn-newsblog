from aldryn_apphooks_config.admin import BaseAppHookConfig
from aldryn_translation_tools.admin import AllTranslationsMixin
from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.admin.placeholderadmin import PlaceholderAdminMixin
from django.contrib import admin
from django.contrib.admin.filters import RelatedFieldListFilter
from django.forms import forms
from django.utils.translation import ugettext_lazy as _
from parler.admin import TranslatableAdmin
from parler.forms import TranslatableModelForm

from aldryn_newsblog import models
from aldryn_newsblog.cms_appconfig import NewsBlogConfig
from aldryn_newsblog.models import Category
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
            'tags',
            'title',
        ]

    def __init__(self, *args, **kwargs):
        super(ArticleAdminForm, self).__init__(*args, **kwargs)

        qs = models.Article.objects
        if self.instance.app_config_id:
            qs = models.Article.objects.filter(
                app_config=self.instance.app_config)
        elif 'initial' in kwargs and 'app_config' in kwargs['initial']:
            qs = models.Article.objects.filter(
                app_config=kwargs['initial']['app_config'])

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if 'related' in self.fields:
            self.fields['related'].queryset = qs

        # Don't allow app_configs to be added here. The correct way to add an
        # apphook-config is to create an apphook on a cms Page.
        if 'app_config' in self.fields.keys():
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
                'site': request.site
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
                'tags',
                'categories',
                'related',
            )
        }),
    )

    filter_horizontal = [
        'categories',
    ]
    app_config_values = {
        'default_published': 'is_published'
    }
    app_config_selection_title = ''
    app_config_selection_desc = ''

    def get_form(self, request, obj=None, **kwargs):
        self._article_instance = obj if obj else None
        form = super().get_form(request, obj=obj, **kwargs)
        form.request_data = request.GET.copy()
        return form

    def add_view(self, request, *args, **kwargs):
        data = request.GET.copy()
        data['author'] = get_person_by_user_model_instance(user=request.user).pk
        request.GET = data
        return super().add_view(request, *args, **kwargs)

    def save_model(self, request, obj, form, change):
        app_config = self._get_appconfig(request, form)
        if app_config:
            obj.app_config = app_config
        return super().save_model(request, obj, form, change)

    def _get_appconfig(self, request, form):
        app_config_pk = None
        if 'app_config' in form.data.keys():
            app_config_pk = form.data.get('app_config', None)
        elif 'app_config' in request.GET.keys():
            app_config_pk = request.GET.get('app_config', None)

        app_config = None
        if app_config_pk:
            try:
                app_config = NewsBlogConfig.objects.get(pk=app_config_pk)
            except NewsBlogConfig.DoesNotExist:
                pass

        return app_config

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "app_config":
                kwargs["queryset"] = NewsBlogConfig.objects.filter(site=request.site)
        if db_field.name == "author_override":
            self._limit_author_queryset_if_needed(request, kwargs)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def _limit_author_queryset_if_needed(self, request, kwargs):
        app_config_id = self._get_app_config_id(request)
        if app_config_id:
            kwargs["queryset"] = models.Author.objects.filter(app_config_id=app_config_id)

    def _get_app_config_id(self, request):
        if self._article_instance and self._article_instance.app_config:
            return self._article_instance.app_config.id
        elif 'app_config' in request.GET:
            return request.GET['app_config']

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "categories":
            self._limit_categories_queryset_if_needed(request, kwargs)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def _limit_categories_queryset_if_needed(self, request, kwargs):
        app_config_id = self._get_app_config_id(request)
        if app_config_id:
            kwargs['queryset'] = Category.objects.filter(newsblog_config_id=app_config_id)
        else:
            kwargs['queryset'] = Category.objects.filter(newsblog_config__site=request.site)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(app_config__site=request.site)

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
        return qs.filter(site=request.site)

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


class AuthorAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',), }


admin.site.register(models.Author, AuthorAdmin)
