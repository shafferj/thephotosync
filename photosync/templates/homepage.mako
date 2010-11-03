<%inherit file="/base.mako"/>\
<%namespace file="/widgets/task.mako" name="t"/>
<%namespace file="/widgets/box.mako" name="box"/>


% if c.tasks:
<%box:box title="Status">
  % for task in c.tasks:
      ${t.task(task)}
  % endfor
</%box:box>
% endif

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
        % if c.flickr_user:
        <strong>${c.flickr_user.username}</strong>
        % else:
        <a href="${c.flickr_connect_url}">Connect</a>
        % endif
      </td>
    </tr>
    <tr>
      <td>
        Picassa:
      </td>
      <td>
        Not implemented yet :(
      </td>
    </tr>
  </table>
  <%def name="buttons()">
    <a class="button" href="/sync/long_ping?seconds=30">Sync</a>
  </%def>
</%box:box>
