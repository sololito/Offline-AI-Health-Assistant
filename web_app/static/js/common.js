// Common JavaScript functions for the application

// Initialize common functionality when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Common JavaScript loaded');
    
    // Initialize tooltips if using Bootstrap
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Add any other common initialization code here
});
