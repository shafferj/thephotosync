<%inherit file="/base.mako"/>\
<%namespace file="/widgets/box.mako" name="box"/>


<form method="POST" action="/settings/save">
<%box:box title="Settings">
  <div class="row">
    <label>Facebook Privacy:</label>
    ${h.select('fb_privacy', c.fb_privacy_setting, c.fb_privacy_options)}
  </div>
  <%def name="buttons()">
    ${h.submit('save', 'Save')}
  </%def>
</%box:box>
</form>
