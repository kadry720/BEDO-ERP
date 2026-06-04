from __future__ import annotations

from bedo_platform.setup import seed_dashboards, seed_departments, seed_initial_users, seed_roles, site_state


def execute() -> None:
    site_state.mark_setup_complete()
    seed_departments.execute()
    seed_roles.execute()
    seed_dashboards.execute()
    seed_initial_users.execute(strict=False)
