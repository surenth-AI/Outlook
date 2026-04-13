document.addEventListener('DOMContentLoaded', () => {
    const emailList = document.getElementById('emailList');
    const refreshBtn = document.getElementById('refreshEmails');

    if (emailList) {
        fetchEmails();
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            emailList.innerHTML = `
                <div class="loader-container">
                    <div class="loader"></div>
                    <p>Refreshing your messages...</p>
                </div>
            `;
            fetchEmails();
        });
    }

    async function fetchEmails() {
        try {
            const response = await fetch('/get_emails');
            if (response.redirected) {
                window.location.href = response.url;
                return;
            }
            
            const data = await response.json();
            renderEmails(data.value || []);
        } catch (error) {
            console.error('Error fetching emails:', error);
            emailList.innerHTML = `
                <div class="error-container">
                    <p>Failed to load emails. Please try again later.</p>
                </div>
            `;
        }
    }

    function renderEmails(emails) {
        if (emails.length === 0) {
            emailList.innerHTML = '<p class="empty-state">No emails found in your inbox.</p>';
            return;
        }

        emailList.innerHTML = emails.map(email => `
            <div class="email-card animate-up">
                <div class="email-sender">
                    <i data-lucide="user" size="16"></i>
                    <span>${email.from?.emailAddress?.name || email.from?.emailAddress?.address || 'Unknown'}</span>
                </div>
                <h3 class="email-subject">${email.subject || '(No Subject)'}</h3>
                <p class="email-preview">${email.bodyPreview || 'No preview available...'}</p>
                <div class="email-footer" style="margin-top: 0.5rem; font-size: 0.8rem; color: #94a3b8;">
                    ${new Date(email.receivedDateTime).toLocaleString()}
                </div>
            </div>
        `).join('');
        
        // Re-initialize icons for new content
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }
});
