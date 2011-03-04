<%inherit file="/base.mako"/>
<%namespace file="/widgets/box.mako" name="box"/>


<form method="POST" action="/settings/save">
<%box:box title="Settings">

  <div class="row">
    <label>Facebook Privacy:</label>
    ${h.select('fb_privacy', c.fb_privacy_setting, c.fb_privacy_options)}
  </div>

  <div class="row">
    ${h.checkbox('select_sets', value=1, checked=c.select_sets, label="Only sync the flickr sets I choose")}
  </div>

  <div id="flickr_set_list" class="row ${'' if c.select_sets else 'hidden'}">
    <label>Choose the sets you want to sync:</label>
    <ul>
    % for set in c.all_sets:
      <li>
      ${h.checkbox('selected_sets', value=set['id'], checked=set['checked'], label=set['title'])}
      </li>
    % endfor
    </ul>
  </div>

  <%def name="buttons()">
    ${h.submit('save', 'Save')}
  </%def>
</%box:box>
</form>

<script type="text/javascript" src="/settings.js"></script>
