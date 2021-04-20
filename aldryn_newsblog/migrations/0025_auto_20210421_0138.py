# Generated by Django 2.2.17 on 2021-04-20 23:38

import aldryn_apphooks_config.fields
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import djangocms_text_ckeditor.fields
import filer.fields.image
import sortedm2m.fields
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.FILER_IMAGE_MODEL),
        ('aldryn_newsblog', '0024_auto_20210203_1905'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'verbose_name': 'Kategorie', 'verbose_name_plural': 'Kategorien'},
        ),
        migrations.AlterModelOptions(
            name='categorytranslation',
            options={'default_permissions': (), 'managed': True, 'verbose_name': 'Kategorie Translation'},
        ),
        migrations.AlterField(
            model_name='article',
            name='app_config',
            field=aldryn_apphooks_config.fields.AppHookConfigField(help_text='Das Formular wird neu geladen wenn ein neuer Wert ausgewählt wurde', on_delete=django.db.models.deletion.CASCADE, to='aldryn_newsblog.NewsBlogConfig', verbose_name='Section'),
        ),
        migrations.AlterField(
            model_name='article',
            name='author',
            field=models.ForeignKey(blank=True, help_text='Only used if AUTHOR is not set.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='aldryn_people.Person', verbose_name='Author (Django CMS User)'),
        ),
        migrations.AlterField(
            model_name='article',
            name='featured_image',
            field=filer.fields.image.FilerImageField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.FILER_IMAGE_MODEL, verbose_name='Hauptbild'),
        ),
        migrations.AlterField(
            model_name='article',
            name='is_featured',
            field=models.BooleanField(db_index=True, default=False, verbose_name='Ist featured'),
        ),
        migrations.AlterField(
            model_name='article',
            name='is_published',
            field=models.BooleanField(db_index=True, default=False, verbose_name='veröffentlicht'),
        ),
        migrations.AlterField(
            model_name='article',
            name='publishing_date',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Veröffentlichungsdatum'),
        ),
        migrations.AlterField(
            model_name='article',
            name='related',
            field=sortedm2m.fields.SortedManyToManyField(blank=True, help_text=None, to='aldryn_newsblog.Article', verbose_name='Ähnliche Artikel'),
        ),
        migrations.AlterField(
            model_name='article',
            name='tags',
            field=taggit.managers.TaggableManager(blank=True, help_text='Eine durch Komma getrennte Schlagwortliste.', through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Schlagworte'),
        ),
        migrations.AlterField(
            model_name='articletranslation',
            name='language_code',
            field=models.CharField(db_index=True, max_length=15, verbose_name='Sprache'),
        ),
        migrations.AlterField(
            model_name='articletranslation',
            name='lead_in',
            field=djangocms_text_ckeditor.fields.HTMLField(blank=True, default='', help_text='Der Lead sollte dem Leser die eigentliche Idee des Text geben. Dies ist hilfreich für Überschriften, Listen oder als Einleitung eines Artikels.', verbose_name='Lead'),
        ),
        migrations.AlterField(
            model_name='articletranslation',
            name='meta_description',
            field=models.TextField(blank=True, default='', verbose_name='Meta-Beschreibung'),
        ),
        migrations.AlterField(
            model_name='articletranslation',
            name='meta_keywords',
            field=models.TextField(blank=True, default='', verbose_name='Meta-Schlüsselwörter'),
        ),
        migrations.AlterField(
            model_name='articletranslation',
            name='meta_title',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Meta-Titel'),
        ),
        migrations.AlterField(
            model_name='articletranslation',
            name='slug',
            field=models.SlugField(blank=True, help_text='Wird in der URL verwendet. Wenn dies geändert wird, ändert sich auch die URL. Lösch es um es automatisch neu-generieren zu können.', max_length=255, verbose_name='slug'),
        ),
        migrations.AlterField(
            model_name='articletranslation',
            name='title',
            field=models.CharField(max_length=234, verbose_name='Titel'),
        ),
        migrations.AlterField(
            model_name='categorytranslation',
            name='language_code',
            field=models.CharField(db_index=True, max_length=15, verbose_name='Sprache'),
        ),
        migrations.AlterField(
            model_name='categorytranslation',
            name='name',
            field=models.CharField(default='', max_length=255, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='categorytranslation',
            name='slug',
            field=models.SlugField(blank=True, default='', help_text='Leer lassen um den Slug automatisch zu generieren.', max_length=255, verbose_name='slug'),
        ),
        migrations.AlterField(
            model_name='newsblogarchiveplugin',
            name='app_config',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aldryn_newsblog.NewsBlogConfig', verbose_name='Apphook Konfiguration'),
        ),
        migrations.AlterField(
            model_name='newsblogarchiveplugin',
            name='cache_duration',
            field=models.PositiveSmallIntegerField(default=0, help_text='Wie lange (in sekunden) soll der Inhalt dieses Plugins im cache sein.'),
        ),
        migrations.AlterField(
            model_name='newsblogarticlesearchplugin',
            name='app_config',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aldryn_newsblog.NewsBlogConfig', verbose_name='Apphook Konfiguration'),
        ),
        migrations.AlterField(
            model_name='newsblogarticlesearchplugin',
            name='max_articles',
            field=models.PositiveIntegerField(default=10, help_text='Maximale Anzahl der gefundenen Artikel.', validators=[django.core.validators.MinValueValidator(1)], verbose_name='Max Artikel'),
        ),
        migrations.AlterField(
            model_name='newsblogauthorsplugin',
            name='app_config',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aldryn_newsblog.NewsBlogConfig', verbose_name='Apphook Konfiguration'),
        ),
        migrations.AlterField(
            model_name='newsblogcategoriesplugin',
            name='app_config',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aldryn_newsblog.NewsBlogConfig', verbose_name='Apphook Konfiguration'),
        ),
        migrations.AlterField(
            model_name='newsblogconfig',
            name='create_authors',
            field=models.BooleanField(default=True, help_text='Sollen automatisch Autoren für eingeloggte Benutzer erstellt werden?', verbose_name='Autoren automatisch erstellen?'),
        ),
        migrations.AlterField(
            model_name='newsblogconfig',
            name='exclude_featured',
            field=models.PositiveSmallIntegerField(blank=True, default=0, help_text='Wenn das "Featured Articles" Plugin verwendet wird auf der "article-list-view", wird bevorzugt, dass "Featured Articles" ausgeschlossen wird von der Artikel-Liste selber, umso Dublikate zu vermeiden. Um dies umzusetzen, gebe die gleiche Anzahl von Nummern hier ein, wie im "Featured Articles" Plugin definiert wurden.', verbose_name='Ausgeschlossene Featured Artikel'),
        ),
        migrations.AlterField(
            model_name='newsblogconfig',
            name='namespace',
            field=models.CharField(default=None, max_length=100, unique=True, verbose_name='Instanz Namensraum'),
        ),
        migrations.AlterField(
            model_name='newsblogconfig',
            name='non_permalink_handling',
            field=models.SmallIntegerField(choices=[(200, 'Erlauben'), (302, 'Zum Permalink weiterleiten (Standard)'), (301, 'Permanente Weiterleitung zum Permalink'), (404, 'Zeige 404: Nicht gefunden')], default=302, help_text='Wie sollen nicht-Permamente Links gehandhabt werden?', verbose_name='Nicht-Permanente Links Handhabung'),
        ),
        migrations.AlterField(
            model_name='newsblogconfig',
            name='paginate_by',
            field=models.PositiveIntegerField(default=5, help_text='Wie viele Artikel sollen pro Seite dargestellt werden?', verbose_name='Anzahl der Seitennummern'),
        ),
        migrations.AlterField(
            model_name='newsblogconfig',
            name='pagination_pages_start',
            field=models.PositiveIntegerField(default=10, help_text='Ab wievielen Seiten soll die Seitennavigation zusammengefasst werden.', verbose_name='Start der Seitennummern'),
        ),
        migrations.AlterField(
            model_name='newsblogconfig',
            name='pagination_pages_visible',
            field=models.PositiveIntegerField(default=4, help_text='Bestimme wie viele Seiten bei der groupierung der Seitennummern sichtbar sind auf beiden Richtungen der aktiven Seite.', verbose_name='Sichtbare Seitennummern'),
        ),
        migrations.AlterField(
            model_name='newsblogconfig',
            name='permalink_type',
            field=models.CharField(choices=[('s', 'der-adler-ist-gelandet/'), ('ys', '1969/der-adler-ist-gelandet/'), ('yms', '1969/07/der-adler-ist-gelandet/'), ('ymds', '1969/07/16/der-adler-ist-gelandet/'), ('ymdi', '1969/07/16/11/')], default='slug', help_text='Stil der URLs aus den Beispielen auswählen. (Notiz, alle Typen sind relativ zur Applikations Seite)', max_length=8, verbose_name='Permalink Typ'),
        ),
        migrations.AlterField(
            model_name='newsblogconfig',
            name='search_indexed',
            field=models.BooleanField(default=True, help_text='Sollen Artikel indexiert werden?', verbose_name='Im Suchindex mit einbeziehen?'),
        ),
        migrations.AlterField(
            model_name='newsblogconfig',
            name='template_prefix',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Präfix für Template "dirs"'),
        ),
        migrations.AlterField(
            model_name='newsblogconfig',
            name='type',
            field=models.CharField(max_length=100, verbose_name='Typ'),
        ),
        migrations.AlterField(
            model_name='newsblogconfigtranslation',
            name='app_title',
            field=models.CharField(max_length=234, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='newsblogconfigtranslation',
            name='language_code',
            field=models.CharField(db_index=True, max_length=15, verbose_name='Sprache'),
        ),
        migrations.AlterField(
            model_name='newsblogfeaturedarticlesplugin',
            name='app_config',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aldryn_newsblog.NewsBlogConfig', verbose_name='Apphook Konfiguration'),
        ),
        migrations.AlterField(
            model_name='newsblogfeaturedarticlesplugin',
            name='article_count',
            field=models.PositiveIntegerField(default=1, help_text='Maximale Anzahl der "featured" Artikel.', validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name='newsbloglatestarticlesplugin',
            name='app_config',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aldryn_newsblog.NewsBlogConfig', verbose_name='Apphook Konfiguration'),
        ),
        migrations.AlterField(
            model_name='newsbloglatestarticlesplugin',
            name='cache_duration',
            field=models.PositiveSmallIntegerField(default=0, help_text='Wie lange (in sekunden) soll der Inhalt dieses Plugins im cache sein.'),
        ),
        migrations.AlterField(
            model_name='newsbloglatestarticlesplugin',
            name='exclude_featured',
            field=models.PositiveSmallIntegerField(blank=True, default=0, help_text='Maximale Anzahl von "featured" Artikel, die ausgeschlossen sind. z.B. für Benutzer in Kombination mit "featured" Artikel Plugins.'),
        ),
        migrations.AlterField(
            model_name='newsbloglatestarticlesplugin',
            name='latest_articles',
            field=models.IntegerField(default=5, help_text='Maximale Anzal der neusten Artikel.'),
        ),
        migrations.AlterField(
            model_name='newsblogrelatedplugin',
            name='cache_duration',
            field=models.PositiveSmallIntegerField(default=0, help_text='Wie lange (in sekunden) soll der Inhalt dieses Plugins im cache sein.'),
        ),
        migrations.AlterField(
            model_name='newsblogtagsplugin',
            name='app_config',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aldryn_newsblog.NewsBlogConfig', verbose_name='Apphook Konfiguration'),
        ),
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(blank=True, help_text='Wird in der URL verwendet. Wenn dies geändert wird, ändert sich auch die URL. Lösch es um es automatisch neu-generieren zu können.', max_length=255, verbose_name='slug')),
                ('function', models.CharField(blank=True, default='', max_length=255)),
                ('app_config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aldryn_newsblog.NewsBlogConfig', verbose_name='Apphook Konfiguration')),
                ('visual', filer.fields.image.FilerImageField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='author_override', to=settings.FILER_IMAGE_MODEL)),
            ],
            options={
                'unique_together': {('slug', 'app_config')},
            },
        ),
        migrations.AddField(
            model_name='article',
            name='author_override',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='aldryn_newsblog.Author', verbose_name='Autor'),
        ),
    ]
