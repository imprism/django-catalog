function editItem(id){
    var win = window.open("/admin/catalog/edititem/" + id +
            "/?_popup=1", "EditTreeItemWindow", "menubar=no,width=800,height=730,toolbar=no,scrollbars=yes");
    win.focus();
}

function edit_related(url, id){
    var win = window.open("/admin/catalog/rel/" + url + '/' + id + "/",
    "RelatedTreeItemWindow", "menubar=no,width=800,height=730,toolbar=no,scrollbars=yes");
    win.focus();
}

function view_on_site(id){
    var win = window.open("/admin/catalog/view/" + id + "/", "NewWindow", "scrollbars=yes");
    win.focus();
}

/***** move items on drop *****/
function move_items(source_list, target_id, point) {
    tree_panel.showMask('Перемещение товара');

    Ext.Ajax.request({
        url: '/admin/catalog/json/move/',
        timeout: 10000,
        callback: function() {
            grid_panel.reload();
            tree_panel.selModel.selNode.parentNode.reload();
        },
        success: function(response, options){
            tree_panel.hideMask();
        },
        failure: function(response, options){
            tree_panel.hideMask();
            if (response.staus == '500') {
                Ext.Msg.alert('Ошибка','Ошибка на сервере');
                grid_panel.reload();
                tree_panel.reload();
            }
            if (response.isTimeout) {
                Ext.Msg.alert('Ошибка','Обрыв связи');
                window.location.reload();
            }
        },
        params: {
            source: source_list.join(','),
            target: target_id,
            point: point
        }
    });
}

/********** add items as relations on drop *******/
function add_relations(source_list, target_id, point, url) {
    tree_panel.showMask('Перемещение товара');

    Ext.Ajax.request({
        url: '/admin/catalog/rel/json/' + url + '/add/',
        timeout: 10000,
        callback: function() {
            grid_panel.reload();
            tree_panel.selModel.selNode.parentNode.reload();
        },
        success: function(response, options){
            tree_panel.hideMask();
        },
        failure: function(response, options){
            tree_panel.hideMask();
            if (response.staus == '500') {
                Ext.Msg.alert('Ошибка','Ошибка на сервере');
                grid_panel.reload();
                tree_panel.reload();
            }
            if (response.isTimeout) {
                Ext.Msg.alert('Ошибка','Обрыв связи');
                window.location.reload();
            }
        },
        params: {
            source: source_list.join(','),
            target: target_id,
            point: point
        }
    });
}


/****** delete items *******/
function delete_items(id_list){
    var link_regexp = /\d+-link/;
    var links_to_delete = [];
    var objects_to_delete = [];
    var children_count = 0;
    var warning_message = '';

    console.log('deleting', id_list);
    for (var i=0; i<id_list.length;i++){
        var match = String(id_list[i]).match(link_regexp);
        if (match) {
            // we have a link to delete
            links_to_delete.push(id_list[i]);
        } else {
            objects_to_delete.push(id_list[i]);
        }
    }
    
    Ext.Ajax.request({
        url: '/admin/catalog/json/delete_count/',
        success: function(response, options) {
            var data = Ext.util.JSON.decode(response.responseText);
            children_count = data.all - objects_to_delete.length;
            
            console.log('data: ', data, ' children:', children_count, 'objects', objects_to_delete, objects_to_delete.length);

            // prepare wraning message
            if (children_count > 0 ){
                warning_message = 'Удаление ' + objects_to_delete.length + ' объектов приведет к удалению ' + children_count + ' дочерних объектов';
                    if (links_to_delete.length > 0 ) {
                        warning_message += 'и ' + links_to_delete.length + 'ссылок. Продолжить?';
                    } else {
                        warning_message += '. Продолжить?';
                    }
            } else {
                warning_message = 'Удалить ' + objects_to_delete.length + ' объектов ';
                    if (links_to_delete.length > 0 ) {
                        warning_message += 'и ' + links_to_delete.length + ' ссылок?';
                    } else {
                        warning_message += '?';
                    }
            }

            var parent_id = tree_panel.selModel.selNode ? tree_panel.selModel.selNode.attributes.id : 'root';

            Ext.Msg.confirm('Внимание!', warning_message,
                function(btn, text){
                    if (btn == 'yes') {
                        Ext.Ajax.request({
                            url: '/admin/catalog/json/delete/',
                            success: function(response, options){
                                grid_panel.reload();
                            },
                            failure: function(response, options){
                                grid_panel.reload();
                            },
                            params: {
                                items: id_list.join(','),
                                parent_id: parent_id 
                            }
                        });
                    }
            });

        },
        params: {
            items: objects_to_delete.join(','),
        }
    });
}

