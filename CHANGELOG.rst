Changelog
=========

2.2.3.30 (2023-03-22)
=====================

* Fix problem with a clean migration that was not correctly respecting migration dependencies
* Fix missing import in backwards migration

2.2.3.29 (2023-01-27)
=====================

* Fix warning after model changes from 2.2.3.28

2.2.3.28 (2023-01-13)
=====================

* Add write permissions limitations for users per blog section

2.2.3.27 (2022-09-01)
=====================

* Fix slow page tree generation

2.2.3.26 (2022-06-30)
=====================

* Fixed ValueError in parsing of ``max_articles`` parameter

2.2.3.25 (2022-05-25)
=====================

* Display NewsBlogConfig as column in the admin Tag list

2.2.3.24 (2022-03-30)
=====================

* Fixed latest articles feed of a tag view

2.2.3.23 (2021-12-13)
=====================

* Fixed exclude_featured articles functionality

2.2.3.22 (2021-12-01)
=====================

* Replaced taggit usage with a custom model with m2m realtionship for article tags

2.2.3.21 (2021-11-23)
=====================

* MySQL support for exclude_featured articles functionality

2.2.3.20 (2021-09-20)
=====================

* Fix ``get_render_template`` for ``NewsBlogRelatedPlugin``


2.2.3.19 (2021-08-06)
=====================

* Adding author instance to article before form validation on new article wizard


2.2.3.18 (2021-11-05)
=====================

* Limited authors queryset by site in admin cpanel list


2.2.3.17 (2021-11-05)
=====================

* Limited categories queryset by app config of the blog article


2.2.3.16 (2021-11-05)
=====================

* RSS displaying images


2.2.3.15 (2021-05-05)
=====================

* Author list plugin showing only authors of current section


2.2.3.14 (2021-05-05)
=====================

* Limiting author selection by section in article admin cpanel


2.2.3.11 (2021-04-21)
=====================

* Added a new "Author" model and ability to override existing author field with it


2.2.3.5 (2020-09-22)
====================

* Added a new "Category" model and implemented the way to migrate all the old Article's relations


2.2.3.4 (2020-09-09)
====================

* Make the person field optional


2.2.3.3 (2020-06-30)
====================

* Add multisite support integration


2.2.3.2 (2020-06-30)
====================

* Add another render_placeholder_no_cache template tag


2.2.3.1 (2020-03-10)
====================

* Update the urls regex to fix the issue


2.2.3 (2020-03-10)
==================

* Fix the URLs issue (articles-list)
* Fix the compatibility with django-taggit


2.2.2
==================

* Updated translations
* Fixed error when page with attached menu without apphook was not working
* Removed the dollar from the routes
* Fixed article search functionality to work with django CMS 3.6


2.2.1 (2019-02-12)
==================

* Added missing POST methods for newsblog views


2.2.0 (2019-02-05)
==================

* Added support for Django 2.0 and 2.1
* Removed support for Django < 1.11
* Adapted testing infrastructure (tox/travis) to incorporate django CMS 3.6


2.1.4 (2019-02-04)
==================

* Fixed problem with not working sending forms on apphooked pages


2.1.3 (2018-06-21)
==================

* Reverted "Fixed NoReverseMatch errors raised when indexing an article not present on the site being indexed."


2.1.2 (2018-06-14)
==================

* Fixed NoReverseMatch errors raised when indexing an article not present
  on the site being indexed.


2.1.1 (2018-04-10)
==================

* django-parler >= 1.8.1 is now required
* Fixed FieldError on creating article from cms wizard


2.1.0 (2018-04-06)
==================

* Introduced Django 1.11 support
* Dropped django CMS 3.2 & 3.3 support


2.0.0 (2018-01-25)
==================

* Introduced django CMS 3.5 support
* Dropped aldryn-reversion/django-reversion support


1.3.3 (2017-05-15)
==================

* Admin UI enhancements


1.3.2 (2017-03-23)
==================

* Disabled caching for ``NewsBlogCategoriesPlugin`` plugin.


1.3.1 (2017-03-02)
==================

* Updated translations
* Removed cache exclusion for ``NewsBlogRelatedPlugin`` plugin.


1.3.0 (2016-09-05)
==================

* Fixed related_name inconsistency with django CMS 3.3.1
* Dropped support for djangoCMS < 3.2
* Introduced support for djangoCMS 3.4.0


1.2.4 (2016-07-14)
==================

* Relaxed sortedm2m version range
* Updated translation setup for transifex
* Updated translation strings
* Fixed aldryn_translation_tools not being added to INSTALLED_APPS on Aldryn


1.2.3 (2016-06-28)
==================

* Updated translation setup for transifex
* Fixed bootstrap3 article template sometimes causing broken pages
* Added support for cache durations fields in "time-sensitive" plugins on django CMS 3.3.0+
* Added support for newer versions of django-filer


1.2.2 (2016-05-19)
==================

* Adds support for Python 3.5
* Adds support for Django 1.9
* Adds support for CMS 3.3.x


1.2.1 (2016-03-18)
==================

* Adapt pagenav to hide too many entries
* Pagenav shows "..." if there are to many pages forward or backwards
* Add pagenav settings to apphook configs


1.2.0 (2016-03-10)
==================

* Remove unused render_placeholder configs
* Add static_placeholders where necessary
* Simplify templates


1.1.1 (2016-02-12)
==================

* Change default for app config setting ``default_published`` to False


1.1.0 (2016-02-12)
==================

* Add Django 1.9 compatibility
* Add stripped default django templates to ``/aldryn_newsblog/templates``
* Newly created articles are not published by default
* UX admin interface improvements


1.0.12 (2016-01-12)
===================

* Updates for recent versions of django-reversion
* Adds integration tests against CMS v3.2


1.0.11 (2016-01-09)
===================

* Adds support for reversion with wizards
* Cleans-up and updates test configuration


1.0.10 (2015-11-20)
===================

* Fixes CMS 3.2 wizard
* Fixes issue with lazy translations


1.0.9 (2015-11-04)
==================

* Fixes restrictive django-filer dependency (<0.10)


1.0.8 (2015-11-01)
==================

* Adds Django 1.8 support
* Pins Aldryn Translation Tools to >= 0.1.2
* Pins Aldryn Boilerplates to >=0.7.2
* Menu (CMSAttachMenu) is no longer automatically added
* Adds a CMS 3.2 wizard for creating articles


1.0.7 (2015-10-31)
==================

* Add missing requirement python-dateutil


1.0.6 (2015-08-06)
==================

* Overhaul the News & Blog CMS Toolbar
* Pins Aldryn Translation Tools to >=0.1.0
* Pins Aldryn Reversion to >=0.1.0
* Pins Aldryn Boilerplates to >=0.6.0
* Documentation improvements
* Fixes tag link on article detail page


1.0.5 (2015-07-22)
==================

* Unrestricts Aldryn Translation Tools and implements AllTranslationsMixin
  where appropriate.


1.0.4 (2015-07-22)
==================

* Restrict Aldryn Translation Tools to <0.0.7


1.0.3 (2015-07-22)
==================

* Adds frontend testing configuration and tests
* Restricts Aldryn Reversion to <0.1.0


1.0.2 (2015-07-13)
==================

* Adds a switch: ALDRYN_NEWSBLOG_UPDATE_SEARCH_DATA_ON_SAVE that when set to
  False, prevents article data from being saved into search_data. This is useful
  in environments which prefers to do all indexing in batches.
* Adds a management command: rebuild_article_search_data which can be used to
  update search_data for all articles.


1.0.1 (2015-06-30)
==================

* Fixes an issue where unintended, empty translations are created


1.0.0 (2015-06-23)
==================

* First production release
* i18n improvements
* Spaces support fixes
* Improve user documentation
* Increase test coverage


0.9.6 (2015-05-31)
==================

* Fixes search index bug
* Fixes testsuite issue with django-filer>=0.9.10
* Fixes bug with toolbar


0.9.5 (2015-05-21)
==================

* Improves migration-ability
* improves support for some version of MySQL
* Improves auto-slugification process


0.9.4 (2015-04-26)
==================

* Now requires v0.1.3+ of aldryn-common
* Now requires v0.5.2+ of aldryn-people
* Fixes a bad migration
* Tested to work in django CMS 3.0.x and 3.1.x
* Other minor refactoring


0.9.3 (2015-04-23)
==================

* Fixes older South migration (0028) for CMS 3.1
* Add "magic" migrations to move from old-style CMS plugin table naming to new
  for users using older versions of CMS.
* Post a deprecation notice about supporting only CMS 3.0+ from version 1.0.0
  of Aldryn News & Blog.


0.9.2 (2015-04-21)
==================

* Pin parler to version 1.4, which is required by the latest migration.
* Reimplements a means of allowing users to use plugins and Articles before
  creating and publishing the corresponding apphook'ed page. This new method
  gives more flexibility to developers and template authors.


0.9.1
-----

Unreleased.


0.9.0 (2015-04-20)
==================

* Adds breadcrump support by adding a CMSAttachMenu. NOTE: django CMS v3.0.14
  or v3.1 or later must be used to have working breadcrumbs.
* Adds support for swappable User models.
* Adds sitemaps support.
* Improves support of language fallbacks as defined in CMS_LANGUAGES
* Adds new app configuration option for setting a template prefix.
* Fix an error in search indexer that breaks indexing if an article has no
  search data
* Search indexer is using switch_language from parler
* Now requires aldryn-apphooks-config v0.2.4 or later


0.8.8 (2015-04-??)
==================


0.8.7 (2015-04-??)
==================


0.8.6 (2015-04-16)
==================

* Use get_current_language from cms instead get_language from Django because Django bug #9340


0.7.5 (2015-04-16)
==================

* Use get_current_language from cms instead get_language from Django because Django bug #9340


0.2.0 (2015-02-03)
==================

* multi-boilerplate support
  new requirement: aldryn-boilerplates (needs configuration)
