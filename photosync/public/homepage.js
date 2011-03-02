
var UPDATE_TIME = 1000;

function update() {
  $.getJSON('/sync/status', function(task) {
    if (!task) {
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