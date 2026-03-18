import re

with open('dashboard/teacher_routes_current.py', 'r', encoding='utf-8') as f:
    current = f.read()

with open('dashboard/teacher_routes.py', 'r', encoding='utf-8') as f:
    old = f.read()

# 1. teacher_alerts_page
m1_curr = re.search(r"@teacher_bp\.route\('/teacher/alerts'\).*?def teacher_alerts_page\(\):.*?return render_template\('teacher_alerts\.html'.*?\)", current, re.DOTALL)
alerts_page_curr = m1_curr.group(0)

# 2. api_teacher_resolve_alert
m2_curr = re.search(r"@teacher_bp\.route\('/api/teacher/alerts/<int:alert_id>/resolve', methods=\['POST'\]\).*?def api_teacher_resolve_alert\(alert_id\):.*?return jsonify\(\{.*?\}\)", current, re.DOTALL)
resolve_alert_curr = m2_curr.group(0)

# 3. New endpoints
m3_curr = re.search(r"@teacher_bp\.route\('/api/teacher/alerts/summary', methods=\['GET'\]\).*?def api_teacher_alerts_summary\(\):.*?return jsonify\(\{.*?\}\)", current, re.DOTALL)
alerts_summary_curr = m3_curr.group(0)

m4_curr = re.search(r"@teacher_bp\.route\('/api/teacher/alerts/resolve-batch', methods=\['POST'\]\).*?def api_teacher_resolve_alerts_bulk\(\):.*?return jsonify\(\{.*?\}\)", current, re.DOTALL)
resolve_bulk_curr = m4_curr.group(0)

# Replace in old
old = re.sub(r"@teacher_bp\.route\('/teacher/alerts'\).*?def teacher_alerts_page\(\):.*?return render_template\('teacher_alerts\.html'.*?\)", alerts_page_curr, old, flags=re.DOTALL)

old = re.sub(r"@teacher_bp\.route\('/api/teacher/alerts/<int:alert_id>/resolve', methods=\['POST'\]\).*?def api_teacher_resolve_alert\(alert_id\):.*?return jsonify\(\{.*?\}\)", resolve_alert_curr, old, flags=re.DOTALL)

# Insert new endpoints after api_teacher_resolve_alert
if resolve_alert_curr in old:
    insert_pos = old.find(resolve_alert_curr) + len(resolve_alert_curr)
    old = old[:insert_pos] + '\n\n' + alerts_summary_curr + '\n\n' + resolve_bulk_curr + old[insert_pos:]
else:
    print("Could not find insertion point!")

with open('dashboard/teacher_routes.py', 'w', encoding='utf-8') as f:
    f.write(old)

print('Success')
