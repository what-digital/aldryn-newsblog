# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from cms.api import add_plugin
from cms.utils import permissions
from cms.wizards.forms import BaseFormMixin
from cms.wizards.wizard_base import Wizard
from cms.wizards.wizard_pool import wizard_pool

from djangocms_text_ckeditor.html import clean_html
from djangocms_text_ckeditor.widgets import TextEditorWidget
from parler.forms import TranslatableModelForm

from .cms_appconfig import NewsBlogConfig
from .models import Article
from .utils.utilities import get_person_by_user_model_instance
from .utils.utilities import is_valid_namespace
from .models import Category


def get_published_app_configs():
    """
    Returns a list of app_configs that are attached to a published page.
    """
    published_configs = []
    for config in NewsBlogConfig.objects.iterator():
        # We don't want to let people try to create Articles here, as
        # they'll just 404 on arrival because the apphook isn't active.
        if is_valid_namespace(config.namespace):
            published_configs.append(config)
    return published_configs


class NewsBlogArticleWizard(Wizard):

    def user_has_add_permission(self, user, **kwargs):
        """
        Return True if the current user has permission to add an article.
        :param user: The current user
        :param kwargs: Ignored here
        :return: True if user has add permission, else False
        """
        # No one can create an Article, if there is no app_config yet.
        app_configs = get_published_app_configs()
        if not app_configs:
            return False

        # Ensure user has permission to create articles.
        app_config_ids = [app_config.id for app_config in app_configs]
        if user.is_superuser or user.has_perm("aldryn_newsblog.add_article") and user.blog_sections.filter(
            pk__in=app_config_ids
        ).exists():
            return True

        # By default, no permission.
        return False


class CreateNewsBlogArticleForm(BaseFormMixin, TranslatableModelForm):
    """
    The ModelForm for the NewsBlog article wizard. Note that Article has a
    number of translated fields that we need to access, so, we use
    TranslatableModelForm
    """

    content = forms.CharField(
        label=_('Content'),
        required=False,
        widget=TextEditorWidget,
        help_text=_(
            "Optional. If provided, it will be added to the main body of "
            "the article as a text plugin, that can be formatted."
        )
    )

    class Meta:
        model = Article
        fields = ['title', 'app_config']
        # The natural widget for app_config is meant for normal Admin views and
        # contains JS to refresh the page on change. This is not wanted here.
        widgets = {'app_config': forms.Select()}

    def __init__(self, **kwargs):
        super(CreateNewsBlogArticleForm, self).__init__(**kwargs)

        # If there's only 1 (or zero) app_configs, don't bother show the
        # app_config choice field, we'll choose the option for the user.
        app_configs = get_published_app_configs()
        if len(app_configs) < 2:
            self.fields['app_config'].widget = forms.HiddenInput()
            self.fields['app_config'].initial = app_configs[0].pk
        self.instance.author = get_person_by_user_model_instance(user=self.user)

    def save(self, commit=True):
        article = super(CreateNewsBlogArticleForm, self).save()

        # If 'content' field has value, create a TextPlugin with same and add it to the PlaceholderField
        content = clean_html(self.cleaned_data.get('content', ''), False)
        if content and permissions.has_plugin_permission(self.user, 'TextPlugin', 'add'):
            add_plugin(
                placeholder=article.content,
                plugin_type='TextPlugin',
                language=self.language_code,
                body=content,
            )

        return article


newsblog_article_wizard = NewsBlogArticleWizard(
    title=_(u"New news/blog article"),
    weight=200,
    form=CreateNewsBlogArticleForm,
    description=_(u"Create a new news/blog article.")
)

wizard_pool.register(newsblog_article_wizard)


class CategoryWizard(Wizard):

    def user_has_add_permission(self, user, **kwargs):
        """
        Return True if the current user has permission to add a category.
        :param user: The current user
        :param kwargs: Ignored here
        :return: True if user has add permission, else False
        """
        # No one can create an Article, if there is no app_config yet.
        app_configs = get_published_app_configs()
        if not app_configs:
            return False

        # Ensure user has permission to create articles.
        app_config_ids = [app_config.id for app_config in app_configs]
        if user.is_superuser or user.has_perm("aldryn_newsblog.add_category") and user.blog_sections.filter(
            pk__in=app_config_ids
        ).exists():
            return True

        # By default, no permission.
        return False

    def get_success_url(self, *args, **kwargs):
        # Since categories do not have their own urls, return None so that
        # cms knows that it should just close the wizard window (reload
        # current page)
        return None


class CreateCategoryForm(BaseFormMixin, TranslatableModelForm):
    """
    The model form for Category wizard.
    """

    class Meta:
        model = Category
        fields = ['name', 'slug', ]


aldryn_category_wizard = CategoryWizard(
    title=_('New category'),
    weight=290,
    form=CreateCategoryForm,
    description=_('Create a new category.')
)

wizard_pool.register(aldryn_category_wizard)
