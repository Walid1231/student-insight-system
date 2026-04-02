/**
 * Custom UI Alerts & Confirmations
 * Replaces default browser alert() and confirm()
 */

(function() {
    let toastContainer, modalBackdrop;

    document.addEventListener('DOMContentLoaded', () => {
        // Inject Toast Container
        toastContainer = document.createElement('div');
        toastContainer.id = 'ui-toast-container';
        document.body.appendChild(toastContainer);

        // Inject Modal Backdrop
        modalBackdrop = document.createElement('div');
        modalBackdrop.id = 'ui-modal-backdrop';
        modalBackdrop.innerHTML = `
            <div class="ui-modal" id="ui-modal-box">
                <div class="ui-modal-title" id="ui-modal-title">Confirm</div>
                <div class="ui-modal-text" id="ui-modal-text">Are you sure?</div>
                <div class="ui-modal-actions">
                    <button class="ui-btn ui-btn-cancel" id="ui-modal-cancel">Cancel</button>
                    <button class="ui-btn ui-btn-confirm" id="ui-modal-confirm">Confirm</button>
                </div>
            </div>
        `;
        document.body.appendChild(modalBackdrop);
    });

    // Icon SVG definitions
    const icons = {
        success: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`,
        error: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`,
        warning: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`,
        info: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`
    };

    /**
     * Show a sliding toast notification
     * @param {string} message - The text to display
     * @param {string} type - 'success', 'error', 'warning', or 'info'
     * @param {number} duration - How long before auto-dismiss (ms)
     */
    window.showToast = function(message, type = 'success', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `ui-toast ${type}`;
        
        toast.innerHTML = `
            <div class="ui-toast-icon">${icons[type] || icons.info}</div>
            <div class="ui-toast-content">${message}</div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Trigger animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Removal timeout
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400); // Wait for transition
        }, duration);
    };

    /**
     * Show a glassmorphic confirmation modal
     * @param {string} title - The title of the modal
     * @param {string} message - The descriptive text
     * @param {function} onConfirm - The callback if "Confirm" is clicked
     * @param {string} confirmText - Optional override for confirm button text
     */
    window.showConfirm = function(title, message, onConfirm, confirmText = "Confirm") {
        document.getElementById('ui-modal-title').textContent = title;
        document.getElementById('ui-modal-text').textContent = message;
        document.getElementById('ui-modal-confirm').textContent = confirmText;
        
        const backdrop = document.getElementById('ui-modal-backdrop');
        const cancelBtn = document.getElementById('ui-modal-cancel');
        const confirmBtn = document.getElementById('ui-modal-confirm');
        
        // Remove old listeners to prevent multiple fires
        const newCancelBtn = cancelBtn.cloneNode(true);
        const newConfirmBtn = confirmBtn.cloneNode(true);
        cancelBtn.replaceWith(newCancelBtn);
        confirmBtn.replaceWith(newConfirmBtn);

        function closeModal() {
            backdrop.classList.remove('show');
        }

        newCancelBtn.addEventListener('click', closeModal);
        newConfirmBtn.addEventListener('click', () => {
            closeModal();
            if (typeof onConfirm === 'function') onConfirm();
        });

        backdrop.classList.add('show');
    };
})();
