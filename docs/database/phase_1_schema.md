# Phase 1 Schema

The Phase 1 schema is implemented with Frappe DocTypes.

## BEDO Department

- `department_code`: Data, required, unique
- `department_name`: Data, required
- `description`: Small Text
- `is_active`: Check
- `parent_department`: Link to BEDO Department

## BEDO User Profile

- `user`: Link to User, required, unique
- `full_name`: Data
- `email`: Data
- `employee_code`: Data
- `department`: Link to BEDO Department
- `job_title`: Data
- `auth_source`: Select, Local or LDAP
- `ldap_username`: Data
- `ldap_dn`: Data
- `is_created_from_ldap`: Check
- `is_active_in_bedo_erp`: Check
- `last_successful_login`: Datetime
- `last_failed_login`: Datetime

## BEDO LDAP Group Role Mapping

- `ldap_group_name`: Data, required
- `ldap_group_dn`: Data
- `frappe_role`: Link to Role, required
- `priority`: Int
- `is_active`: Check

## BEDO Access Audit Log

- `user`: Link to User
- `event_type`: Select
- `auth_source`: Select
- `success`: Check
- `failure_reason`: Small Text
- `ip_address`: Data
- `user_agent`: Small Text
- `session_id`: Data
- `created_at`: Datetime

## BEDO Security Settings

Singleton DocType with LDAP login flags, local login flags, default LDAP role, failed login thresholds, lockout duration, session timeout, active profile requirement, and audit logging switch.
