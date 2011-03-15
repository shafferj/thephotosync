<%inherit file="/admin/base.mako"/>

<div id="admin-stats">
  <ul>
    <li>Users: ${c.user_count}</li>
    <li>Syncs: ${c.sync_count}</li>
    <li>AsyncTasks: ${c.async_tasks_count}</li>
  </ul>


  <h3>Top Users</h3>
  <table>
    <tr>
      <th><a href="${url('admin-stats', order_by=0)}">Id</a></th>
      <th><a href="${url('admin-stats', order_by=0)}">User</a></th>
      <th><a href="${url('admin-stats', order_by=1)}">Sync Records</a></th>
      <th><a href="${url('admin-stats', order_by=2)}">MB In</a></th>
      <th><a href="${url('admin-stats', order_by=3)}">MB Out</a></th>
      <th><a href="${url('admin-stats', order_by=4)}">Cost</a></th>
    </tr>
    %for user, count, tin, tout, cost in c.user_stats:
    <tr>
      <td>
        <a href="http://www.facebook.com/profile.php?id=${user.fb_uid}">
          ${user.id}
        </a>
      </td>
      <td>
        <a href="http://www.facebook.com/profile.php?id=${user.fb_uid}">
          <img src="http://graph.facebook.com/${user.fb_uid}/picture"/>
        </a>
      </td>
      <td>${count}</td>
      <td>${tin}MB</td>
      <td>${tout}MB</td>
      <td>$${cost}</td>
    </tr>
    %endfor
    <tr>
      <td>Totals:</td>
      <td>${len(c.user_stats)}</td>
      <td>${c.total_count}</td>
      <td>${c.total_tin}MB</td>
      <td>${c.total_tout}MB</td>
      <td>$${c.total_cost}</td>
    </tr>
  </table>
</div>
