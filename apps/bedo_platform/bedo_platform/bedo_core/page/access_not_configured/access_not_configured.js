frappe.pages["access-not-configured"].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: "Access Not Configured",
    single_column: true,
  });
  $(page.body).html(
    '<section class="bedo-dashboard-shell"><div class="bedo-dashboard-panel">Access is not configured for this account. Contact a BEDO administrator.</div></section>'
  );
};
