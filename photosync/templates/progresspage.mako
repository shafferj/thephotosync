<%inherit file="/base.mako"/>\

<%def name="header()">Progress</%def>

${c.progressbar}

<script type="text/javascript">
  window.setTimeout(function(){ window.location.reload(true); }, 1000);
</script>