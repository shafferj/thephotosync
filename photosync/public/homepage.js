
var UPDATE_TIME = 1000;

function update() {
  $.getJSON('/sync/status', function(task) {
    if (!task) {
      $('#status-box').find('.progress').animate({
          width: '100%'
        }, {
          duration: 600,
          complete: function() {
            $('#status-box').find('.message').html("...all done");
            window.location.reload();
          }
        }).end();
      return;
    }
    $('#status-box')
      .find('.progress').width(task.completed_units/task.total_units*100+'%').end()
      .find('.message').html(task.status_data).end()
      .find('.stats').html(task.completed_units+'/'+task.total_units).end();
    window.setTimeout(update, UPDATE_TIME);
  });
}


$(document).ready(function(){
  window.setTimeout(update, UPDATE_TIME);
});