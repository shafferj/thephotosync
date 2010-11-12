<%namespace file="/widgets/progressbar.mako" import="*"/>
<%def name="task(task)">

% if task.time_left:
next sync in ${h.distance_of_time_in_words(task.time_left)}
% elif task.end_time:
<div>
  Completed on ${task.end_time.strftime('%x')} at ${task.end_time.strftime('%X')}
</div>

% else:
  % if task.percentComplete is None:
    ${progress_bar(0, "Starting...")}
  % else:
    ${progress_bar(task.percentComplete, task.status_data)}
    ${task.end_time}
  % endif
% endif
</%def>
