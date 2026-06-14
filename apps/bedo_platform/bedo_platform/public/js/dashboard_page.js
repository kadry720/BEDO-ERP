window.bedo_platform = window.bedo_platform || {};

window.bedo_platform.render_dashboard_page = function (wrapper, options) {
  const escape = frappe.utils.escape_html;
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: options.title || "BEDO",
    single_column: true,
  });

  const body = $(page.body);
  body.html('<div class="bedo-dashboard-shell"><div class="bedo-loading">Loading workspace...</div></div>');

  frappe.call({
    method: "bedo_platform.api.routing.ensure_dashboard_access",
    args: { route: options.route },
    callback: function (response) {
      const data = response.message || {};
      const links = data.visible_dashboards || [];
      page.set_title(data.title || options.title || "BEDO");

      const dashboardCards = links
        .filter((item) => item.route !== options.route)
        .map(
          (item) =>
            `<a class="bedo-dashboard-link" href="${escape(item.route)}">
              <span class="bedo-link-module">${escape(item.module || "BEDO")}</span>
              <strong>${escape(item.title)}</strong>
              <span>${escape(item.content || "Ready")}</span>
            </a>`
        )
        .join("");

      const title = data.title || options.title || "BEDO";
      const content = data.content || options.content || "Workspace ready";
      body.html(`
        <section class="bedo-dashboard-shell">
          <header class="bedo-dashboard-hero">
            <div>
              <span class="bedo-kicker">BEDO Platform</span>
              <h2>${escape(title)}</h2>
              <p>${escape(content)}</p>
            </div>
            <div class="bedo-hero-status">
              <span>Access verified</span>
              <strong>${escape(frappe.session.user || "")}</strong>
            </div>
          </header>

          <div class="bedo-metric-grid">
            <div class="bedo-metric">
              <span>Workspace state</span>
              <strong>Ready</strong>
            </div>
            <div class="bedo-metric">
              <span>Department access</span>
              <strong>${links.length}</strong>
            </div>
            <div class="bedo-metric">
              <span>Phase</span>
              <strong>Foundation</strong>
            </div>
          </div>

          <div class="bedo-dashboard-panel">
            <div class="bedo-panel-header">
              <div>
                <span class="bedo-kicker">Current workspace</span>
                <h3>${escape(title)}</h3>
              </div>
              <span class="bedo-status-pill">No active workflow records</span>
            </div>
            <div class="bedo-empty-state">
              <strong>${escape(content)}</strong>
              <span>Workflow objects are intentionally empty in this phase.</span>
            </div>
          </div>
          ${dashboardCards ? `<nav class="bedo-dashboard-links">${dashboardCards}</nav>` : ""}
        </section>
      `);
    },
    error: function () {
      frappe.set_route("access-not-configured");
    },
  });
};
