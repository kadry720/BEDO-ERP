window.bedo_platform = window.bedo_platform || {};

window.bedo_platform.render_admin_users_page = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "BEDO Admin Users",
    single_column: true,
  });
  const body = $(page.body);
  body.html('<div class="bedo-admin-shell"><div class="bedo-loading">Loading...</div></div>');

  const renderUsers = function (users) {
    if (!users.length) {
      return '<div class="bedo-empty">No users found.</div>';
    }
    return `
      <table class="bedo-user-table">
        <thead>
          <tr>
            <th>Username</th><th>Name</th><th>Email</th><th>Phone</th><th>Department</th><th>Roles</th><th>Status</th>
          </tr>
        </thead>
        <tbody>
          ${users
            .map(
              (user) => `
                <tr>
                  <td>${frappe.utils.escape_html(user.username || user.user || "")}</td>
                  <td>${frappe.utils.escape_html([user.first_name, user.last_name].filter(Boolean).join(" "))}</td>
                  <td>${frappe.utils.escape_html(user.email || "")}</td>
                  <td>${frappe.utils.escape_html(user.phone_number || "")}</td>
                  <td>${frappe.utils.escape_html(user.primary_department || "")}</td>
                  <td>${frappe.utils.escape_html((user.roles || []).join(", "))}</td>
                  <td>${user.enabled ? "Enabled" : "Disabled"}</td>
                </tr>`
            )
            .join("")}
        </tbody>
      </table>`;
  };

  const render = function (data) {
    const roles = data.roles || [];
    const departments = (data.departments || []).filter((department) => department.dashboard_route);
    const departmentOptions = departments
      .map((department) => `<option value="${department.key}">${frappe.utils.escape_html(department.name)}</option>`)
      .join("");
    const roleOptions = roles
      .map((role) => `<option value="${frappe.utils.escape_html(role)}">${frappe.utils.escape_html(role)}</option>`)
      .join("");

    body.html(`
      <section class="bedo-admin-shell">
        <form class="bedo-admin-form">
          <div class="bedo-form-grid">
            <input name="username" autocomplete="off" placeholder="Username" required />
            <input name="password" autocomplete="new-password" placeholder="LDAP password" type="password" required />
            <input name="first_name" placeholder="First name" required />
            <input name="last_name" placeholder="Last name" required />
            <input name="email" placeholder="Email" type="email" required />
            <input name="phone_number" placeholder="Phone number" required />
            <select name="primary_department" required>
              <option value="">Primary department</option>
              ${departmentOptions}
            </select>
            <select name="roles" multiple required>${roleOptions}</select>
          </div>
          <button class="btn btn-primary" type="submit">Add user</button>
        </form>
        <div class="bedo-users-list">${renderUsers(data.users || [])}</div>
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
