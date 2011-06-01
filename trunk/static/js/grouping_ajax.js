$(
    function(){
        $('.top-td').live('mouseenter', function(){$(this).children(':hidden').show();})
        $('.top-td').live('mouseleave', function(){$(this).children('img').hide();});
    }
)

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
