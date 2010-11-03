<%def name="box(title)">
<div class="box">
  <h1>${title}</h1>
  <div class="box-content">
    ${caller.body()}
  </div>
  % if hasattr(caller, 'buttons'):
  <div class="box-buttons">
    ${caller.buttons()}
  </div>
  % endif
</div>
</%def>
