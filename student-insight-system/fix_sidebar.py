import os
import glob
import re

for filepath in glob.glob('templates/teacher_*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Look for: <a href="/teacher/alerts" class="nav-item"> or similar, and check if it's missing the span
    # Actually, we can just replace the empty space after <span class="nav-icon"><i data-lucide="bell"></i></span> Alerts
    
    # If the file is dashboard, it uses overview.alerts_count
    badge_html = ""
    if 'teacher_dashboard.html' in filepath:
        if 'overview.alerts_count > 0' not in content:
            badge_html = '{% if overview.alerts_count > 0 %}<span style="margin-left:auto; background:var(--danger, #ef4444); color:white; padding:2px 6px; border-radius:10px; font-size:10px;">{{ overview.alerts_count }}</span>{% endif %}'
    else:
        badge_html = '{% if total_alerts and total_alerts > 0 %}<span style="margin-left:auto; background:var(--sev-critical, #ef4444); color:white; padding:2px 6px; border-radius:10px; font-size:10px;">{{ total_alerts }}</span>{% endif %}'

    if badge_html:
        # Avoid double inserting
        if badge_html not in content:
            # Replaces the anchor text block
            pattern = re.compile(
                r'(<a\s+href="/teacher/alerts"\s+class="nav-item.*?>\s*<span class="nav-icon"><i data-lucide="bell"></i></span>\s*Alerts)(.*?)(</a>)',
                re.DOTALL
            )
            # Remove any empty spaces or newlines that were left behind, and insert the proper badge
            new_content = pattern.sub(r'\1\n                ' + badge_html + r'\n            \3', content)

            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f'Restored badge in {filepath}')
