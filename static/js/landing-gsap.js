/**
 * EduExam Pro - GSAP ScrollTrigger Section Motion Engine
 * Custom animations for Two Modes, Roll Call, Sandbox Judge, System Capacity & Final CTA
 */

document.addEventListener('DOMContentLoaded', () => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReducedMotion) return;

  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
    console.warn('GSAP or ScrollTrigger script not loaded.');
    return;
  }

  // Register ScrollTrigger plugin
  gsap.registerPlugin(ScrollTrigger);

  // Set perspective on 3D container elements
  gsap.set('#modes .modes-grid', { perspective: 1000 });

  // ==========================================================================
  // 0. Hero Section & Visual Cards Scroll Parallax Depth
  // ==========================================================================
  const heroContent = document.querySelector('.hero-content');
  if (heroContent) {
    gsap.to(heroContent, {
      scrollTrigger: {
        trigger: '#hero',
        start: 'top top',
        end: 'bottom top',
        scrub: 0.5
      },
      y: -50,
      opacity: 0.45,
      scale: 0.97,
      ease: 'none'
    });
  }

  // Differential parallax for side-by-side hero cards
  const examSheetCard = document.getElementById('card-exam-sheet');
  const sandboxConsoleCard = document.getElementById('card-sandbox-console');

  if (examSheetCard) {
    gsap.to(examSheetCard, {
      scrollTrigger: {
        trigger: '#hero',
        start: 'top top',
        end: 'bottom top',
        scrub: 0.6
      },
      y: -40,
      rotateZ: -1.5,
      ease: 'none'
    });
  }

  if (sandboxConsoleCard) {
    gsap.to(sandboxConsoleCard, {
      scrollTrigger: {
        trigger: '#hero',
        start: 'top top',
        end: 'bottom top',
        scrub: 0.8
      },
      y: -75,
      rotateZ: 2,
      ease: 'none'
    });
  }

  // ==========================================================================
  // 1. Two Modes Section (#modes): 3D Perspective Tilt & Feature Stagger
  // ==========================================================================
  const modesTimeline = gsap.timeline({
    scrollTrigger: {
      trigger: '#modes',
      start: 'top 85%',
      toggleActions: 'play none none none'
    }
  });

  modesTimeline
    .fromTo('#modes .section-header', 
      { opacity: 0, y: 40 },
      { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' }
    )
    .fromTo('#col-exam-mode',
      { opacity: 0, x: -80, rotateY: -20, scale: 0.9 },
      { opacity: 1, x: 0, rotateY: 0, scale: 1, duration: 0.8, ease: 'back.out(1.4)' },
      '-=0.3'
    )
    .fromTo('#col-practice-mode',
      { opacity: 0, x: 80, rotateY: 20, scale: 0.9 },
      { opacity: 1, x: 0, rotateY: 0, scale: 1, duration: 0.8, ease: 'back.out(1.4)' },
      '-=0.8'
    )
    .fromTo('#modes .mode-tag',
      { opacity: 0, scale: 0.4 },
      { opacity: 1, scale: 1, stagger: 0.15, duration: 0.5, ease: 'back.out(2)' },
      '-=0.5'
    )
    .fromTo('#modes .mode-feature-row',
      { opacity: 0, x: -25 },
      { opacity: 1, x: 0, stagger: 0.04, duration: 0.4, ease: 'power2.out' },
      '-=0.4'
    );

  // Differential parallax for Two Modes cards
  const colExamMode = document.getElementById('col-exam-mode');
  const colPracticeMode = document.getElementById('col-practice-mode');

  if (colExamMode) {
    gsap.to(colExamMode, {
      scrollTrigger: {
        trigger: '#modes',
        start: 'top bottom',
        end: 'bottom top',
        scrub: 0.5
      },
      y: -35,
      rotateZ: -1,
      ease: 'none'
    });
  }

  if (colPracticeMode) {
    gsap.to(colPracticeMode, {
      scrollTrigger: {
        trigger: '#modes',
        start: 'top bottom',
        end: 'bottom top',
        scrub: 0.8
      },
      y: -60,
      rotateZ: 1,
      ease: 'none'
    });
  }

  // ==========================================================================
  // 2. Roll Call Section (#roll-call): Skew Curtain Slide & Badge Pop
  // ==========================================================================
  const rollCallTimeline = gsap.timeline({
    scrollTrigger: {
      trigger: '#roll-call',
      start: 'top 85%',
      toggleActions: 'play none none none'
    }
  });

  rollCallTimeline
    .fromTo('#roll-call .section-header',
      { opacity: 0, y: 40 },
      { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' }
    )
    .fromTo('.roll-row',
      { opacity: 0, x: -100, skewX: -12 },
      { opacity: 1, x: 0, skewX: 0, stagger: 0.2, duration: 0.75, ease: 'power4.out' },
      '-=0.3'
    )
    .fromTo('.roll-num',
      { scale: 0, rotate: -45 },
      { scale: 1, rotate: 0, stagger: 0.2, duration: 0.5, ease: 'back.out(2)' },
      '-=0.7'
    );

  // ==========================================================================
  // 3. Isolated Sandbox Judge (#judge): Elastic Drop & Grid Stagger
  // ==========================================================================
  const judgeTimeline = gsap.timeline({
    scrollTrigger: {
      trigger: '#judge',
      start: 'top 85%',
      toggleActions: 'play none none none'
    }
  });

  judgeTimeline
    .fromTo('#judge .section-header',
      { opacity: 0, y: 40 },
      { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' }
    )
    .fromTo('.runtimes-container .stamp',
      { opacity: 0, y: -50, scale: 0.5 },
      { opacity: 1, y: 0, scale: 1, stagger: 0.12, duration: 0.7, ease: 'elastic.out(1, 0.5)' },
      '-=0.3'
    )
    .fromTo('.judge-feature-item',
      { opacity: 0, y: 50, scale: 0.9 },
      {
        opacity: 1,
        y: 0,
        scale: 1,
        stagger: {
          amount: 0.4,
          grid: [2, 2],
          from: 'center'
        },
        duration: 0.6,
        ease: 'back.out(1.5)'
      },
      '-=0.3'
    );

  // ==========================================================================
  // 4. System Capacity (#analytics): Explosive Scale & Number Pulse
  // ==========================================================================
  const analyticsTimeline = gsap.timeline({
    scrollTrigger: {
      trigger: '#analytics',
      start: 'top 85%',
      toggleActions: 'play none none none'
    }
  });

  analyticsTimeline
    .fromTo('#analytics .section-header',
      { opacity: 0, y: 40 },
      { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' }
    )
    .fromTo('.tally-cell',
      { opacity: 0, scale: 0.4, y: 30 },
      { opacity: 1, scale: 1, y: 0, stagger: 0.12, duration: 0.65, ease: 'back.out(2.2)' },
      '-=0.3'
    )
    .fromTo('.tally-num',
      { rotateX: 90 },
      { rotateX: 0, stagger: 0.1, duration: 0.5, ease: 'power2.out' },
      '-=0.4'
    );

  // ==========================================================================
  // 5. Final CTA Section (#cta): Guaranteed Button Reveal & Scale Bounce
  // ==========================================================================
  const ctaTimeline = gsap.timeline({
    scrollTrigger: {
      trigger: '#cta',
      start: 'top 95%',
      toggleActions: 'play none none none'
    }
  });

  ctaTimeline
    .fromTo('#cta .container',
      { opacity: 0, scale: 0.9, y: 40 },
      { opacity: 1, scale: 1, y: 0, duration: 0.7, ease: 'power3.out' }
    )
    .fromTo('#cta .hero-ctas .btn',
      { opacity: 0, y: 25, scale: 0.9 },
      { opacity: 1, y: 0, scale: 1, stagger: 0.15, duration: 0.6, ease: 'back.out(1.7)' },
      '-=0.4'
    );

  // ==========================================================================
  // 6. Navigation Bar Scrollspy & Smooth Offset Click-to-Scroll
  // ==========================================================================
  const navSections = [
    { linkId: 'link-modes', sectionId: 'modes' },
    { linkId: 'link-roll-call', sectionId: 'roll-call' },
    { linkId: 'link-judge', sectionId: 'judge' },
    { linkId: 'link-analytics', sectionId: 'analytics' }
  ];

  const navLinks = document.querySelectorAll('header nav ul li a');

  const setActiveLink = (activeId) => {
    navLinks.forEach(link => {
      if (link.id === activeId) {
        link.classList.add('active');
      } else {
        link.classList.remove('active');
      }
    });
  };

  navSections.forEach(({ linkId, sectionId }) => {
    const section = document.getElementById(sectionId);
    const link = document.getElementById(linkId);

    if (section && link) {
      // Scrollspy active highlight on scroll
      ScrollTrigger.create({
        trigger: section,
        start: 'top 40%',
        end: 'bottom 40%',
        onEnter: () => setActiveLink(linkId),
        onEnterBack: () => setActiveLink(linkId)
      });

      // Smooth click-to-scroll with sticky header offset correction
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetOffset = section.getBoundingClientRect().top + window.pageYOffset - 75;
        window.scrollTo({
          top: targetOffset,
          behavior: 'smooth'
        });
      });
    }
  });

  // Remove active state when scrolled back up to top / hero section
  const heroSection = document.getElementById('hero');
  if (heroSection) {
    ScrollTrigger.create({
      trigger: heroSection,
      start: 'top top',
      end: 'bottom 50%',
      onEnter: () => navLinks.forEach(l => l.classList.remove('active')),
      onEnterBack: () => navLinks.forEach(l => l.classList.remove('active'))
    });
  }
});
