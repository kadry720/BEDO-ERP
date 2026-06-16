(function () {
  const hiddenWorkspaces = new Set(["Website", "Tools", "Integrations", "Build"]);
  const hiddenUserMenuItems = new Set(["My Settings", "Session Defaults", "Reload", "View Website", "Apps"]);

  const normalizeText = function (value) {
    return (value || "").replace(/\s+/g, " ").trim();
  };

  const routeTo = function (route) {
    if (route.startsWith("/app/")) {
      window.location.href = route;
      return;
    }
    frappe.set_route(route);
  };

  const isUsersWorkspace = function () {
    const route = frappe.get_route ? frappe.get_route() : [];
    const routeText = route.join("/").toLowerCase();
    const title = normalizeText($(".page-title .title-text, .page-head .title-text, h3").first().text());
    return title === "Users" && (routeText.includes("users") || window.location.pathname.endsWith("/users"));
  };

  const hideWorkspaceSidebarItems = function () {
    $(".standard-sidebar-item, .desk-sidebar a, .layout-side-section a").each(function () {
      const item = $(this);
      const label = normalizeText(item.find(".sidebar-item-label, .item-label").first().text() || item.text());
      if (hiddenWorkspaces.has(label)) {
        item.closest(".standard-sidebar-item, li, a").hide();
      }
    });
  };

  const cleanupNavbar = function () {
    $('[aria-label="Help Dropdown"], [aria-controls="toolbar-help"]').closest(".nav-item, .dropdown, li, .navbar-item").hide();

    $(".navbar .dropdown-toggle, .navbar button, .navbar a").each(function () {
      const item = $(this);
      const label = normalizeText(item.text());
      if (label === "Help") {
        item.closest(".nav-item, .dropdown, li").hide();
      }
    });

    $(".dropdown-menu a, .dropdown-menu button, .dropdown-menu .dropdown-item").each(function () {
      const item = $(this);
      const label = normalizeText(item.text());
      if (hiddenUserMenuItems.has(label)) {
        item.hide();
      }
      if (label === "My Profile") {
        item.attr("href", "/app/bedo-profile");
      }
    });
  };

  const renderUsersWorkspace = function () {
    if (!isUsersWorkspace()) return;
    const main = $(".layout-main-section").first();
    if (!main.length || main.attr("data-bedo-users-workspace") === "1") return;

    main.attr("data-bedo-users-workspace", "1");
    main.html(`
      <section class="bedo-users-workspace">
        <header class="bedo-users-hero">
          <div>
            <span class="bedo-kicker">Administration</span>
            <h2>Users</h2>
            <p>Manage accounts, roles, permissions, and security logs from one organized workspace.</p>
          </div>
          <a class="btn btn-primary" href="/app/bedo-admin-users">Open BEDO Admin Users</a>
        </header>

        <div class="bedo-admin-overview">
          <a class="bedo-admin-card is-primary" href="/app/bedo-admin-users">
            <span class="bedo-card-kicker">Directory</span>
            <strong>BEDO Admin Users</strong>
            <p>Create BEDO users, assign departments, and maintain BEDO roles.</p>
          </a>
          <a class="bedo-admin-card" href="/app/user">
            <span class="bedo-card-kicker">Accounts</span>
            <strong>User Directory</strong>
            <p>Review Frappe user records and account status.</p>
          </a>
          <a class="bedo-admin-card" href="/app/role">
            <span class="bedo-card-kicker">Access model</span>
            <strong>Roles</strong>
            <p>Review platform roles and role profiles.</p>
          </a>
          <a class="bedo-admin-card" href="/app/permission-manager">
            <span class="bedo-card-kicker">Permissions</span>
            <strong>Permission Manager</strong>
            <p>Control document access and permission rules.</p>
          </a>
        </div>

        <div class="bedo-admin-sections">
          <section class="bedo-admin-section">
            <div class="bedo-panel-header">
              <div>
                <span class="bedo-kicker">Users</span>
                <h3>Account setup</h3>
              </div>
            </div>
            <div class="bedo-admin-link-grid">
              <a href="/app/user">User</a>
              <a href="/app/role">Role</a>
              <a href="/app/role-profile">Role Profile</a>
              <a href="/app/module-profile">Module Profile</a>
              <a href="/app/user-type">User Type</a>
              <a href="/app/bedo-profile">My Profile</a>
            </div>
          </section>

          <section class="bedo-admin-section">
            <div class="bedo-panel-header">
              <div>
                <span class="bedo-kicker">Logs</span>
                <h3>Security review</h3>
              </div>
            </div>
            <div class="bedo-admin-link-grid">
              <a href="/app/activity-log">Activity Log</a>
              <a href="/app/access-log">Access Log</a>
            </div>
          </section>

          <section class="bedo-admin-section">
            <div class="bedo-panel-header">
              <div>
                <span class="bedo-kicker">Permissions</span>
                <h3>Access control</h3>
              </div>
            </div>
            <div class="bedo-admin-link-grid">
              <a href="/app/permission-manager">Role Permissions Manager</a>
              <a href="/app/user-permission">User Permissions</a>
              <a href="/app/role-permission-for-page-and-report">Role Permission for Page and Report</a>
              <a href="/app/query-report/Permitted%20Documents%20For%20User">Permitted Documents For User</a>
              <a href="/app/query-report/Document%20Share%20Report">Document Share Report</a>
            </div>
          </section>
        </div>
      </section>
    `);
  };

  const cleanupUserForm = function () {
    const route = frappe.get_route ? frappe.get_route() : [];
    const isUserForm = route[0] === "Form" && route[1] === "User";
    $("body").toggleClass("bedo-user-form-clean", isUserForm);
    if (!isUserForm) return;

    const docname = route[2] || "";
    if (frappe.session.user !== "Administrator" && docname && docname !== frappe.session.user) {
      frappe.set_route("bedo-profile");
      return;
    }

    $(".page-actions .btn, .page-actions .btn-group, .page-actions .icon-btn").each(function () {
      const item = $(this);
      const label = normalizeText(item.text());
      if (
        ["Permissions", "Password", "Create User Email"].includes(label) ||
        item.hasClass("prev-doc") ||
        item.hasClass("next-doc")
      ) {
        item.hide();
      }
    });
    $(".prev-doc, .next-doc, .menu-btn-group, .form-sidebar .add-assignment-btn, .form-sidebar .add-attachment-btn").hide();
    $('[data-fieldname="enabled"], [data-fieldname="email"], [data-fieldname="language"], [data-fieldname="time_zone"]').hide();
    $(".form-tabs .nav-link, .form-tabs a").each(function () {
      const tab = $(this);
      const label = normalizeText(tab.text());
      if (label && !["User Details", "Settings"].includes(label)) {
        tab.closest("li, .nav-item").hide();
      }
    });
  };

  const applyDeskCustomizations = frappe.utils.debounce(function () {
    hideWorkspaceSidebarItems();
    cleanupNavbar();
    renderUsersWorkspace();
    cleanupUserForm();
  }, 100);

  $(document).on("click", ".dropdown-menu a, .dropdown-menu button, .dropdown-menu .dropdown-item", function (event) {
    const label = normalizeText($(this).text());
    if (label === "My Profile") {
      event.preventDefault();
      routeTo("bedo-profile");
    }
    if (hiddenUserMenuItems.has(label)) {
      event.preventDefault();
      return false;
    }
  });

  if (frappe.router && frappe.router.on) {
    frappe.router.on("change", applyDeskCustomizations);
  }

  $(document).on("shown.bs.dropdown page-change", applyDeskCustomizations);
  const observer = new MutationObserver(applyDeskCustomizations);
  observer.observe(document.body, { childList: true, subtree: true });
  frappe.after_ajax(applyDeskCustomizations);
  $(applyDeskCustomizations);
})();
