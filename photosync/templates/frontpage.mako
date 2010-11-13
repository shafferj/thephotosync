<%inherit file="/base.mako"/>\

<%def name="header()">Welcome to PhotoSync!</%def>

<div id="login">
  <a id="login-link" href="${c.fb_connect_url}">Log in with your Facebook account</a>
</div>