# Generated by Django 2.2.24 on 2021-11-30 17:07

from django.db import migrations


def populate_article_tags(apps, schema_editor):
    from taggit.models import Tag

    if Tag.objects.exists():
        populate_article_tags_from_taggit_tags()


def populate_article_tags_from_taggit_tags():
    from aldryn_newsblog.models import Article, ArticleTag

    for article in Article.objects.all():
        for taggit_tag in article.tags.all():
            article_tag = ArticleTag.objects.get_or_create(
                translations__slug=taggit_tag.slug,
                newsblog_config_id=article.app_config_id,
                defaults={
                    'slug': taggit_tag.slug,
                    'name': taggit_tag.name,
                    'newsblog_config_id': article.app_config_id
                }
            )[0]
            if article_tag not in article.article_tags.all():
                article.article_tags.add(article_tag)


def remove_all_article_tags(apps, schema_editor):
    from aldryn_newsblog.models import Article, ArticleTag

    for article in Article.objects.all():
        article.article_tags.clear()
    ArticleTag.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('aldryn_newsblog', '0026_auto_20211130_2341'),
        ('filer', '0012_file_mime_type'),
    ]

    operations = [
        migrations.RunPython(populate_article_tags, remove_all_article_tags)
    ]