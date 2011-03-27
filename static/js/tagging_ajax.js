function addtags(widget){    
    tags = $.grep(tags, function(tag){ return tag.name != widget.target.name});
    
    $.ajax({
        url: '/msghandler/default/insert_ajax_msg_tag',
        data: 'group=' + this.id  + '&id=' + msg_id
        })             
    
    td1 = $('<img>').attr({
            src:'/msghandler/static/images/delete.png',
            class:'tags-add',
            hidden:true,
            id: 'img' + widget.target.id,
            name: widget.target.name,
        });

    $(widget.target).parent().fadeOut(function() { $(this).remove(); });
    $('#tr-tags-new table tr').append($('<td class="top-td">').append($('<span>'+ widget.target.name +'</span>'),td1));
    
    $('.tags-add').unbind();
    click_once_tag();    
}

function click_once_tag(){
    $('.tags-add').one('click', function(){
        $(this).parent().fadeOut( function() { $(this).remove();});
        id = parseInt(this.id.split('imgt')[1]);
        tag = {id:id, name:this.name};
        tags.push(tag);    
        $.ajax({
            url: '/msghandler/default/delete_ajax_msg_tag',
            data: 'group=' + this.id  + '&id=' + msg_id
        })             
        showtags();
    });

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
