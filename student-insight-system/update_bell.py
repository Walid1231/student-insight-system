import glob
import re

new_html = '''                                <div style="font-size:13px; font-weight:600; color:var(--dark, #111827); margin-bottom:2px;">{{ req.student.full_name }}</div>
                                <div style="font-size:11px; color:var(--text-secondary, #6b7280); margin-bottom:6px; display: flex; align-items: center; gap: 4px;">
                                    <i data-lucide="hash" style="width:10px;height:10px;"></i>
                                    {{ req.student.student_code or 'Unknown ID' }} &bull; {{ req.student.department or 'General' }}
                                </div>
                                <div style="font-size:12px; color:var(--text-secondary, #4b5563); margin-bottom:10px; line-height: 1.4;">
                                    <strong>{{ req.requester.full_name }}</strong> has requested to formally transfer this student into their classroom.
                                </div>'''

# Regex to match the existing block, being flexible with whitespace/newlines
pattern = re.compile(
    r'<div style="font-size:13px; color:var\(--dark, #111827\); margin-bottom:10px; line-height: 1\.4;">\s*<strong>\{\{\s*req\.requester\.full_name\s*\}\}</strong> is requesting <strong>\{\{\s*req\.student\.full_name\s*\}\}</strong>\.\s*</div>',
    re.DOTALL
)

for f in glob.glob('templates/teacher_*.html'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if '{{ req.student.student_code' not in content:
        new_content, count = pattern.subn(new_html, content)
        if count > 0:
            with open(f, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f'Updated {f} ({count} replacements)')
