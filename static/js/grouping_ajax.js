$(
    function(){
        $('.top-td').live('mouseenter', function(){$($(this).children()[1]).show();})
        $('.top-td').live('mouseleave', function(){$($(this).children()[1]).hide();});
    }
)

function addgroups(widget){    
    groups = $.grep(groups, function(group){ return group.role != widget.target.name } )
    
    $.ajax({
        url: '/msghandler/default/insert_ajax_group',
        data: 'group=' + this.id  + '&id=' + user_id
        })             
    
    td1 = $('<img>').attr({
            src:'/msghandler/static/images/delete.png',
            class:'groups-add',
            hidden:true,
            id: 'img' + widget.target.id,
            name: widget.target.name,
        });

    $(widget.target).parent().fadeOut(function() { $(this).remove(); });
    $('#tr-groups-new table tr').append($('<td class="top-td">').append($('<span>'+ widget.target.name +'</span>'),td1));
    
    $('.groups-add').unbind();
    click_once_group();
}

function click_once_group(){
    $('.groups-add').one('click', function(){
                $(this).parent().fadeOut( function() { $(this).remove();});
                tag = {id:parseInt(this.id.split('imgt')[1]), role:this.name};
                groups.push(tag); 
                $.ajax({
                    url: '/msghandler/default/delete_ajax_group',
                    data: 'group=' + this.id  + '&id=' + user_id
                })             
               showgroups();                 
    });
}

function showgroups()
{
    var text = $(':input[name=groups]').val().toLowerCase();
    var pattern = new RegExp('^.*' + text + '.*$', 'ig');

    $('#new-groups').children().remove();
    if(text != ''){
        for(i = 0; i < groups.length; i++){
            if (groups[i].role.match(pattern)) 
            {
                $('#new-groups').append($('<div>').attr({ 
                      id: 'tag-'+groups[i].id,
                    }).append($('<input>').attr({
                         type: 'checkbox',
                         id: 't' + groups[i].id,
                         name: groups[i].role,
                       })).append($('<label>').text(groups[i].role)));
                  $('#t'+groups[i].id).one('click', addgroups);                  
             }
        }
    }
}
