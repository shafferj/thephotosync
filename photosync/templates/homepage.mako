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
          <strong>${c.fbuser.first_name} ${c.fbuser.last_name}</strong>
        </td>
      </tr>
    </table>
  </div>
</div>
