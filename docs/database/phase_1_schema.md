# Phase 1 Schema

The Phase 1 schema is implemented with Frappe DocTypes.

## BEDO Department

- `department_key`: Data, required, unique
- `department_name`: Data, required
- `pillar_number`: Int
- `dashboard_route`: Data
- `is_active`: Check
- `is_global_access_department`: Check

## BEDO Role Catalog

- `role_key`: Data, required, unique
- `role_name`: Data, required
- `frappe_role`: Link to Role, required
- `department`: Link to BEDO Department
- `role_category`: Select
- `is_managerial`: Check
- `is_active`: Check
- `description`: Small Text

## BEDO User Role Assignment

- `user`: Link to User, required
- `department`: Link to BEDO Department
- `role_catalog`: Link to BEDO Role Catalog, required
- `is_primary_department`: Check
- `is_active`: Check

## BEDO Module Access

- `department`: Link to BEDO Department, required
- `dashboard_route`: Data, required
- `allowed_role`: Link to Role
- `is_active`: Check

## BEDO Security Event

- `event_type`: Data, required
- `username`: Data
- `user`: Link to User
- `status`: Select
- `ip_address`: Data
- `user_agent`: Data
- `message`: Small Text
- `created_at`: Datetime
