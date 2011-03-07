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
        <td class="flickr">
          <a target="_new" href="${c.flickr_user.link}">
            <img class="profile-pic" src="${c.flickr_user.profile_pic_url}" />
            <br />
            <img class="icon" src="/flickr-icon.gif"/>
            ${c.flickr_user.name}
          </a>
        </td>
        <td class="arrow">
          ➞
        </td>
        <td class="facebook">
          <a target="_new" href="${c.fb_user.link}">
            <img class="profile-pic" src="${c.fb_user.profile_pic_url}" />
            <br />
            <img class="icon" src="/facebook-icon.gif"/>
            ${c.fb_user.name}
          </a>
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
      ${p.progress_bar(0, c.current_task.status_data)}
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

    <div class="account-stats">
      You've transfered ${round(c.bytes_transferred, 2)} MB at a cost of
      $${round(c.cost, 3)}
    </div>

  %endif
</div>
%endif
