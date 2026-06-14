frappe.pages["ard-scmdp-dashboard"].on_page_load = function (wrapper) {
  bedo_platform.render_dashboard_page(wrapper, {
    route: "/app/ard-scmdp-dashboard",
    title: "ARD SCMDP Dashboard",
  });
};
