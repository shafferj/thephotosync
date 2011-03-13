<%inherit file="/base.mako"/>
<div class="error">
  ${c.error_message}
</div>
<div id="error-page" class="error">
  <p>
    Oh snap! There was a problem.
  </p>
  <p>
    If this keeps happening, please email
    <a href="mailto:${app_globals.HELP_EMAIL}">${app_globals.HELP_EMAIL}</a>
    with a description of what you were doing when the error occurred.
  </p>
</div>
