<%inherit file="/base.mako"/>\
<%namespace file="/widgets/task.mako" name="t"/>
<%namespace file="/widgets/box.mako" name="box"/>
<%namespace file="/widgets/progressbar.mako" name="p"/>

<script type="text/javascript">
  $("#settings-link").click(
    function() {
      $("#settings").fadeToggle('fast');
    });
</script>

%if c.tasks:

<div id="status-box">
  <div class="profiles">
    <table>
      <tr>
        <td>
          <img class="profile-pic" src="${c.flickr_user.profile_pic_url}" />
          <br />
          <a target="_new" href="${c.flickr_user.link}">${c.flickr_user.name}</a>
        </td>
        <td class="arrow">
          ➞
        </td>
        <td>
          <img class="profile-pic" src="${c.fb_user.profile_pic_url}" />
          <br />
          <a target="_new" href="${c.fb_user.link}">${c.fb_user.name}</a>
        </td>
      </tr>
    </table>
  </div>



%if c.current_task:

  %if c.current_task.is_buried:
    <div class="error">
      I've been having a hard time syncing your photos and decided to give up
      for the time being.  You might try
      <a href="${c.sync_url}">kicking me</a>, but no guarantees I'll
      start working again.
    </div>
  %else:

    <script src="/homepage.js"></script>

  %endif


  %if c.current_task.percentComplete is None:
    ${p.progress_bar(0, "Starting...")}
  %else:
    ${p.progress_bar(c.current_task.percentComplete, c.current_task.status_data)}
    <div class="stats">
      ${c.current_task.completed_units}/${c.current_task.total_units}
    </div>
  %endif

%else:
  <div class="last-update">

  %if c.next_task:
    <div>
      <span class="time-left">
        ${h.distance_of_time_in_words(c.next_task.time_left, granularity='minute')}
        left
      </span>
      until next sync
    </div>
    <a class="sync-now" href="${c.sync_url}">sync now</a>
  %endif

  %if c.last_task:
    <div class="time-since-last-sync">
    last sync finished
    %if c.last_task.end_time:
      ${h.time_ago_in_words(c.last_task.end_time, granularity='minute')}
      ago
    %else:
      ${c.last_task.queue_id}
    %endif
    </div>
  %endif

  </div>

%endif
</div>
%endif

<div id="settings" style="${'display:none;' if c.tasks else ''}">
  <table>
    <tr>
      <td>
        Facebook Account:
      </td>
      <td>
        <strong>${c.fb_user.first_name} ${c.fb_user.last_name}</strong>
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
      <td></td>
      <td class="buttons">
        <a class="button" onclick="$('#settings').fadeToggle();">Ok</a>
      </td>
      </tr>
  </table>
</div>
