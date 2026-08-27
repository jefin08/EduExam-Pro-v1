/**
 * EduExam Pro - Framer Motion Engine & Preloader Initializer
 * Powered by Framer Motion (Motion for JavaScript)
 */

document.addEventListener('DOMContentLoaded', () => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  
  if (typeof Motion === 'undefined') {
    console.warn('Framer Motion library not detected.');
    const preloader = document.getElementById('app-preloader');
    if (preloader) preloader.style.display = 'none';
    return;
  }

  const { animate, inView, stagger } = Motion;

  // ==========================================================================
  // 1. Framer Motion Preloader & Entrance Animation Routine
  // ==========================================================================
  const preloaderEl = document.getElementById('app-preloader');
  const progressBar = document.getElementById('preloader-progress');
  const statusText = document.getElementById('preloader-status');

  const runPreloader = () => {
    if (!preloaderEl) {
      triggerHeroEntrance();
      return;
    }

    if (prefersReducedMotion) {
      preloaderEl.style.display = 'none';
      triggerHeroEntrance();
      return;
    }

    // Pulse preloader stamp with spring physics
    const stampEl = preloaderEl.querySelector('.preloader-stamp');
    if (stampEl) {
      animate(stampEl, { scale: [0.9, 1.1, 1], rotate: [-8, -4, -6] }, { duration: 0.8, easing: 'ease-out' });
    }

    // Progress bar fill animation
    let progress = 0;
    const statusMessages = [
      'Loading Question Bank Engine...',
      'Setting Up Code Sandbox Containers...',
      'Verifying Role Integrity Rules...',
      'Environment Ready!'
    ];

    const progressInterval = setInterval(() => {
      progress += Math.floor(Math.random() * 25) + 15;

      if (progress > 100) progress = 100;
      if (progressBar) progressBar.style.width = `${progress}%`;

      if (statusText) {
        if (progress < 35) statusText.textContent = statusMessages[0];
        else if (progress < 70) statusText.textContent = statusMessages[1];
        else if (progress < 95) statusText.textContent = statusMessages[2];
        else statusText.textContent = statusMessages[3];
      }

      if (progress >= 100) {
        clearInterval(progressInterval);

        // Smooth exit animation for preloader
        setTimeout(() => {
          if (preloaderEl) {
            preloaderEl.style.pointerEvents = 'none';
            try {
              animate(
                preloaderEl,
                { opacity: [1, 0], scale: [1, 1.04] },
                { duration: 0.5, easing: [0.22, 1, 0.36, 1] }
              );
            } catch (e) {
              console.warn('Preloader fade animation fallback:', e);
            }

            setTimeout(() => {
              preloaderEl.style.display = 'none';
              triggerHeroEntrance();
              triggerDashboardEntrance();
            }, 450);
          }
        }, 200);
      }
    }, 120);
  };

  // ==========================================================================
  // 2. Landing Page Hero Staggered Reveal Sequence
  // ==========================================================================
  const triggerHeroEntrance = () => {
    if (prefersReducedMotion) return;

    // Header bar slide down
    const header = document.querySelector('header');
    if (header) {
      animate(header, { opacity: [0, 1], y: [-25, 0] }, { duration: 0.5, easing: 'ease-out' });
    }

    // 1. Hero Eyebrow tracking expand & slide down
    const eyebrow = document.getElementById('hero-eyebrow');
    if (eyebrow) {
      animate(eyebrow, { opacity: [0, 1], y: [-20, 0] }, { duration: 0.5, easing: 'ease-out' });
    }

    // 2. Hero Title 3D perspective rise
    const title = document.getElementById('hero-title');
    if (title) {
      animate(
        title,
        { opacity: [0, 1], y: [35, 0] },
        { duration: 0.7, easing: [0.22, 1, 0.36, 1] }
      );
    }

    // 3. Trigger red underline stroke draw animation
    setTimeout(() => {
      const highlight = document.querySelector('.underline-highlight');
      if (highlight) highlight.classList.add('drawn');
    }, 450);

    // 4. Hero Lead paragraph blur-to-sharp focus reveal
    const lead = document.getElementById('hero-lead');
    if (lead) {
      animate(
        lead,
        { opacity: [0, 1], y: [20, 0], filter: ['blur(6px)', 'blur(0px)'] },
        { duration: 0.65, delay: 0.25, easing: 'ease-out' }
      );
    }

    // 5. CTA Buttons spring scale pop-in
    const buttons = document.querySelectorAll('.hero-ctas .btn');
    if (buttons.length > 0) {
      animate(
        buttons,
        { opacity: [0, 1], scale: [0.85, 1.04, 1], y: [15, 0] },
        { delay: stagger(0.12, { startDelay: 0.35 }), duration: 0.5, easing: [0.34, 1.56, 0.64, 1] }
      );
    }

    // 6. Hero Visual Side-by-Side Cards (Exam Sheet + Coding Sandbox)
    const examCard = document.getElementById('card-exam-sheet');
    if (examCard) {
      animate(
        examCard,
        { opacity: [0, 1], x: [-60, 0], scale: [0.92, 1] },
        { delay: 0.4, duration: 0.75, easing: [0.34, 1.56, 0.64, 1] }
      );

      // Paperclip spring wiggle onto exam sheet
      const paperclip = examCard.querySelector('.clip');
      if (paperclip) {
        animate(
          paperclip,
          { opacity: [0, 1], scale: [0.5, 1.15, 1], rotate: [-35, -10, -15] },
          { delay: 0.6, duration: 0.5, easing: [0.34, 1.56, 0.64, 1] }
        );
      }

      // Inner MCQ options stagger reveal
      const mcqOptions = examCard.querySelectorAll('.mcq-option');
      if (mcqOptions.length > 0) {
        animate(
          mcqOptions,
          { opacity: [0, 1], y: [15, 0] },
          { delay: stagger(0.08, { startDelay: 0.65 }), duration: 0.45, easing: 'ease-out' }
        );
      }
    }

    const sandboxCard = document.getElementById('card-sandbox-console');
    if (sandboxCard) {
      animate(
        sandboxCard,
        { opacity: [0, 1], x: [60, 0], scale: [0.92, 1] },
        { delay: 0.55, duration: 0.75, easing: [0.34, 1.56, 0.64, 1] }
      );
    }
  };

  // ==========================================================================
  // Interactive 3D Cursor Tilt Physics for Hero Cards & Two Modes Cards
  // ==========================================================================
  if (!prefersReducedMotion) {
    const tiltCardsList = document.querySelectorAll('.hero-visual .card, .modes-grid .card');
    tiltCardsList.forEach(card => {
      card.style.transformStyle = 'preserve-3d';
      card.style.transition = 'transform 0.15s ease-out, box-shadow 0.15s ease-out';

      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = ((y - centerY) / centerY) * -7;
        const rotateY = ((x - centerX) / centerX) * 7;

        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.018, 1.018, 1.018)`;
        card.style.boxShadow = `${-rotateY * 1.5}px ${rotateX * 1.5 + 8}px 20px rgba(29, 39, 51, 0.12)`;
      });

      card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
        card.style.boxShadow = '2px 2px 0px rgba(29, 39, 51, 0.08)';
      });
    });
  }

  // ==========================================================================
  // 3. Dashboard Page Entrance Routine
  // ==========================================================================
  const triggerDashboardEntrance = () => {
    if (prefersReducedMotion) return;

    const statCards = document.querySelectorAll('.stat-card');
    if (statCards.length > 0) {
      animate(
        statCards,
        { opacity: [0, 1], y: [25, 0], scale: [0.95, 1] },
        { delay: stagger(0.08), duration: 0.5, easing: [0.22, 1, 0.36, 1] }
      );
    }

    const sidebarItems = document.querySelectorAll('.sidebar-menu li');
    if (sidebarItems.length > 0) {
      animate(
        sidebarItems,
        { opacity: [0, 1], x: [-20, 0] },
        { delay: stagger(0.05), duration: 0.4, easing: 'ease-out' }
      );
    }
  };

  // Run preloader sequence on load
  runPreloader();

  // ==========================================================================
  // 4. Section-by-Section Framer Motion Fallback (if GSAP isn't loaded)
  // ==========================================================================
  if (!prefersReducedMotion && typeof gsap === 'undefined') {
    // Modes Section (#modes)
    const modesSection = document.getElementById('modes');
    if (modesSection) {
      inView(modesSection, () => {
        const title = modesSection.querySelector('.section-header');
        if (title) animate(title, { opacity: [0, 1], y: [30, 0] }, { duration: 0.5 });

        const cards = modesSection.querySelectorAll('.mode-column');
        if (cards.length > 0) {
          animate(
            cards,
            { opacity: [0, 1], y: [40, 0], scale: [0.95, 1] },
            { delay: stagger(0.15), duration: 0.6, easing: [0.34, 1.56, 0.64, 1] }
          );
        }
      });
    }
  }

  // ==========================================================================
  // 5. Global Interactive Spring Micro-Interactions
  // ==========================================================================
  if (!prefersReducedMotion) {
    const interactiveElements = document.querySelectorAll(
      '.btn, .stat-card, .card, .action-card, .sidebar-menu li a, .roll-row, .judge-feature-item, .tally-cell'
    );

    interactiveElements.forEach(el => {
      el.addEventListener('mouseenter', () => {
        animate(el, { scale: 1.025, y: -3 }, { duration: 0.2, easing: [0.34, 1.56, 0.64, 1] });
      });

      el.addEventListener('mouseleave', () => {
        animate(el, { scale: 1, y: 0 }, { duration: 0.2, easing: 'ease-out' });
      });

      el.addEventListener('mousedown', () => {
        animate(el, { scale: 0.96 }, { duration: 0.1, easing: 'ease-out' });
      });

      el.addEventListener('mouseup', () => {
        animate(el, { scale: 1.025 }, { duration: 0.15, easing: [0.34, 1.56, 0.64, 1] });
      });
    });
  }
});
