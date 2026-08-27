document.addEventListener('DOMContentLoaded', () => {
  // Check for reduced motion settings
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 1. Live Countdown Timer
  const timerEl = document.getElementById('hero-timer');
  if (timerEl) {
    let totalSeconds = 1 * 3600 + 29 * 60 + 59; // 01:29:59

    function updateTimer() {
      const hrs = Math.floor(totalSeconds / 3600);
      const mins = Math.floor((totalSeconds % 3600) / 60);
      const secs = totalSeconds % 60;

      timerEl.textContent = [
        String(hrs).padStart(2, '0'),
        String(mins).padStart(2, '0'),
        String(secs).padStart(2, '0')
      ].join(':');

      if (totalSeconds > 1 * 3600 + 29 * 60) {
        totalSeconds--;
      } else {
        totalSeconds = 1 * 3600 + 29 * 60 + 59; // Loop back for demo
      }
    }

    if (!prefersReducedMotion) {
      setInterval(updateTimer, 1000);
    }
  }

  // 2. Interactive MCQ Circle Select with Framer Motion spring physics
  const mcqOptions = document.querySelectorAll('.mcq-option');
  mcqOptions.forEach(option => {
    option.addEventListener('click', () => {
      // Clear previously selected
      mcqOptions.forEach(opt => {
        opt.classList.remove('circled');
        opt.classList.remove('correct');
      });

      // Mark this one as selected/correct
      option.classList.add('correct');
      // Force repaint before adding circle animation class
      void option.offsetWidth;
      option.classList.add('circled');

      // Framer Motion spring feedback punch on selection
      if (typeof Motion !== 'undefined' && !prefersReducedMotion) {
        Motion.animate(option, { scale: [0.95, 1.03, 1] }, { duration: 0.35, easing: [0.34, 1.56, 0.64, 1] });
      }
    });
  });

  // 3. Staggered Console Log Reveal & Grade Seal with Framer Motion
  const consoleBody = document.getElementById('judge-console');
  if (consoleBody) {
    const lines = consoleBody.querySelectorAll('.console-line');
    const stamp = consoleBody.querySelector('.stamp-grade');

    let lineIndex = 0;

    function revealConsole() {
      // Reset console state
      lines.forEach(line => line.classList.remove('visible'));
      if (stamp) stamp.classList.remove('revealed');
      lineIndex = 0;

      function showNextLine() {
        if (lineIndex < lines.length) {
          lines[lineIndex].classList.add('visible');
          if (typeof Motion !== 'undefined' && !prefersReducedMotion) {
            Motion.animate(lines[lineIndex], { opacity: [0, 1], x: [-10, 0] }, { duration: 0.3 });
          }
          lineIndex++;
          setTimeout(showNextLine, prefersReducedMotion ? 50 : 800);
        } else {
          // Reveal the A+ grade stamp at the end with Framer Motion spring bounce
          if (stamp) {
            setTimeout(() => {
              stamp.classList.add('revealed');
              if (typeof Motion !== 'undefined' && !prefersReducedMotion) {
                Motion.animate(stamp, { scale: [0.3, 1.25, 1], rotate: [-15, -5] }, { duration: 0.5, easing: [0.34, 1.56, 0.64, 1] });
              }
            }, 500);
          }
          // Loop console again after some idle time
          setTimeout(revealConsole, 5000);
        }
      }

      // Start the reveal chain
      setTimeout(showNextLine, 500);
    }

    // Run terminal animation
    revealConsole();
  }

  // 4. Scroll Reveal via Intersection Observer & Framer Motion
  const sections = document.querySelectorAll('section');
  if (sections.length > 0) {
    if (prefersReducedMotion) {
      sections.forEach(sec => sec.classList.add('revealed'));
    } else {
      const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
            if (typeof Motion !== 'undefined') {
              Motion.animate(entry.target, { opacity: [0, 1], y: [30, 0] }, { duration: 0.6, easing: [0.22, 1, 0.36, 1] });
            }
            observer.unobserve(entry.target);
          }
        });
      }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
      });

      sections.forEach(sec => revealObserver.observe(sec));
    }
  }
});
