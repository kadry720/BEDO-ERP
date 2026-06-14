frappe.pages["gm-support-dashboard"].on_page_load = function (wrapper) {
  bedo_platform.render_dashboard_page(wrapper, {
    route: "/app/gm-support-dashboard",
    title: "GM Support Office Dashboard",
  });
};
