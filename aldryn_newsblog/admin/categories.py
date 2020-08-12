from django.contrib import admin
from django.utils.translation import ugettext

from parler.admin import TranslatableAdmin

from treebeard.admin import TreeAdmin

from aldryn_newsblog.forms import CategoryAdminForm
from aldryn_newsblog.models import Category


class CategoryAdmin(TranslatableAdmin, TreeAdmin):
    form = CategoryAdminForm

    fieldsets = (
        (None, {
            'fields': (
                'name',
                'slug',
                'newsblog_config',
            )
        }),
        (' ', {
            'fields': (
                '_position',
                '_ref_node_id',
            )
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        FormClass = super(CategoryAdmin, self).get_form(request, obj, **kwargs)
        # Workaround for missing translations on treebeard
        FormClass.base_fields['_position'].label = ugettext('Position')
        FormClass.base_fields['_ref_node_id'].label = ugettext('Relative to')
        return FormClass


admin.site.register(Category, CategoryAdmin)
