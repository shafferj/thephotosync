<%inherit file="/base.mako"/>\
<%namespace file="/widgets/task.mako" name="t"/>
<%namespace file="/widgets/box.mako" name="box"/>
<%namespace file="/widgets/progressbar.mako" name="p"/>

%if c.tasks:
<%box:box title="Status">
%if c.current_task:
  %if c.current_task.percentComplete is None:
    ${p.progress_bar(0, "Starting...")}
  %else:
    ${p.progress_bar(c.current_task.percentComplete, c.current_task.status_data)}
  %endif
%else:
  %if c.next_task:
    <div>
      next sync in
      <strong>
        ${h.distance_of_time_in_words(c.next_task.time_left, granularity='minute')}
      </strong>
      <a href="/sync/full_sync">sync now</a>
    </div>
  %endif
  %if c.last_task:
    <div>
    last sync completed
    %if c.last_task.end_time:
      ${h.time_ago_in_words(c.last_task.end_time, granularity='minute')}
      ago
    %else:
      ${c.last_task.queue_id}
    %endif
    </div>
  %endif
%endif
</%box:box>
%endif

<%box:box title="Connected Accounts">
  <table>
    <tr>
      <td>
        Facebook Account:
      </td>
      <td>
        <strong>${c.fbuser.first_name} ${c.fbuser.last_name}</strong>
      </td>
    </tr>
    <tr>
      <td>
        Flickr Account:
      </td>
      <td>
        %if c.flickr_user:
        <strong>${c.flickr_user.username}</strong>
        %else:
        <a href="${c.flickr_connect_url}">Connect</a>
        %endif
      </td>
    </tr>
    <tr>
      <td>
        Picassa:
      </td>
      <td>
        %if c.picasa_user:
        <strong>Connected!</strong>
        %else:
        <a href="${c.picasa_connect_url}">Connect</a>
        %endif
      </td>
    </tr>
  </table>
  <%def name="buttons()">
    <a class="button" href="/sync/long_ping?seconds=5">Ping</a>
    <a class="button" href="/sync/full_sync">Sync</a>
  </%def>
</%box:box>
