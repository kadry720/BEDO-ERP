window.bedo_platform = window.bedo_platform || {};

window.bedo_platform.render_profile_page = function (wrapper) {
  const escape = frappe.utils.escape_html;
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "My Profile",
    single_column: true,
  });
  const body = $(page.body);
  body.html('<div class="bedo-profile-shell"><div class="bedo-loading">Loading profile...</div></div>');

  const render = function (profile) {
    body.html(`
      <section class="bedo-profile-shell">
        <header class="bedo-profile-hero">
          <div class="bedo-profile-avatar">${escape((profile.first_name || profile.username || "U").slice(0, 1).toUpperCase())}</div>
          <div>
            <span class="bedo-kicker">Account settings</span>
            <h2>My Profile</h2>
            <p>Update your account name and password.</p>
          </div>
        </header>

        <form class="bedo-profile-form">
          <section class="bedo-profile-panel">
            <div class="bedo-panel-header">
              <div>
                <span class="bedo-kicker">User details</span>
                <h3>Name</h3>
              </div>
            </div>
            <div class="bedo-form-grid">
              <label><span>Username</span><input name="username" autocomplete="username" value="${escape(profile.username || "")}" required /></label>
              <label><span>First name</span><input name="first_name" value="${escape(profile.first_name || "")}" required /></label>
              <label><span>Middle name</span><input name="middle_name" value="${escape(profile.middle_name || "")}" /></label>
              <label><span>Last name</span><input name="last_name" value="${escape(profile.last_name || "")}" /></label>
            </div>
          </section>

          <section class="bedo-profile-panel">
            <div class="bedo-panel-header">
              <div>
                <span class="bedo-kicker">Settings</span>
                <h3>Password</h3>
              </div>
            </div>
            <div class="bedo-form-grid">
              <label><span>New password</span><input name="password" autocomplete="new-password" type="password" /></label>
            </div>
          </section>

          <div class="bedo-profile-actions">
            <button class="btn btn-primary" type="submit">Save profile</button>
          </div>
        </form>
      </section>
    `);

    body.find(".bedo-profile-form").on("submit", function (event) {
      event.preventDefault();
      const form = $(this);
      frappe.call({
        method: "bedo_platform.api.profile.update_current_profile",
        args: {
          payload: {
            username: form.find('[name="username"]').val(),
            first_name: form.find('[name="first_name"]').val(),
            middle_name: form.find('[name="middle_name"]').val(),
            last_name: form.find('[name="last_name"]').val(),
            password: form.find('[name="password"]').val(),
          },
        },
        callback: function (response) {
          frappe.show_alert({ message: "Profile updated", indicator: "green" });
          render((response.message || {}).profile || profile);
        },
      });
    });
  };

  frappe.call({
    method: "bedo_platform.api.profile.get_current_profile",
    callback: function (response) {
      render(response.message || {});
    },
  });
};
