window.bedo_platform = window.bedo_platform || {};

window.bedo_platform.render_dashboard_page = function (wrapper, options) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: options.title || "BEDO",
    single_column: true,
  });

  const body = $(page.body);
  body.html('<div class="bedo-dashboard-shell"><div class="bedo-loading">Loading...</div></div>');

  frappe.call({
    method: "bedo_platform.api.routing.ensure_dashboard_access",
    args: { route: options.route },
    callback: function (response) {
      const data = response.message || {};
      const links = data.visible_dashboards || [];
      page.set_title(data.title || options.title || "BEDO");
      const linkHtml = links
        .filter((item) => item.route !== options.route)
        .map(
          (item) =>
            `<a class="bedo-dashboard-link" href="${frappe.utils.escape_html(item.route)}">${frappe.utils.escape_html(item.title)}</a>`
        )
        .join("");
      body.html(`
        <section class="bedo-dashboard-shell">
          <div class="bedo-page-heading">
            <h2>${frappe.utils.escape_html(data.title || options.title || "BEDO")}</h2>
            <p>${frappe.utils.escape_html(data.content || options.content || "Placeholder")}</p>
          </div>
          <div class="bedo-dashboard-panel">
            <div class="bedo-placeholder">${frappe.utils.escape_html(data.content || options.content || "Placeholder")}</div>
          </div>
          ${linkHtml ? `<nav class="bedo-dashboard-links">${linkHtml}</nav>` : ""}
        </section>
      `);
    },
    error: function () {
      frappe.set_route("access-not-configured");
    },
  });
};
