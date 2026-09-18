document.addEventListener('DOMContentLoaded', () => {
    const mainHeader = document.getElementById('main-header');
    const navCollapse = document.getElementById('findbackNav');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link, .btn-fb-primary, .btn-fb-ghost');

    if (mainHeader) {
        const handleScroll = () => {
            if (window.scrollY > 20) {
                mainHeader.classList.add('scrolled');
            } else {
                mainHeader.classList.remove('scrolled');
            }
        };

        handleScroll();
        window.addEventListener('scroll', handleScroll, { passive: true });
    }

    if (navCollapse && window.bootstrap) {
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                const bsCollapse = bootstrap.Collapse.getInstance(navCollapse);
                if (bsCollapse && navCollapse.classList.contains('show')) {
                    bsCollapse.hide();
                }
            });
        });

        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const bsCollapse = bootstrap.Collapse.getInstance(navCollapse);
                if (bsCollapse && navCollapse.classList.contains('show')) {
                    bsCollapse.hide();
                }
            }
        });
    }
});
