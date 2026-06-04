frappe.pages["qc-dashboard"].on_page_load = function (wrapper) {
  bedo_platform.render_dashboard_page(wrapper, {
    route: "/app/qc-dashboard",
    title: "QC Dashboard",
  });
};
