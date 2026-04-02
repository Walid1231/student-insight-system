import os
import glob
import re

bell_dropdown_html = """
            <div class="header-actions" style="position:relative; margin-left:16px;">
                <button id="transferReqBellBtn" style="background:transparent; border:none; color:var(--text-secondary); cursor:pointer; position:relative; padding:8px; border-radius:50%; display:flex; align-items:center; justify-content:center; transition:background 0.2s;">
                    <i data-lucide="bell" style="width:20px; height:20px;"></i>
                    {% if global_transfer_requests and global_transfer_requests|length > 0 %}
                    <span style="position:absolute; top:2px; right:2px; width:10px; height:10px; background:var(--sev-critical, #ef4444); border-radius:50%; border:2px solid var(--card-bg, #fff);"></span>
                    {% endif %}
                </button>

                <div id="transferReqDropdown" style="display:none; position:absolute; top:45px; right:0; width:340px; background:var(--card-bg, #fff); border:1px solid var(--border, #e5e7eb); border-radius:12px; box-shadow:0 10px 25px rgba(0,0,0,0.1); z-index:100; overflow:hidden;">
                    <div style="padding:12px 16px; border-bottom:1px solid var(--border, #e5e7eb); display:flex; justify-content:space-between; align-items:center; background:var(--bg-secondary, #fafafa);">
                        <h4 style="margin:0; font-size:14px; color:var(--dark, #111827); font-weight:600;">Transfer Requests</h4>
                        <span style="font-size:12px; color:var(--text-secondary, #6b7280);">{% if global_transfer_requests %}{{ global_transfer_requests|length }}{% else %}0{% endif %} pending</span>
                    </div>
                    <div style="max-height:320px; overflow-y:auto; padding:8px;">
                        {% if global_transfer_requests %}
                            {% for req in global_transfer_requests %}
                            <div id="top-req-card-{{ req.id }}" style="padding:12px; border:1px solid var(--border, #e5e7eb); border-radius:8px; margin-bottom:8px; background:var(--card-bg, #fff);">
                                <div style="font-size:13px; font-weight:600; color:var(--dark, #111827); margin-bottom:4px;">{{ req.student.full_name }}</div>
                                <div style="font-size:12px; color:var(--text-secondary, #6b7280); margin-bottom:10px;">Requested by: <strong>{{ req.requester.full_name }}</strong></div>
                                <div style="display:flex; gap:8px;">
                                    <button onclick="resolveTransferRequestGlobal('{{ req.id }}', 'accept', this)" style="flex:1; padding:6px; background:var(--success-color, #10b981); color:white; border:none; border-radius:6px; font-size:12px; font-weight:500; cursor:pointer; display:flex; justify-content:center; align-items:center; gap:4px;">
                                        <i data-lucide="check" style="width:12px;height:12px;"></i> Accept
                                    </button>
                                    <button onclick="resolveTransferRequestGlobal('{{ req.id }}', 'reject', this)" style="flex:1; padding:6px; background:transparent; border:1px solid var(--sev-critical, #ef4444); color:var(--sev-critical, #ef4444); border-radius:6px; font-size:12px; font-weight:500; cursor:pointer; display:flex; justify-content:center; align-items:center; gap:4px;">
                                        <i data-lucide="x" style="width:12px;height:12px;"></i> Decline
                                    </button>
                                </div>
                            </div>
                            {% endfor %}
                        {% else %}
                            <div style="padding:24px 0; text-align:center; color:var(--text-secondary, #6b7280); font-size:13px; display:flex; flex-direction:column; align-items:center; gap:8px;">
                                <i data-lucide="check-circle" style="width:24px; height:24px; opacity:0.5;"></i>
                                No pending requests
                            </div>
                        {% endif %}
                    </div>
                </div>
            </div>
"""

js_logic = """
        // ── Transfer Notification Dropdown ──────────────────────────────
        const transferBtn = document.getElementById('transferReqBellBtn');
        const transferDropdown = document.getElementById('transferReqDropdown');
        if (transferBtn && transferDropdown) {
            transferBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                transferDropdown.style.display = transferDropdown.style.display === 'none' ? 'block' : 'none';
            });
            document.addEventListener('click', (e) => {
                if (!transferBtn.contains(e.target) && !transferDropdown.contains(e.target)) {
                    transferDropdown.style.display = 'none';
                }
            });
        }

        async function resolveTransferRequestGlobal(reqId, action, btn) {
            btn.disabled = true;
            const originalHtml = btn.innerHTML;
            btn.innerHTML = `<i data-lucide="loader-2" class="spinner" style="width:12px;height:12px;"></i>`;
            lucide.createIcons({root: btn.parentElement});
            
            try {
                const res = await fetch('/api/teacher/resolve-request', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                    body: JSON.stringify({ request_id: reqId, action: action })
                });
                const data = await res.json();
                
                if (res.ok && data.success) {
                    if(typeof showToast === 'function') showToast(action === 'accept' ? 'Transfer accepted!' : 'Transfer declined', 'success');
                    const card = document.getElementById(`top-req-card-${reqId}`);
                    if (card) card.remove();
                    
                    // Also attempt to remove from main alerts page if we are on it
                    const alertCard = document.getElementById(`req-card-${reqId}`);
                    if (alertCard) alertCard.remove();
                } else {
                    throw new Error(data.msg || 'Action failed.');
                }
            } catch (e) {
                if(typeof showToast === 'function') showToast(e.message, 'error');
                btn.disabled = false;
                btn.innerHTML = originalHtml;
                lucide.createIcons({root: btn});
            }
        }
"""

for filepath in glob.glob('templates/teacher_*.html'):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Step 1: Remove nav_alerts_count logic
    new_content = re.sub(
        r'{%\s*if\s*nav_alerts_count\s*>\s*0\s*%}.*?{%\s*endif\s*%}',
        '',
        content,
        flags=re.DOTALL
    )

    # Step 2: Inject bell_dropdown into the header div
    # Looks for: `<div class="header">\n            <div>\n                <h1>...</h1>\n                <p>...</p>\n            </div>\n            <div style="display:flex; align-items:center; gap:12px; font-size:14px; color:var(--text-secondary)">\n                {{ now_date }}`
    # Or just find `<div class="header">\n` and inject our block at the end of the flex container?
    # Better: Find `<button class="dm-toggle"` and insert our bell BEFORE it.
    if 'id="transferReqBellBtn"' not in new_content:
        new_content = re.sub(
            r'(<button class="dm-toggle")',
            bell_dropdown_html + r'                \1',
            new_content
        )

    # Step 3: Inject JS Logic near the bottom script
    if 'resolveTransferRequestGlobal' not in new_content:
        # insert before closing script
        new_content = re.sub(
            r'(</script>\n</body>)',
            js_logic + r'\1',
            new_content
        )

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Updated {filepath}')

