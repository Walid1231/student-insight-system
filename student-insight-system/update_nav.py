import os
import glob
import re

for filepath in glob.glob('templates/teacher_*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_content = re.sub(
        r'<a href="/teacher/alerts" class="nav-item(?P<active>.*?)">\s*<span class="nav-icon"><i data-lucide="bell"></i></span> Alerts(?:\s*{%\s*if\s+total_alerts\s*>\s*0\s*%}\s*<span id="navAlertBadge"[^>]*>{{ total_alerts }}</span>\s*{%\s*endif\s*%})?',
        r'<a href="/teacher/alerts" class="nav-item\g<active>">\n                <span class="nav-icon"><i data-lucide="bell"></i></span> Alerts\n                {% if nav_alerts_count > 0 %}\n                <span id="navAlertBadge" style="margin-left:auto; background:var(--sev-critical, #ef4444); color:white; padding:2px 6px; border-radius:10px; font-size:10px;">{{ nav_alerts_count }}</span>\n                {% endif %}',
        content,
        flags=re.DOTALL
    )
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Updated {filepath}')
