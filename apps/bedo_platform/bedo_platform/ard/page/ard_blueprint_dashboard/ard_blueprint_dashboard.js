frappe.pages["ard-blueprint-dashboard"].on_page_load = function (wrapper) {
  bedo_platform.render_dashboard_page(wrapper, {
    route: "/app/ard-blueprint-dashboard",
    title: "ARD Blueprint Dashboard",
  });
};
