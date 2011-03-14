<%inherit file="/admin/base.mako"/>

<ul>
  <li>Users: ${c.user_count}</li>
  <li>Syncs: ${c.sync_count}</li>
  <li>AsyncTasks: ${c.async_tasks_count}</li>
</ul>


<h3>Top Users</h3>
<table>
  <tr>
    <th>User</th>
    <th>MB In</th>
    <th>MB Out</th>
    <th>Cost</th>
  </tr>
  %for user, tin, tout, cost in c.user_stats:
  <tr>
    <td><img src="http://graph.facebook.com/${user.fb_uid}/picture"/></td>
    <td>${tin}MB</td>
    <td>${tout}MB</td>
    <td>$${cost}</td>
  </tr>
  %endfor
  <tr>
    <td>Totals:</td>
    <td>${c.total_tin}MB</td>
    <td>${c.total_tout}MB</td>
    <td>$${c.total_cost}</td>
  </tr>
</table>
