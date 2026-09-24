/**
 * FindBack Navigation & Responsive Sidebar Handler
 */
document.addEventListener('DOMContentLoaded', () => {
    // Mobile navigation toggle on landing page
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', () => {
            const isExpanded = mobileMenuToggle.getAttribute('aria-expanded') === 'true';
            mobileMenuToggle.setAttribute('aria-expanded', !isExpanded);
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Mobile sidebar drawer in dashboard & application pages
    const mobileSidebarToggle = document.getElementById('mobile-sidebar-toggle');
    const mobileSidebarDrawer = document.getElementById('mobile-sidebar-drawer');

    if (mobileSidebarToggle && mobileSidebarDrawer) {
        mobileSidebarToggle.addEventListener('click', () => {
            mobileSidebarDrawer.classList.toggle('hidden');
        });
    }

    // Highlight current active sidebar link based on current path
    const currentPath = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('[data-sidebar-link]');

    sidebarLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && (currentPath.includes(href) || (href === '/' && currentPath === '/'))) {
            link.classList.add('active');
        }
    });
});
