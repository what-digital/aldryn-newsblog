from aldryn_newsblog.cms_appconfig import NewsBlogConfig
from django.contrib import admin
from django.utils.translation import ugettext
from django.utils.translation import ugettext_lazy as _
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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "newsblog_config":
                kwargs["queryset"] = NewsBlogConfig.objects.filter(site=request.site)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(newsblog_config__site=request.site)


admin.site.register(Category, CategoryAdmin)
