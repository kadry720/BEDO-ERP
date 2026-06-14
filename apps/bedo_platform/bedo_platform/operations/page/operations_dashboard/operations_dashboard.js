frappe.pages["operations-dashboard"].on_page_load = function (wrapper) {
  bedo_platform.render_dashboard_page(wrapper, {
    route: "/app/operations-dashboard",
    title: "Operations Dashboard",
  });
};
