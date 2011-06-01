function addtags(widget){    
    tags = $.grep(tags, function(tag){ return tag.name != widget.target.name});
    td1 = $('<img>').attr({
            src:'/msghandler/static/images/delete.png',
            class:'tags-add',
            hidden:true,
            name:widget.target.name,
            id: 'img' + widget.target.id,
        });

    $(widget.target).parent().fadeOut(function() { $(this).remove(); });
    $('#tr-tags-new table tr').append($('<td class="top-td">').append($('<span>'+ widget.target.name +'</span>'),td1));
    
    $('.tags-add').one('click', function(){
                $(this).parent().fadeOut( function() { $(this).remove(); update_tags();});
                id = parseInt(this.id.split('imgt')[1]);
                tag = {id:id, name:this.name};
                tags.push(tag);    
                showtags();
    });
    
    update_tags();
}

function update_tags(){
    selected = $('img.tags-add');
    str = '';
    for(i= 0 ; i < selected.size(); i++){
        str = str + selected[i].id + ',';
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
                $('#new-tags').append($('<div>').append($('<input>').attr({
                         type: 'checkbox',
                         id: 't' + tags[i].id,
                         name: tags[i].name,
                       })).append($('<label>').text(tags[i].name)));
                  $('#t'+tags[i].id).one('click', addtags);                  
             }
        }
    }
}
