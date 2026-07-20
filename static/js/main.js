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

  // 2. Interactive MCQ Circle Select
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
    });
  });

  // 3. Staggered Console Log Reveal & Grade Seal
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
          lineIndex++;
          setTimeout(showNextLine, prefersReducedMotion ? 50 : 800);
        } else {
          // Reveal the A+ grade stamp at the end
          if (stamp) {
            setTimeout(() => {
              stamp.classList.add('revealed');
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

  // 4. Scroll Reveal via Intersection Observer
  const sections = document.querySelectorAll('section');
  if (sections.length > 0) {
    if (prefersReducedMotion) {
      sections.forEach(sec => sec.classList.add('revealed'));
    } else {
      const revealObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
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
