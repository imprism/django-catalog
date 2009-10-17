# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from catalog.fields import RelatedField
from catalog.models import TreeItem, Base

from catalog import settings as catalog_settings

# fake tinymce
if catalog_settings.CATALOG_TINYMCE:
    from tinymce.models import HTMLField
else:
    from django.forms import Textarea as HTMLField
# fake imagekit
if catalog_settings.CATALOG_IMAGEKIT:
    from imagekit.models import ImageModel
else:
    from django.db.models import Model as ImageModel


class Section(Base):
    class Meta:
        verbose_name = u"Раздел каталога"
        verbose_name_plural = u'Разделы каталога'

    images = generic.GenericRelation('TreeItemImage')

    # Display options
    show = models.BooleanField(verbose_name=u'Отображать', default=True)

    # Primary options
    slug = models.SlugField(verbose_name=u'Slug', max_length=200, null=True, blank=True)
    name = models.CharField(verbose_name=u'Наименование', max_length=200, default='')
    description = models.TextField(verbose_name=u'Описание', null=True, blank=True)

    @models.permalink
    def get_absolute_url(self):
        return self.tree.get().get_absolute_url()

    def formatted_name(self):
        return itemname(self.name)

    def get_all_items(self):
        children = self.tree.get().children_item() | self.tree.get().children_metaitem()
        related_ids = self.items.values_list('id', flat=True)
        item_ct = ContentType.objects.get_for_model(Item)
        metaitem_ct = ContentType.objects.get_for_model(MetaItem)
        related_items = TreeItem.objects.filter(content_type=item_ct, object_id__in=related_ids)
        related_metaitems = TreeItem.objects.filter(content_type=metaitem_ct, object_id__in=related_ids)
        return children | related_items | related_metaitems

    def get_all_items_show(self):
        filtered = []
        for treeitem in self.get_all_items():
            if treeitem.content_object.show:
                filtered.append(treeitem)
        return filtered

    def ext_tree(self):
        return {
            'text': self.name,
            'id': '%d' % self.tree.get().id,
            'leaf': False,
            'cls': 'folder',
         }

    def ext_grid(self):
        return {
            'name': self.name,
            'id': '%d' % self.tree.get().id,
            'type': self.tree.get().content_type.model,
            'itemid': self.id,
            'show': self.show,
            'price': 0.0,
            'quantity': 0,
            'has_image': False if self.images.count() == 0 else True,
            'has_image': False,
            'has_description': False if self.description is None else True,
        }

    def has_nested_sections(self):
        section_ct = ContentType.objects.get_for_model(Section)
        return bool(len(self.tree.get().children.filter(content_type=section_ct)))

    def __unicode__(self):
        return self.name


class MetaItem(Section):
    class Meta:
        verbose_name = u"Метатовар"
        verbose_name_plural = u'Метатовары'

    images = generic.GenericRelation('TreeItemImage')

    exclude_children = [u'section']

    @models.permalink
    def get_absolute_url(self):
        return self.tree.get().get_absolute_url_undecorated()

    def palletes(self):
        palletes = []
        for child in self.tree.get().children.all():
            palletes += child.content_object.images.filter(pallete=True)
        return palletes

    def price(self):
        return min([child.content_object.price for child in self.tree.get().children.all()])


class Item(Base):
    class Meta:
        verbose_name = u"Продукт каталога"
        verbose_name_plural = u'Продукты каталога'

    images = generic.GenericRelation('TreeItemImage')

    # Display options
    show = models.BooleanField(verbose_name=u'Отображать', default=True)

    # Primary options
    slug = models.SlugField(verbose_name=u'Slug', max_length=200, null=True, blank=True)
    name = models.CharField(verbose_name=u'Наименование', max_length=200, default='')
    description = models.TextField(verbose_name=u'Описание', null=True, blank=True)

    # Item fields
    # Relation options
    relative = RelatedField('Item', verbose_name=u'Сопутствующие товары', null=True, blank=True, related_name='relative')
    sections = RelatedField('Section', verbose_name=u'Разделы', null=True, blank=True, related_name='items')

    # Sale options
    price = models.DecimalField(verbose_name=u'Цена', null=True, blank=True, max_digits=12, decimal_places=2)
    quantity = models.IntegerField(verbose_name=u'Остаток на складе',
        help_text=u'Введите 0 если на складе нет товара', null=True, blank=True)

    exclude_children = [u'item', u'section', u'metaitem']

    @models.permalink
    def get_absolute_url(self):
        return self.tree.get().get_absolute_url_undecorated()

    def formatted_name(self):
        return itemname(self.name)

    def ext_tree(self):
        return {
            'text': self.name,
            'id': '%d' % self.tree.get().id,
            'leaf': True,
            'cls': 'leaf',
         }

    def ext_grid(self):
        return {
            'name': self.name,
            'id': '%d' % self.tree.get().id,
            'type': 'item',
            'itemid': self.id,
            'show': self.show,
            'price': float(self.price) if self.price is not None else 0.0,
            'quantity': self.quantity,
            'has_image': False if self.images.count() == 0 else True,
            'has_description': False if self.description is None else True,
        }

    def __unicode__(self):
        return self.name

class TreeItemImage(ImageModel):
    image = models.ImageField(verbose_name=u'Изображение',
        upload_to='upload/catalog/itemimages/%Y-%m-%d')

    pallete = models.BooleanField(default=False, verbose_name=u'Палитра',
        help_text=u'Картинка будет отображаться в полном размере после описания')

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class IKOptions:
        cache_dir = 'upload/catalog/cache'
        spec_module = 'catalog.ikspec'

    def __unicode__(self):
        return self.image.url
