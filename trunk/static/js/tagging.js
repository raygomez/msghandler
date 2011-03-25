$(
    function(){
        $('.top-td').live('mouseenter', function(){$($(this).children()[1]).show();})
        $('.top-td').live('mouseleave', function(){$($(this).children()[1]).hide();});
    }
)

function addtags(widget){    
    tags = $.grep(tags, function(tag){ return tag.id != parseInt(widget.target.id.split('t')[1])});
    td = $('<span>'+ widget.target.name +'</span>');
    td1 = $('<img>').attr({
            src:'/msghandler/static/images/delete.png',
            class:'tags-add',
            hidden:true,
            id: 'img' + widget.target.id,
            name: widget.target.name,
        });

    $(widget.target).parent().fadeOut(function() { $(this).remove(); });
    $('#tr-tags-new table tr').append($('<td class="top-td">').append(td,td1));
    
    $('.tags-add').unbind();
    $('.tags-add').one('click', function(){
                $(this).parent().fadeOut( function() { $(this).remove(); update_tags();});
                id = parseInt(this.id.split('imgt')[1]);
                tag = {id:id, name:this.name};
                tags.push(tag);    
                $('#msg_attachment_tags').keyup();                 
    });
    
    update_tags();
}

function update_tags(){
    selected = $('img.tags-add');
    str = '';
    for(i= 0 ; i < selected.size(); i++){
        str = str + selected[i].id.split('t')[1] + ',';
    }
    $(':input[name=tags_new]').val(str);
}

function showtags()
{
    var text = $(':input[name=tags]').val().toLowerCase();
    var pattern = new RegExp('^.*' + text + '.*$', 'ig');

    $('#new-tags').children().remove();
    if(text != ''){
        for(i = 0; i < tags.length; i++){
            if (tags[i].name.match(pattern)) 
            {
                $('#new-tags').append($('<div>').attr({ 
                      class: 'tags',
                      id: 'tag-'+tags[i].id,
                    }).append($('<input>').attr({
                         type: 'checkbox',
                         id: 't' + tags[i].id,
                         name: tags[i].name,
                       })).append($('<label>').text(tags[i].name)));
                  $('#t'+tags[i].id).one('click', addtags);                  
             }
        }
    }
}
