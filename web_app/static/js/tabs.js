document.addEventListener('DOMContentLoaded', function() {
    const tabsContainer = document.querySelector('.tabs-container');
    const tabs = tabsContainer?.querySelector('.tabs');
    const scrollLeftBtn = tabsContainer?.querySelector('.scroll-button.left');
    const scrollRightBtn = tabsContainer?.querySelector('.scroll-button.right');

    if (!tabs || !scrollLeftBtn || !scrollRightBtn) return;

    // Function to update button states based on scroll position
    function updateScrollButtons() {
        const { scrollLeft, scrollWidth, clientWidth } = tabs;
        
        // Show/hide left button
        if (scrollLeft === 0) {
            scrollLeftBtn.setAttribute('disabled', 'true');
        } else {
            scrollLeftBtn.removeAttribute('disabled');
        }
        
        // Show/hide right button
        if (Math.ceil(scrollLeft + clientWidth) >= scrollWidth) {
            scrollRightBtn.setAttribute('disabled', 'true');
        } else {
            scrollRightBtn.removeAttribute('disabled');
        }
    }

    // Initial state
    updateScrollButtons();

    // Handle scroll events
    tabs.addEventListener('scroll', updateScrollButtons);

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(updateScrollButtons, 100);
    });

    // Scroll left button click handler
    scrollLeftBtn.addEventListener('click', () => {
        tabs.scrollBy({
            left: -200, // Adjust scroll amount as needed
            behavior: 'smooth'
        });
    });

    // Scroll right button click handler
    scrollRightBtn.addEventListener('click', () => {
        tabs.scrollBy({
            left: 200, // Adjust scroll amount as needed
            behavior: 'smooth'
        });
    });

    // Handle keyboard navigation
    tabs.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') {
            tabs.scrollBy({ left: -100, behavior: 'smooth' });
        } else if (e.key === 'ArrowRight') {
            tabs.scrollBy({ left: 100, behavior: 'smooth' });
        }
    });
});
