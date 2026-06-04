frappe.pages["ard-coordination-dashboard"].on_page_load = function (wrapper) {
  bedo_platform.render_dashboard_page(wrapper, {
    route: "/app/ard-coordination-dashboard",
    title: "ARD Coordination Dashboard",
  });
};
