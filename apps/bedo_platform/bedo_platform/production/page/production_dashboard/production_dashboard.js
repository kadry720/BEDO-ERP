frappe.pages["production-dashboard"].on_page_load = function (wrapper) {
  bedo_platform.render_dashboard_page(wrapper, {
    route: "/app/production-dashboard",
    title: "Production Dashboard",
  });
};
