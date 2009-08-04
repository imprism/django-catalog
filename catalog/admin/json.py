# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseServerError
from catalog.models import Section, Item, TreeItem
from django.contrib.auth.decorators import permission_required
from django.utils import simplejson
from django.shortcuts import render_to_response, get_object_or_404


def get_content(parent):
    if parent == 'root':
        parent = None

    tree_items = TreeItem.objects.filter(parent=parent)
    all_sections = [treeitem.section for treeitem in 
        tree_items.filter(section__isnull=False)]
    sections = [treeitem.section for treeitem in 
        tree_items.filter(section__isnull=False, section__is_meta_item=False)]
    metaitems = [treeitem.section for treeitem in 
        tree_items.filter(section__isnull=False, section__is_meta_item=True)]
    items = [treeitem.item for treeitem in tree_items.filter(item__isnull=False)]
    return {'sections': sections, 'metaitems': metaitems, 'items': items}


@permission_required('catalog.add_section', login_url='/admin/')
def tree(request):
    tree = []
    if request.method == 'POST':
        parent = request.REQUEST.get('node', 'root')
        content = get_content(parent)

        for section in content['sections']:
            tree.append({'text': section.tree.name,
                         'id': '%d' % section.tree.id,
                         'cls': 'folder',
                         })
        for metaitem in content['metaitems']:
            tree.append({'text': metaitem.tree.name,
                         'id': '%d' % metaitem.tree.id,
                         'cls': 'folder',
                         })
        for item in content['items']:
            tree.append({'text': item.tree.name,
                         'id': '%d' % item.tree.id,
                         'leaf': True,
                         'cls': 'leaf',
                         })
    return HttpResponse(simplejson.encode(tree))


@permission_required('catalog.change_section', login_url='/admin/')
def list(request):
    grid = []
    if request.method == 'POST':
        parent = request.REQUEST.get('node', 'root')
        content = get_content(parent)

        def object2dict(obj):
            return {
                'name': obj.tree.name,
                'id': '%d' % obj.tree.id,
                'cls': 'folder' if obj.tree.get_type() == 'section' else 'leaf',
                'type': obj.tree.get_type(),
                'itemid': obj.id,
                'show': obj.tree.show,
                'price': float(0 if obj.price is None else obj.price) if obj.tree.get_type() == 'item' else 0,
                'quantity': int(0 if obj.quantity is None else obj.quantity) if obj.tree.get_type() == 'item' else 0,
                'has_image': False if obj.images.count() == 0 else True,
                'has_description': True if obj.tree.short_description  else False,
                }

        for section in content['sections']:
            grid.append(object2dict(section))

        for metaitem in content['metaitems']:
            grid.append(object2dict(metaitem))

        for item in content['items']:
            grid.append(object2dict(item))

    return HttpResponse(simplejson.encode({'items': grid}))

# moving tree items

def get_tree_item(node):
    if node == 'root':
        item = None
    else:
        try:
            item = TreeItem.objects.get(id=int(node))
        except TreeItem.DoesNotExist, ValueError:
            item = None
    return item

def may_move(node, parent):
    move_matrix = {
        'item': ['section', 'metaitem'],
        'metaitem': ['section'],
        'section': ['section'],
        }
    if parent is None:
        return True
    elif parent.get_type() in move_matrix[node.get_type()]:
        return True
    else:
        return False

def move_node(request):
    if request.method == 'POST':
        sources = request.REQUEST.get('source', '').split(',')
        target_id = int(request.REQUEST.get('target', ''))
        point = request.REQUEST.get('point', '')
        if point == 'above':
            position = 'left'
        elif point == 'below':
            position = 'right'
        else:
            position = 'last-child'

        new_parent = get_tree_item(target_id)
        move = []
        for source in sources:
            this_section = get_tree_item(source)
            if may_move(this_section, new_parent):
                move.append(True)
            else:
                move.append(False)

        if all(move):
            for source in sources:
                this_section = get_tree_item(source)
                this_section.move_to(new_parent, position)
            return HttpResponse('OK')
        else:
            return HttpResponseServerError('Can not move')

def visible(request):
    try:
        items_list = request.REQUEST.get('items', '').split(',')
        show = bool(int(request.REQUEST.get('visible', '1')))
        TreeItem.objects.filter(id__in=items_list).update(show=show)
        return HttpResponse('OK')
    except ValueError:
        return HttpResponseServerError('Bad arguments')

def delete_items(request):
    try:
        items_list = request.REQUEST.get('items', '').split(',')
        items_to_delete = TreeItem.objects.filter(id__in=items_list)
        for item in items_to_delete:
            item.delete()
        return HttpResponse('OK')
    except ValueError:
        return HttpResponseServerError('Bad arguments')

class RelativeTree(object):

    def save(self, request, obj_id):
        current_item = get_object_or_404(Item, id=obj_id)
        relative_list = request.REQUEST.get('relative', '').split(',')
        # add
        ids_to_add = [obj_id for obj_id in relative_list 
            if int(obj_id) not in current_item.relative.values_list('id', flat=True)]
        # remove
        objs_to_remove = [obj for obj in current_item.relative.all()
            if str(obj.id) not in relative_list]
        
        for new_obj_id in ids_to_add:
            object = get_object_or_404(TreeItem, id=new_obj_id)
            current_item.relative.add(object)
        
        for obj in objs_to_remove:
            current_item.relative.remove(obj)
        return HttpResponse('OK')

    def tree(self, request, obj_id):
        current_item = get_object_or_404(Item, id=obj_id)
        
        tree = []
        if request.method == 'POST':
            parent = request.REQUEST.get('node', 'root')
            content = get_content(parent)
    
            for section in content['sections']:
                tree.append({'text': section.tree.name,
                             'id': '%d' % section.tree.id,
                             'cls': 'folder',
                             })
            for metaitem in content['metaitems']:
                tree.append({'text': metaitem.tree.name,
                             'id': '%d' % metaitem.tree.id,
                             'cls': 'folder',
                             })
            for item in content['items']:
                tree.append({'text': item.tree.name,
                             'id': '%d' % item.tree.id,
                             'cls': 'leaf',
                             'leaf': True,
                             'checked': item.tree.id in current_item.relative.values_list('id', flat=True),
                             })
        return HttpResponse(simplejson.encode(tree))
