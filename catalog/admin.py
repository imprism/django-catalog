# -*- coding: utf-8 -*-
from catalog.models import Link
from django import template
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.util import unquote
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _
from django.views.generic.simple import direct_to_template
from forms import LinkInsertionForm
from models import TreeItem
from mptt.admin import MPTTModelAdmin
from mptt.forms import MoveNodeForm


def context_admin_helper(admin_instance, request, opts, obj):
    return {
        'root_path': admin_instance.admin_site.root_path,
        'is_popup': request.REQUEST.has_key('_popup'),
        'app_label': opts.app_label,
        'form_url': '.',
        'opts': opts,
        'has_add_permission': admin_instance.has_add_permission(request),
        'has_change_permission': admin_instance.has_change_permission(request, obj),
        'has_delete_permission': admin_instance.has_delete_permission(request, obj),
        'change': False,
        'save_as': False,
        'show_delete': False,
    } 


class CatalogAdmin(admin.ModelAdmin):

    # override to show links
    add_form_template = 'admin/catalog/change_form_with_links.html'
    change_form_template = 'admin/catalog/change_form_with_links.html'

    
    def add_link(self, request, object_id):
        '''Show new link creation form'''
        model = self.model
        opts = model._meta
        
        obj = self.get_object(request, unquote(object_id).rstrip('/newlink'))
        content_type = ContentType.objects.get_for_model(obj)
        
        if request.method == 'POST':
            form = LinkInsertionForm(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponse('<script type="text/javascript">window.close();</script>')
        else:
            form = LinkInsertionForm(initial={
                'object_id': obj.id,
                'content_type': content_type.pk,
            })
         
        fields = form.base_fields.keys()
        fields.remove('content_type')
        fields.remove('object_id')
        fieldsets = [
            (_('Select position'), {
                'fields': ('content_type', 'object_id'),
                'classes': ('collapsed',),
            }),
            (None, {'fields': fields}),
        ]
        # TODO: Make render_link_form function
        # TODO: Make response_link_add function
        context = context_admin_helper(self, request, opts, obj)
        context.update({
            'title': _('Add link to %s') % force_unicode(opts.verbose_name),
            'adminform': helpers.AdminForm(
                form,
                fieldsets,
                {},
                (),
                model_admin=self
            ),
            'errors': helpers.AdminErrorList(form, []),
        })
        context_instance = template.RequestContext(request, current_app=self.admin_site.name)
        return render_to_response('admin/catalog/link_add_form.html',
            context, context_instance=context_instance)

    def get_urls(self, *args, **kwds):
        from django.conf.urls.defaults import patterns, url
        return patterns('',
            url(r'^(\d+)/newlink/$', self.admin_site.admin_view(self.add_link), 
                name='add_link')
        ) + super(CatalogAdmin, self).get_urls()


class TreeItemAdmin(MPTTModelAdmin):
    change_form_template = 'admin/catalog/change_treeiem.html'
    
    
    def move(self, request, object_id):
        '''Move Treeitem form'''
        model = self.model
        opts = model._meta

        treeitem = self.get_object(request, unquote(object_id).rstrip('/move'))
        if request.method == 'POST':
            form = MoveNodeForm(treeitem, request.POST)
            if form.is_valid():
                form.save()
                return HttpResponse('<script type="text/javascript">window.close();</script>')
                return HttpResponseRedirect(
                    reverse('admin:catalog_treeitem_change', args=[treeitem.id,])
                )
        else:
            form = MoveNodeForm(treeitem)

        fields = form.base_fields.keys()
        fieldsets = [
            (None, {'fields': fields}),
        ]
        
        context = context_admin_helper(self, request, opts, treeitem)
        context.update({
            'title': _('Move %s') % force_unicode(opts.verbose_name),
            'adminform': helpers.AdminForm(
                form,
                fieldsets,
                {},
                (),
                model_admin=self,
            ),
            'errors': helpers.AdminErrorList(form, []),
        })
        context_instance = template.RequestContext(request, current_app=self.admin_site.name)
        return render_to_response('admin/catalog/move_node_form.html',
            context, context_instance=context_instance)
    
    def ext_js_config(self, request, extra_context):
        opts = self.model._meta
        if not self.has_change_permission(request, None):
            raise PermissionDenied

        # Check actions to see if any are available on this changelist
        actions = self.get_actions(request)

        # Remove action checkboxes if there aren't any actions available.
        list_display = list(self.list_display)
        context = {
            'list_display': list_display,
            'options': opts,
            'actions': actions,
        }
        if extra_context:
            context.update(extra_context)
        return direct_to_template(request, 'admin/catalog/extjs_admin.html',
            extra_context=context)
    
    def changelist_view_wrapper(self, request, extra_context=None):
        '''Overriding ``changelist_view`` to enable plain html view key in GET'''
        if 'plain' in request.GET:
            # small hack, do not consider 'plain' in GET attributes
            copied_get = request.GET.copy()
            copied_get.pop('plain')
            request.GET = copied_get
            return super(TreeItemAdmin, self).changelist_view(request, extra_context)
        else:
            return self.ext_js_config(request, extra_context)

    def get_urls(self, *args, **kwds):
        from django.conf.urls.defaults import patterns, url
        
        info = self.model._meta.app_label, self.model._meta.module_name
        return patterns('',
            url(r'^(\d+)/move/$', self.admin_site.admin_view(self.move), 
                name='move_tree_item'),
            url(r'^$', self.admin_site.admin_view(self.changelist_view_wrapper),
                name='%s_%s_changelist' % info)
        ) + super(TreeItemAdmin, self).get_urls()


# TODO: Remove delete action (we need to call delete() method per-object)
admin.site.register(TreeItem, TreeItemAdmin)

class LinkAdmin(CatalogAdmin):
    model = Link

admin.site.register(Link, LinkAdmin)