import glob

js_logic = """
<!-- Transfer Accept logic -->
<script>
async function resolveTransferRequestGlobal(reqId, action, btn) {
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i data-lucide="loader-2" class="spinner" style="width:14px;height:14px;"></i> Processing';
        if(typeof lucide !== 'undefined') lucide.createIcons();
    }
    try {
        const res = await fetch('/api/teacher/resolve-request', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_id: reqId, action: action })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            // Remove from Bell
            const card = document.getElementById('top-req-card-' + reqId);
            if (card) card.remove();
            
            // Remove from inline page Tables if any
            const row = document.getElementById('req-row-' + reqId);
            if (row) row.remove();

            if (typeof showToast === 'function') {
                showToast('Transfer request ' + action + 'ed!', 'success');
            } else {
                alert('Transfer request ' + action + 'ed successfully!');
            }
            
            setTimeout(() => window.location.reload(), 800);
        } else {
            if (typeof showToast === 'function') {
                showToast(data.msg || 'Action failed.', 'error');
            } else {
                alert(data.msg || 'Action failed.');
            }
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = action === 'accept' ? 'Accept' : 'Decline';
            }
        }
    } catch (e) {
        console.error(e);
        if (typeof showToast === 'function') showToast('Network error.', 'error');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = action === 'accept' ? 'Accept' : 'Decline';
        }
    }
}
</script>
"""

for f in glob.glob('templates/teacher_*.html'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    if 'async function resolveTransferRequestGlobal' not in content:
        new_content = content.replace('</body>', js_logic + '\n</body>')
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Added resolveTransferRequestGlobal to {f}')
