import cms.models.fields
import django.db.models.deletion
import parler.fields
from django.db import migrations
from django.db import models

from aldryn_newsblog.models import NewsBlogConfig


def update_app_configs(apps, schema_editor):
    '''
    We need to loop over all existing NewsBlogConfig instances to initialize added
    'placeholder_feature' and 'placeholder_sidebar' placeholders
    '''
    for app_config in NewsBlogConfig.objects.all():
        app_config.save()


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0022_auto_20180620_1551'),
        ('aldryn_newsblog', '0017_auto_20200422_0003'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='article',
            name='owner',
        ),
        migrations.AddField(
            model_name='newsblogconfig',
            name='placeholder_feature',
            field=cms.models.fields.PlaceholderField(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='aldryn_newsblog_feature', slotname='newsblog_feature', to='cms.Placeholder'),
        ),
        migrations.AddField(
            model_name='newsblogconfig',
            name='placeholder_sidebar',
            field=cms.models.fields.PlaceholderField(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='aldryn_newsblog_sidebar', slotname='newsblog_sidebar', to='cms.Placeholder'),
        ),
        migrations.AlterField(
            model_name='article',
            name='author',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='aldryn_people.Person', verbose_name='author'),
        ),
        migrations.AlterField(
            model_name='articletranslation',
            name='master',
            field=parler.fields.TranslationsForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='aldryn_newsblog.Article'),
        ),
        migrations.AlterField(
            model_name='newsblogconfigtranslation',
            name='master',
            field=parler.fields.TranslationsForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='aldryn_newsblog.NewsBlogConfig'),
        ),
        migrations.RunPython(update_app_configs),
    ]
