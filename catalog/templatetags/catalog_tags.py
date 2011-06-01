from catalog.models import TreeItem
from catalog.utils import get_data_appnames
from classytags.arguments import Argument, ChoiceArgument
from classytags.core import Tag, Options
from classytags.helpers import InclusionTag
from django import template
from django.template import loader, TemplateSyntaxError
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

register = template.Library()

TREE_TYPE_EXPANDED = 'expanded'
TREE_TYPE_COLLAPSED = 'collapsed'
TREE_TYPE_DRILLDOWN = 'drilldown'


def get_treeitem_from_context(context, silent=True):
    '''
    Utility tries to get TreItem from ``context['object']``.
    
    If silent=False, returns TreeItem instance or raises TemplateSyntaxError,
    otherwise returns TreeItem instance or None
    '''
    # Try to resolve ``object`` from context
    if 'object' in context and (getattr(context['object'], 'tree'), None):
        obj = context['object']
        if (hasattr(obj.tree, 'get') and callable(obj.tree.get)):
            # Check that object.tree.get() returns TreeItem instance
            if (isinstance(context['object'].tree.get(), TreeItem)):
                treeitem = obj.tree.get()
    if silent:
        return None
    else:
        raise TemplateSyntaxError('No TreeItem instance found in context')

class CatalogChildren(Tag):
    '''
    Render or get chlidren for given object. Object must be registered in 
    catalog tree and have the ``tree()`` attribute.
    
    **Usage**::
    
        {% catalog_children [for my_section] [type children_type] [as varname] %}

    **Magic**
    
        If context has ``object`` variable and *for* paramenter is not specified,
        it will try to fetch ``object.tree.get()`` automatically, and if it find
        ``TreeItem`` instance as result of object.tree.get(), it will 
        show children for it.
    
    **Examples**
        
        1. Render children for ``my_section`` context object. ::
           
            {% catalog_children for my_section %}
            
          or render children for ``object`` in context ::
          
            {% catalog_children for my_section %}
        
        2. Render children for ``my_section`` into ``children`` context variable. ::
    
            {% catalog_children for my_section as children %}
        
        3. Render children only with type ``item`` for ``my_section`` ::
        
            {% catalog_children for my_section type item %}
        

    '''
    name = 'catalog_children'
    templates = ['catalog/children_tag.html', ]

    options = Options(
        'for',
        Argument('instance', required=False),
        'type',
        Argument('children_type', required=False, resolve=False),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def render_tag(self, context, instance, children_type, varname):
        if instance is not None:
            try:
                treeitem = instance.tree.get()
            except AttributeError:
                raise TemplateSyntaxError('Instance argument must have `tree` attribute')
        else:
            # try to guess
            treeitem = get_treeitem_from_context(context)

        children_qs = TreeItem.objects.published().filter(parent=treeitem)
        if children_type:
            children_qs = children_qs.filter(content_type__model=children_type)

        if varname:
            context[varname] = children_qs
            return ''
        else:
            self.templates[0:0] = ['%s/children_tag.html' % app_name for app_name in get_data_appnames()]
            context['children_queryset'] = children_qs
            return render_to_string(self.templates, context)

register.tag(CatalogChildren)


class BreadcrumbTag(InclusionTag):
    '''
    TODO: DOCME!
    '''
    name = 'catalog_breadcrumbs'
    template = 'catalog/breadcrumbs.html'

    def get_context(self, context, **kwargs):
        treeitem = get_treeitem_from_context(context, silent=False)
        if treeitem is not None:
            ancestors = list(treeitem.get_ancestors())
            return {'breadcrumbs': ancestors + [treeitem, ] }
        else:
            return {}

register.tag(BreadcrumbTag)

class CatalogTree(Tag):
    '''
    Render catalog tree menu
        
    **Usage**::
    
        {% render_catalog_tree [activate active_treeitem] [type type] [current current_treeitem] %}
    
    **Parameters**:
        active_treeitem
            Activate element in tree, highlight or select it
        type
            Menu type. Three types available:
            
            * ``drilldown`` - enabled by default. It will expand only active 
                path in tree
            * ``collapsed`` - menu will be collapsed only to dislpay root elements
            * ``expanded`` - all menu nodes will be expanded
        current_treeitem
            Argument for internal usage, for recursion organization
    
    **Magic**
    
        Templatetag casts a spell a bit. If context has ``object`` variable,
        it will try to fetch ``object.tree.get()`` automatically, and if it find
        ``TreeItem`` instance as result of object.tree.get(), it will set
        active_treeitem = obejct.tree.get() silently.
    
    **Template**
    
        {% render_catalog_tree %} use ``catalog/tree.html`` template to render menu
    
    **Examples**
    
    1. Render full catalog tree ::
       
        {% render_catalog_tree type 'expanded' %}
    
    2. Render drill-down catalog tree ::

            {% render_catalog_tree %}
        
      same results can be achieved by specifying arguments directly and without *magic*::
        
            {% render_catalog_tree activate object.tree.get type 'drilldown' %}
    
    3. Render only root nodes::
    
            {% render_catalog_tree type 'collapsed' %}

    '''
    name = 'render_catalog_tree'
    template = 'catalog/tree.html'

    options = Options(
        'activate',
        Argument('active', required=False),
        'type',
        Argument('tree_type', required=False, resolve=True, default=TREE_TYPE_DRILLDOWN),
        'current',
        Argument('current', required=False),
    )

    def render_tag(self, context, active, tree_type, current):
        context.push()
        if current is not None:
            children = current.children.published()
        else:
            children = TreeItem.objects.published().filter(parent=None)
        if active is None:
            # Try to resolve ``object`` from context
            active = get_treeitem_from_context(context)

        if active is not None:
            context['breadcrumbs'] = [active]
            context['breadcrumbs'].extend(active.get_ancestors())

        context['object_list'] = children
        context['type'] = tree_type
        context['active'] = active
        context['current'] = current

        output = render_to_string(self.template, context)
        context.pop()
        return output

register.tag(CatalogTree)
