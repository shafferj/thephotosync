<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html>
  <head>
    <title>PhotoSync</title>
    <link rel="stylesheet" type="text/css"
          href="http://yui.yahooapis.com/combo?2.6.0/build/reset-fonts/reset-fonts.css" />
    <link rel="stylesheet" type="text/css" href="/style.css" />
    <link rel="icon" type="image/gif" href="/logo16x16.gif" />
    <script type="text/javascript"
            src="http://code.jquery.com/jquery-1.4.4.min.js"></script>
  </head>

  <body>
    <div id="header">
      <div class="container">
        <h1><a href="/">PhotoSync</a></h1>
        % if session.get('user_id'):
        <div id="header-links">
          <a href="/logout">logout</a>
          &middot;
          <a href="/settings">settings</a>
        </div>
        % endif
      </div>
    </div>
    <div id="main" class="container">
      <% messages = h.flash.pop_messages() %>
      % if messages:
      <ul id="flash-messages">
        % for message in messages:
        <li>${message}</li>
        % endfor
      </ul>
      % endif
      ${next.body()}
    </div>
    <div id="footer" class="container">
      &copy; 2010 Paul Carduner and Friends
    </div>
    <div id="fb-root"></div>
    <script src="http://connect.facebook.net/en_US/all.js"></script>
    <script>
      FB.init({appId: "${app_globals.FB_APP_ID}", status: true, cookie: true, xfbml: true});
      FB.Event.subscribe('auth.sessionChange', function(response) {
        if (response.session) {
          console.log("User is loged in");
          // A user has logged in, and a new cookie has been saved
        } else {
          console.log("User is logged out.");
          // The user has logged out, and the cookie has been cleared
        }
      });
    </script>

  </body>
</html>
