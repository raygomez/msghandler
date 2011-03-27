$(
    function(){
        $('.top-td').live('mouseenter', function(){$($(this).children()[1]).show();})
        $('.top-td').live('mouseleave', function(){$($(this).children()[1]).hide();});
    }
)

function addgroups(widget){    
    groups = $.grep(groups, function(group){ return group.role != widget.target.name } )
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
    $('.groups-add').one('click', function(){
                $(this).parent().fadeOut( function() { $(this).remove(); updategroups();});
                id = parseInt(this.id.split('imgt')[1]);
                tag = {id:id, role:this.name};
                groups.push(tag);    
                showgroups();                 
    });
    
    updategroups();
}

function updategroups(){
    selected = $('img.groups-add');
    str = '';
    for(i= 0 ; i < selected.size(); i++){
        str = str + selected[i].id + ',';
    }
    $(':input[name=groups_new]').val(str);
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
                $('#new-groups').append($('<div>').append($('<input>').attr({
                         type: 'checkbox',
                         id: 't' + groups[i].id,
                         name: groups[i].role,
                       })).append($('<label>').text(groups[i].role)));
                  $('#t'+groups[i].id).one('click', addgroups);                  
             }
        }
    }
}
