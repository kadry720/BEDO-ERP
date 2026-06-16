window.bedo_platform = window.bedo_platform || {};

window.bedo_platform.render_admin_users_page = function (wrapper) {
  const escape = frappe.utils.escape_html;
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "BEDO Admin Users",
    single_column: true,
  });
  const body = $(page.body);
  body.html('<div class="bedo-admin-shell"><div class="bedo-loading">Loading users...</div></div>');

  const renderUsers = function (users) {
    if (!users.length) {
      return '<div class="bedo-empty">No users found.</div>';
    }
    return `
      <div class="bedo-user-card-grid">
        ${users
          .map((user) => {
            const fullName = [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username || user.user;
            const roles = (user.roles || [])
              .map((role) => `<span class="bedo-role-chip">${escape(role)}</span>`)
              .join("");
            return `
              <article class="bedo-user-card">
                <div class="bedo-user-card-top">
                  <div class="bedo-user-avatar">${escape((fullName || "U").slice(0, 1).toUpperCase())}</div>
                  <div>
                    <strong>${escape(fullName || "")}</strong>
                    <span>${escape(user.username || user.user || "")}</span>
                  </div>
                  <span class="bedo-account-state ${user.enabled ? "is-enabled" : "is-disabled"}">${user.enabled ? "Enabled" : "Disabled"}</span>
                </div>
                <div class="bedo-user-meta">
                  <span>${escape(user.email || "No email")}</span>
                  <span>${escape(user.phone_number || "No phone")}</span>
                  <span class="bedo-status-pill">${escape(user.primary_department || "Unassigned")}</span>
                </div>
                <div class="bedo-role-chip-row">${roles || '<span class="bedo-role-chip is-empty">No BEDO roles</span>'}</div>
              </article>`;
          })
          .join("")}
      </div>`;
  };

  const render = function (data) {
    const roles = data.roles || [];
    const departments = (data.departments || []).filter((department) => department.dashboard_route);
    const departmentOptions = departments
      .map((department) => `<option value="${department.key}">${escape(department.name)}</option>`)
      .join("");
    const roleOptions = roles
      .map((role) => `<option value="${escape(role)}">${escape(role)}</option>`)
      .join("");

    body.html(`
      <section class="bedo-admin-shell">
        <header class="bedo-dashboard-hero">
          <div>
            <span class="bedo-kicker">Administration</span>
            <h2>BEDO Admin Users</h2>
            <p>User provisioning, access assignment, and account status.</p>
          </div>
          <div class="bedo-hero-status">
            <span>Total users</span>
            <strong>${(data.users || []).length}</strong>
          </div>
        </header>

        <div class="bedo-admin-overview">
          <div class="bedo-admin-card is-primary">
            <span class="bedo-card-kicker">Users</span>
            <strong>${(data.users || []).length}</strong>
            <p>Active and disabled BEDO accounts.</p>
          </div>
          <a class="bedo-admin-card" href="/app/permission-manager">
            <span class="bedo-card-kicker">Permissions</span>
            <strong>Permission Manager</strong>
            <p>Review role permissions and access rules.</p>
          </a>
          <a class="bedo-admin-card" href="/app/user-permission">
            <span class="bedo-card-kicker">User access</span>
            <strong>User Permissions</strong>
            <p>Control document-level user restrictions.</p>
          </a>
          <a class="bedo-admin-card" href="/app/role">
            <span class="bedo-card-kicker">Roles</span>
            <strong>Role Directory</strong>
            <p>Review role records and role profiles.</p>
          </a>
        </div>

        <form class="bedo-admin-form">
          <div class="bedo-panel-header">
            <div>
              <span class="bedo-kicker">BEDO user</span>
              <h3>Create user</h3>
            </div>
          </div>
          <div class="bedo-form-grid">
            <label><span>Username</span><input name="username" autocomplete="off" required /></label>
            <label><span>Password</span><input name="password" autocomplete="new-password" type="password" required /></label>
            <label><span>First name</span><input name="first_name" required /></label>
            <label><span>Last name</span><input name="last_name" required /></label>
            <label><span>Email</span><input name="email" type="email" required /></label>
            <label><span>Phone number</span><input name="phone_number" required /></label>
            <label><span>Primary department</span><select name="primary_department" required>
                <option value="">Select department</option>
                ${departmentOptions}
              </select></label>
            <label class="bedo-field-wide"><span>Roles</span><select name="roles" multiple required>${roleOptions}</select></label>
          </div>
          <button class="btn btn-primary" type="submit">Add user</button>
        </form>
        <div class="bedo-users-list">
          <div class="bedo-panel-header">
            <div>
              <span class="bedo-kicker">Directory</span>
              <h3>Current users</h3>
            </div>
          </div>
          ${renderUsers(data.users || [])}
        </div>
      </section>
    `);

    body.find(".bedo-admin-form").on("submit", function (event) {
      event.preventDefault();
      const form = $(this);
      const payload = {
        username: form.find('[name="username"]').val(),
        password: form.find('[name="password"]').val(),
        first_name: form.find('[name="first_name"]').val(),
        last_name: form.find('[name="last_name"]').val(),
        email: form.find('[name="email"]').val(),
        phone_number: form.find('[name="phone_number"]').val(),
        primary_department: form.find('[name="primary_department"]').val(),
        roles: form.find('[name="roles"]').val() || [],
      };
      frappe.call({
        method: "bedo_platform.api.user_management.create_user_from_admin",
        args: { payload },
        callback: function () {
          frappe.show_alert({ message: "User created", indicator: "green" });
          window.bedo_platform.render_admin_users_page(wrapper);
        },
      });
    });
  };

  frappe.call({
    method: "bedo_platform.api.user_management.get_admin_bootstrap",
    callback: function (response) {
      render(response.message || {});
    },
  });
};
