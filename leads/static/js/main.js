// Função para lazy loading
const lazyloadRunObserver = () => {
    const lazyloadBackgrounds = document.querySelectorAll(`.e-con.e-parent:not(.e-lazyloaded)`);
    const lazyloadBackgroundObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                let lazyloadBackground = entry.target;
                if (lazyloadBackground) {
                    lazyloadBackground.classList.add('e-lazyloaded');
                }
                lazyloadBackgroundObserver.unobserve(entry.target);
            }
        });
    }, { rootMargin: '200px 0px 200px 0px' });
    
    lazyloadBackgrounds.forEach((lazyloadBackground) => {
        lazyloadBackgroundObserver.observe(lazyloadBackground);
    });
};

// Eventos para inicializar o lazy loading
const events = [
    'DOMContentLoaded',
    'elementor/lazyload/observe',
];

events.forEach((event) => {
    document.addEventListener(event, lazyloadRunObserver);
});

// Menu mobile
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.querySelector('.elementor-menu-toggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            const dropdownMenu = document.querySelector('.elementor-nav-menu--dropdown');
            if (dropdownMenu) {
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                this.setAttribute('aria-expanded', !isExpanded);
                dropdownMenu.style.display = isExpanded ? 'none' : 'block';
            }
        });
    }
});

// Inicializa animações quando elementos entram na viewport
function initAnimations() {
    const animatedElements = document.querySelectorAll('.elementor-invisible');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('elementor-animation-fadeInUp');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    animatedElements.forEach(element => {
        observer.observe(element);
    });
}

document.addEventListener('DOMContentLoaded', initAnimations);