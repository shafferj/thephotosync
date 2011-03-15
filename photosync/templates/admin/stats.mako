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
      <th>Id</th>
      <th>User</th>
      <th>Sync Records</th>
      <th>MB In</th>
      <th>MB Out</th>
      <th>Cost</th>
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
      <td></td>
      <td></td>
      <td>${c.total_tin}MB</td>
      <td>${c.total_tout}MB</td>
      <td>$${c.total_cost}</td>
    </tr>
  </table>
</div>
