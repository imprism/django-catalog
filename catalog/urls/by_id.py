# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, include, handler404, handler500, url
from django.conf import settings
from catalog.urls import urlpatterns

handler404
handler500

urlpatterns += patterns('',
    url(r'^(?P<slug>[\w\-]*)-(?P<object_id>\d+)$', 'catalog.views.by_id', name='catalog-by-id'),
)
