<%inherit file="/base.mako"/>\

<div id="frontpage">


  %if not c.fb_user:
  <div class="step">
    <h1>Step 1:</h1>
    <a class="big-button" href="${c.fb_connect_url}">
      Log in with your Facebook account
    </a>
  </div>
  %endif

  %if c.fb_user:
  <div class="step completed">
    <table>
      <tr>
        <td>
          <img class="profile-pic" src="${c.fb_user.profile_pic_url}" />
          <br />
          <a target="_new" href="${c.fb_user.link}">${c.fb_user.name}</a>
        </td>
        <td>
          Facebook account connected
        </td>
      </tr>
    </table>
  </div>
  %endif

  %if not c.flickr_user:
  <div class="step ${'' if c.fb_user else 'disabled'}">
    <h1>Step 2:</h1>
    <a class="big-button" href="${c.flickr_connect_url}">
      Log in with your Flickr account
    </a>
  </div>
  %endif

  %if c.flickr_user:
  <div class="step completed">
    <table>
      <tr>
        <td>
          <img class="profile-pic" src="${c.flickr_user.profile_pic_url}" />
          <br />
          <a target="_new" href="${c.flickr_user.link}">${c.flickr_user.name}</a>
        </td>
        <td>
          Flickr account connected
        </td>
      </tr>
    </table>
  </div>
  %endif

  <div class="step ${'' if c.flickr_user and c.fb_user else 'disabled'}">
    <h1>Step 3:</h1>
    <a class="big-button" href="${c.sync_url}">
      Start syncing your photos
    </a>
  </div>

</div>
