frappe.pages["srs-dashboard"].on_page_load = function (wrapper) {
  bedo_platform.render_dashboard_page(wrapper, {
    route: "/app/srs-dashboard",
    title: "SRS Dashboard",
  });
};
