<%def name="progress_bar(percentComplete, message)">
<div class="progressbar">
  <div class="message">
    ${message}
  </div>
  <div class="bar">
    <div class="progress" style="width: ${percentComplete}%">
    </div>
  </div>
</div>
</%def>
