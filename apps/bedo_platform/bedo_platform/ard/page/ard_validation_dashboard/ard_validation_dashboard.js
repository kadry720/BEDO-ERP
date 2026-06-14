frappe.pages["ard-validation-dashboard"].on_page_load = function (wrapper) {
  bedo_platform.render_dashboard_page(wrapper, {
    route: "/app/ard-validation-dashboard",
    title: "ARD Validation Dashboard",
  });
};
