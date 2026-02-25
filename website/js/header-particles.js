/**
 * Header particle animation — floating dots that echo the scatter plot theme
 */
(function () {
    'use strict';

    const PARTICLE_COUNT = 28;
    const COLORS = [
        'rgba(255,255,255,0.35)',
        'rgba(255,255,255,0.2)',
        'rgba(171,221,164,0.3)',   // cluster green
        'rgba(50,136,189,0.3)',    // cluster blue
        'rgba(254,224,139,0.25)',  // cluster yellow
    ];

    const canvas = document.getElementById('header-particles');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let particles = [];
    let animId;

    function resize() {
        const header = canvas.parentElement;
        canvas.width = header.offsetWidth;
        canvas.height = header.offsetHeight;
    }

    function createParticles() {
        particles = [];
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                r: Math.random() * 2.2 + 0.8,
                dx: (Math.random() - 0.5) * 0.4,
                dy: (Math.random() - 0.5) * 0.25,
                color: COLORS[Math.floor(Math.random() * COLORS.length)],
            });
        }
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        for (const p of particles) {
            p.x += p.dx;
            p.y += p.dy;

            // Wrap around edges
            if (p.x < -4) p.x = canvas.width + 4;
            if (p.x > canvas.width + 4) p.x = -4;
            if (p.y < -4) p.y = canvas.height + 4;
            if (p.y > canvas.height + 4) p.y = -4;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.fill();
        }

        animId = requestAnimationFrame(draw);
    }

    function init() {
        resize();
        createParticles();
        draw();
    }

    window.addEventListener('resize', () => {
        resize();
        createParticles();
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
