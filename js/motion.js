/* GSAP + Lenis layer: scroll-scrubbed scenes on top of the base IO reveal system.
   If this file doesn't run (reduced motion, missing libs), main.js CSS fallbacks take over. */
(function () {
  'use strict';

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

  window.__ZG_MOTION__ = true;
  document.documentElement.classList.add('gsap');
  gsap.registerPlugin(ScrollTrigger);

  document.addEventListener('DOMContentLoaded', function () {
    // Scrolling is native: momentum/glide reads as lag, and anchor links use
    // the stylesheet's scroll-behavior. GSAP only drives scroll-linked scenes.
    if (document.querySelector('.zg-hero__parallax')) {
      // Restrained parallax: enough depth to feel intentional, not a slideshow.
      gsap.to('.zg-hero__parallax', {
        yPercent: 7,
        ease: 'none',
        scrollTrigger: { trigger: '.zg-hero', start: 'top top', end: 'bottom top', scrub: true }
      });
      gsap.to('.zg-hero__content', {
        y: 60,
        opacity: 0,
        ease: 'none',
        scrollTrigger: { trigger: '.zg-hero', start: 'top top', end: '88% top', scrub: true }
      });
    }

    var inner = document.querySelector('.zg-tiles__inner');
    if (inner) {
      var draw = { trigger: inner, start: 'top 82%', end: 'center 48%', scrub: 0.5 };
      gsap.fromTo('.zg-crosshair--top', { xPercent: -50, scaleY: 0, transformOrigin: '50% 0%' },
        { xPercent: -50, scaleY: 1, ease: 'none', scrollTrigger: draw });
      gsap.fromTo('.zg-crosshair--bottom', { xPercent: -50, scaleY: 0, transformOrigin: '50% 100%' },
        { xPercent: -50, scaleY: 1, ease: 'none', scrollTrigger: draw });
      gsap.fromTo('.zg-crosshair--left', { yPercent: -50, scaleX: 0, transformOrigin: '0% 50%' },
        { yPercent: -50, scaleX: 1, ease: 'none', scrollTrigger: draw });
      gsap.fromTo('.zg-crosshair--right', { yPercent: -50, scaleX: 0, transformOrigin: '100% 50%' },
        { yPercent: -50, scaleX: 1, ease: 'none', scrollTrigger: draw });

      ScrollTrigger.create({
        trigger: inner,
        start: 'center 52%',
        once: true,
        onEnter: function () { inner.classList.add('is-drawn'); }
      });
    }

    var cell = document.querySelector('[data-video-cell][data-reveal]');
    if (cell) {
      gsap.fromTo(cell, { '--zg-curtain': '0%' }, {
        '--zg-curtain': '101%',
        ease: 'none',
        scrollTrigger: { trigger: cell, start: 'top 80%', end: 'top 32%', scrub: 0.4 }
      });
    }
  });
})();
