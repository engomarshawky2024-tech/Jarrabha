/**
 * Jarrabha Global UI Logic - Premium Orbital System
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mouse Glow Effect with Smoothing (Performance Optimized)
    const glow = document.getElementById('mouseGlow');
    let mouseX = 0, mouseY = 0;
    let ballX = 0, ballY = 0;
    const speed = 0.08; // Smoothness factor

    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });

    function animateGlow() {
        let distX = mouseX - ballX;
        let distY = mouseY - ballY;
        ballX = ballX + (distX * speed);
        ballY = ballY + (distY * speed);
        
        if (glow) {
            glow.style.left = ballX + 'px';
            glow.style.top = ballY + 'px';
        }
        requestAnimationFrame(animateGlow);
    }
    animateGlow();

    // 2. Intersection Observer for Scroll Reveals & Counters
    const observerOptions = {
        threshold: 0.15,
        rootMargin: '0px 0px -50px 0px'
    };

    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                
                // If this is a component with counters, trigger them
                const counters = entry.target.querySelectorAll('.counter-val');
                if (counters.length > 0) {
                    counters.forEach(counter => animateCounter(counter));
                }
            }
        });
    }, observerOptions);

    document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

    // 3. Counter Animation Logic
    function animateCounter(el) {
        if (el.classList.contains('counted')) return;
        el.classList.add('counted');

        const target = parseInt(el.getAttribute('data-target')) || 0;
        const duration = 2500; // 2.5 seconds for premium feel
        const frameRate = 1000 / 60; // 60fps
        const totalFrames = duration / frameRate;
        const increment = target / totalFrames;
        let current = 0;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                el.innerText = target.toLocaleString();
                clearInterval(timer);
            } else {
                el.innerText = Math.floor(current).toLocaleString();
            }
        }, frameRate);
    }

    // 4. Staggered Logo Entrance Reset
    const logoLetters = document.querySelectorAll('.logo-anim span');
    logoLetters.forEach((letter, index) => {
        letter.style.opacity = '0';
        letter.style.transform = 'translateY(15px)';
        setTimeout(() => {
            letter.style.opacity = '1';
            letter.style.transform = 'translateY(0)';
            letter.style.transition = 'all 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
        }, 300 + (index * 60));
    });

    // 5. Navbar Dynamic Sizing
    const nav = document.querySelector('.glass-nav');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 80) {
            nav.style.padding = '0.6rem 2rem';
            nav.style.width = '92%';
            nav.style.background = 'rgba(2, 6, 23, 0.85)';
        } else {
            nav.style.padding = '0.75rem 2.5rem';
            nav.style.width = '90%';
            nav.style.background = 'rgba(15, 23, 42, 0.6)';
        }
    });

    // 6. Chat Badge Update (Global)
    updateChatBadge();
    setInterval(updateChatBadge, 30000); // Check every 30 seconds
});

/**
 * Fetches the unread message count from the server
 */
function updateChatBadge() {
    const badge = document.getElementById('globalChatBadge');
    if (!badge) return;

    fetch('/chat/unread_count')
        .then(response => response.json())
        .then(data => {
            if (data.count > 0) {
                badge.innerText = data.count > 99 ? '99+' : data.count;
                badge.style.display = 'block';
                badge.classList.add('animate-pulse');
            } else {
                badge.style.display = 'none';
            }
        })
        .catch(err => console.error('Error fetching chat count:', err));
}
