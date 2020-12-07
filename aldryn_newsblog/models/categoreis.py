from django.db import models
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from aldryn_translation_tools.models import (
    TranslatedAutoSlugifyMixin, TranslationHelperMixin)
from parler import appsettings
from parler.models import TranslatableModel, TranslatedFields
from aldryn_newsblog.cms_appconfig import NewsBlogConfig

LANGUAGE_CODES = appsettings.PARLER_LANGUAGES.get_active_choices()


class Category(TranslatedAutoSlugifyMixin, TranslationHelperMixin, TranslatableModel):
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
        verbose_name = _('category')
        verbose_name_plural = _('categories')

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
