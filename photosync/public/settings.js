$(document).ready(function(){
  $("#select_sets").change(function() {
    console.log($(this).is(':checked'));
    $("#flickr_set_list").toggleClass('hidden', !$(this).is(':checked'));
  });
});
