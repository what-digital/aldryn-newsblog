from treebeard.forms import movenodeform_factory, MoveNodeForm

from parler.forms import TranslatableModelForm

from aldryn_newsblog.models import Category


class CategoryAdminForm(TranslatableModelForm, MoveNodeForm):
    pass


CategoryAdminForm = movenodeform_factory(Category, form=CategoryAdminForm)
