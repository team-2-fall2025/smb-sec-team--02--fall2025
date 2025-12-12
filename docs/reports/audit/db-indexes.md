## asset_intel_links
- _id_: {'v': 2, 'key': [('_id', 1)]}
- asset_id_1_intel_id_1: {'v': 2, 'key': [('asset_id', 1), ('intel_id', 1)], 'unique': True, 'partialFilterExpression': SON([('asset_id', SON([('$exists', True)])), ('intel_id', SON([('$exists', True)]))])}

## assets
- _id_: {'v': 2, 'key': [('_id', 1)]}
- ip_1: {'v': 2, 'key': [('ip', 1)]}
- hostname_1: {'v': 2, 'key': [('hostname', 1)]}

## audit_logs
- _id_: {'v': 2, 'key': [('_id', 1)]}

## backup_sets
- _id_: {'v': 2, 'key': [('_id', 1)]}
- asset_last_success: {'v': 2, 'key': [('asset_id', 1), ('last_success_at', -1)]}

## control_evidence
- _id_: {'v': 2, 'key': [('_id', 1)]}

## control_mappings
- _id_: {'v': 2, 'key': [('_id', 1)]}

## controls
- _id_: {'v': 2, 'key': [('_id', 1)]}

## detections
- _id_: {'v': 2, 'key': [('_id', 1)]}

## dr_plans
- _id_: {'v': 2, 'key': [('_id', 1)]}
- service: {'v': 2, 'key': [('service_or_group', 1)]}
- tags: {'v': 2, 'key': [('tags', 1)]}

## incident_evidence
- _id_: {'v': 2, 'key': [('_id', 1)]}
- incident_id_1: {'v': 2, 'key': [('incident_id', 1)]}

## incident_tasks
- _id_: {'v': 2, 'key': [('_id', 1)]}
- incident_id_1_order_1: {'v': 2, 'key': [('incident_id', 1), ('order', 1)]}
- incident_id_1_phase_1: {'v': 2, 'key': [('incident_id', 1), ('phase', 1)]}

## incident_timeline
- _id_: {'v': 2, 'key': [('_id', 1)]}
- incident_id_1_ts_1: {'v': 2, 'key': [('incident_id', 1), ('ts', 1)]}

## incidents
- _id_: {'v': 2, 'key': [('_id', 1)]}
- severity_1_status_1: {'v': 2, 'key': [('severity', 1), ('status', 1)]}
- sla_due_at_1: {'v': 2, 'key': [('sla_due_at', 1)]}
- dedup_key.asset_id_1_dedup_key.indicator_1_dedup_key.source_1: {'v': 2, 'key': [('dedup_key.asset_id', 1), ('dedup_key.indicator', 1), ('dedup_key.source', 1)]}

## intel_events
- _id_: {'v': 2, 'key': [('_id', 1)]}

## policies
- _id_: {'v': 2, 'key': [('_id', 1)]}

## policy_assignments
- _id_: {'v': 2, 'key': [('_id', 1)]}

## resilience_findings
- _id_: {'v': 2, 'key': [('_id', 1)]}
- status_severity: {'v': 2, 'key': [('status', 1), ('severity', -1)]}
- type: {'v': 2, 'key': [('type', 1)]}

## restore_tests
- _id_: {'v': 2, 'key': [('_id', 1)]}
- asset_last_test: {'v': 2, 'key': [('asset_id', 1), ('test_completed_at', -1)]}

## risk_register
- _id_: {'v': 2, 'key': [('_id', 1)]}

## sops
- _id_: {'v': 2, 'key': [('_id', 1)]}

## vulnerabilities
- _id_: {'v': 2, 'key': [('_id', 1)]}

