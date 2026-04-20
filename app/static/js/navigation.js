// Global navigation fix for all dashboards

// Logout function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        // Direct navigation to logout - simpler approach
        window.location.href = '/auth/logout';
    }
}

// Navigation function
function navigateTo(url) {
    window.location.href = url;
}

// Fix all navigation links
document.addEventListener('DOMContentLoaded', function() {
    console.log('Navigation script loaded');
    
    // Reset cursor behavior
    document.body.style.cursor = 'default';
    
    // Only handle logout buttons specifically - don't interfere with other links
    const logoutButtons = document.querySelectorAll('[onclick*="logout"], a[onclick*="logout"]');
    console.log('Found logout buttons:', logoutButtons.length);
    logoutButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Logout button clicked');
            logout();
        });
    });
    
    // Add hover effects to all buttons
    const buttons = document.querySelectorAll('.btn, .btn-modern, .btn-hero');
    console.log('Found buttons for hover effects:', buttons.length);
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px) scale(1.05)';
            this.style.cursor = 'pointer';
        });
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
            this.style.cursor = 'default';
        });
    });
    
    // Fix cursor on page unload
    window.addEventListener('beforeunload', function() {
        document.body.style.cursor = 'default';
    });
    
    // Fix cursor on page load
    setTimeout(function() {
        document.body.style.cursor = 'default';
    }, 100);
    
    console.log('Navigation script initialized');
});

// Export functions for global use
window.logout = logout;
window.navigateTo = navigateTo;
