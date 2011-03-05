<%inherit file="/admin/base.mako"/>

<ul>
  <li>Users: ${c.user_count}</li>
  <li>Syncs: ${c.sync_count}</li>
  <li>AsyncTasks: ${c.async_tasks_count}</li>
</ul>
