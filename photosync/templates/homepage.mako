<%inherit file="/base.mako"/>\


<div class="box">
  <h1>Connected Accounts</h1>
  <div class="box-content">
    <table>
      <tr>
        <td>
          Facebook Account:
        </td>
        <td>
          <strong>${c.fbuser.first_name} ${c.fbuser.last_name}</strong>
          &middot;
          <a href="${url('fb_albums')}">details</a>
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
  </div>
  <div class="box-buttons">
    <a class="button" href="${url('sync')}">Sync</a>
  </div>
</div>
