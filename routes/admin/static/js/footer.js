document.addEventListener('DOMContentLoaded', function() {
    initHeartbeat();
    initScrollTopButton();
    initWavesAnimation();
});

function initHeartbeat() {
    setInterval(function() {
        const heart = document.querySelector('.footer-heart');
        if (heart) {
            heart.classList.add('beat');
            setTimeout(() => {
                heart.classList.remove('beat');
            }, 1000);
        }
    }, 5000);
}

function initWavesAnimation() {
    const waves = document.querySelectorAll('.wave');
    waves.forEach((wave, index) => {
        const randomDuration = 12 + Math.random() * 8;
        const randomDelay = -Math.random() * 5;
        wave.style.animationDuration = `${randomDuration}s`;
        wave.style.animationDelay = `${randomDelay}s`;
    });
}

function initScrollTopButton() {
    const scrollTopBtn = document.createElement('div');
    scrollTopBtn.className = 'scroll-top-btn';
    scrollTopBtn.innerHTML = '<i class="fas fa-arrow-up"></i>';
    document.body.appendChild(scrollTopBtn);
    
    const topNotification = document.getElementById('top-notification');
    let notificationTimeout;
    
    let lastScrollPos = window.pageYOffset;
    let hasScrolled = false;
    
    function checkScrollPosition() {
        const currentScrollPos = window.pageYOffset;
        
        if (currentScrollPos <= 10 && lastScrollPos > 10) {
            if (!topNotification.classList.contains('show')) {
                topNotification.classList.add('show');
                clearTimeout(notificationTimeout);
                notificationTimeout = setTimeout(() => {
                    topNotification.classList.remove('show');
                }, 2000);
            }
        } else {
            topNotification.classList.remove('show');
        }
        
        lastScrollPos = currentScrollPos;
        
        if (!hasScrolled && currentScrollPos > 10) {
            hasScrolled = true;
        }
    }
    
    topNotification.classList.remove('show');
    
    window.addEventListener('scroll', checkScrollPosition);
    
    scrollTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}