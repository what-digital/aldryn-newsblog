from aldryn_client import forms


class Form(forms.BaseForm):

    def to_settings(self, data, settings):
        # from functools import partial
        # from aldryn_addons.utils import boolean_ish, djsenv
        # env = partial(djsenv, settings=settings)

        settings['INSTALLED_APPS'].extend([
            'aldryn_apphooks_config',
            'aldryn_boilerplates',
            'aldryn_common',
            'aldryn_newsblog',
            'aldryn_people',
            'aldryn_translation_tools',
            'easy_thumbnails',
            'filer',
            'sortedm2m',
            'taggit',
            'treebeard',
            # fix for https://github.com/what-digital/aldryn-newsblog/issues/7
            'aldryn_categories',
        ])
        return settings
