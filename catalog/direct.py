# -*- coding: utf-8 -*-
from catalog import settings as catalog_settings
from catalog.models import TreeItem
from django.contrib import admin
from django.db.models import loading
from django.utils import simplejson
from extdirect.django import ExtDirectStore
from extdirect.django.decorators import remoting
from extdirect.django.providers import ExtRemotingProvider

provider = ExtRemotingProvider(namespace='Catalog', url='/admin/catalog/treeitem/direct/router/')

class Column(object):
    _map = {
        # python type - xtype
        unicode: 'gridcolumn',
        str: 'gridcolumn',
        bool: 'booleancolumn',
        int: 'numbercolumn',
    }

    xtype = 'gridcolumn'
    type = unicode
    
    def __init__(self, name, instance, order=0):
        '''
        Creates a column with name and order
        Detect type by instance
        '''
        self.name = name
        self.order = order
        
        # detect type
        if attr_type is int:
            self.type = int
            self.xtype = 'numbercolumn'
        elif attr_type is bool:
            self.type = bool
            self.xtype = 'booleancolumn'
        else:
            # default type and xtype
            self.type = unicode
            self.xtype = 'gridcolumn'
    
    def merge(self, new_field):
        '''
        Merge properties with other model field
        If types are similar, don't change them, otherwise convert all to strings.
        Set order to max order of both instances.
        Returns True if types are similar
        '''
        if self.type == new_field.type:
            self.order =  max(self.order, new_field.order)
            return True
        else:
            self.type = unicode
            self.xtype = 'gridcolumn'
            self.order = max(self.order, new_field.order)
            return False
    

class ColumnModel(object):
    '''Represents python-ExtJS map of types for grid'''
    
    def __init__(self, site):
        '''
        Creates column model singletone. 
        Reads data from django models loader and given site registry
        '''
        self.model_cache = loading.cache
        self.admin_registry = site._registry
        self.fields = {}
        
        for app_label, model_name in catalog_settings.CATALOG_MODELS:
            model_cls = self.model_cache.get_model(app_label, model_name)
            admin_cls = self.admin_registry[model_cls]
            
            list_display = list(admin_cls.list_display)
            list_display.remove('action_checkbox')
            
            # Run over all 'list_display' properties and fill columns
            for i, field_name in enumerate(list_display):
                new_field = Column(field_name, model_cls(), i)
                if field_name not in self.fields:
                    self.fields[field_name] = new_field
                else:
                    self.fields[field_name].merge(new_field)


@remoting(provider, action='treeitem', len=1)
def objects(request):
    '''
    Data grid provider
    '''
    data = request.extdirect_post_data[0]
    items = ExtDirectStore(TreeItem)
    return items.query(**data)

@remoting(provider, action='treeitem', len=1)
def tree(request):
    '''
    Server-side expand of tree structure implementation
    '''
    node = request.extdirect_post_data[0]
    if node == 'root':
        node = None
    children = TreeItem.objects.filter(parent=node)
    data = []
    for item in children:
        data.append({
            'leaf': bool(item.children.all().count() == 0),
            'id': item.id,
            'text': unicode(item.content_object),
        })
    
    return simplejson.dumps(data)

@remoting(provider, action='colmodel')
def getCM():
    '''
    Returns JSON configuration which should be passed into 
    ext.grid.ColumnModel() constructor
    '''
    return catalog_registry