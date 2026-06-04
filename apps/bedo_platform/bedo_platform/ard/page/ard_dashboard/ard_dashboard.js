frappe.pages["ard-dashboard"].on_page_load = function (wrapper) {
  bedo_platform.render_dashboard_page(wrapper, {
    route: "/app/ard-dashboard",
    title: "ARD Main Dashboard",
  });
};
