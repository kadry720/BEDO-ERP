frappe.pages["bedo-admin-dashboard"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "BEDO Admin Dashboard",
    single_column: true,
  });

  frappe.require([], () => {
    $(page.body).html(
      '<div class="p-4">BEDO Admin Dashboard Placeholder - UI owned by Zeinab</div>'
    );
  });
};
