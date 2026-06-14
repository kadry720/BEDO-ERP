frappe.pages["command-center-dashboard"].on_page_load = function (wrapper) {
  bedo_platform.render_dashboard_page(wrapper, {
    route: "/app/command-center-dashboard",
    title: "Command Center Dashboard",
  });
};
