(function () {
  'use strict';

  var REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var IS_MOBILE = window.matchMedia('(max-width: 768px)').matches;
  var VIDEOS_ENABLED = !REDUCED_MOTION && !IS_MOBILE;

  function loadVideoSrc(v) {
    if (!v.getAttribute('src') && v.dataset.src) v.src = v.dataset.src;
  }

  function initVideoCrossfade() {
    var cell = document.querySelector('[data-video-cell]');
    if (!cell) return;

    var videoA = cell.querySelector('[data-video="a"]');
    var videoB = cell.querySelector('[data-video="b"]');
    if (!videoA || !videoB) return;

    if (!VIDEOS_ENABLED) return; // mobile or reduced motion: posters only

    var startIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          loadVideoSrc(videoA);
          safePlay(videoA);
          startIO.disconnect();
        }
      });
    }, { threshold: 0.25 });
    startIO.observe(cell);

    var hovering = false;
    var active = 0; // 0 = A visible, 1 = B visible
    var leaveTimer = null;
    var DEBOUNCE_MS = 180;

    function show(idx) {
      active = idx;
      videoA.classList.toggle('is-visible', active === 0);
      videoA.classList.toggle('is-hidden', active !== 0);
      videoB.classList.toggle('is-visible', active === 1);
      videoB.classList.toggle('is-hidden', active !== 1);
    }

    function safePlay(v) {
      var p = v.play();
      if (p && p.catch) p.catch(function () {});
    }

    cell.addEventListener('mouseenter', function () {
      if (leaveTimer) {
        clearTimeout(leaveTimer);
        leaveTimer = null;
      }
      if (hovering) return;
      hovering = true;
      show(1);
      videoA.pause();
      loadVideoSrc(videoB);
      safePlay(videoB);
    });

    cell.addEventListener('mouseleave', function () {
      if (leaveTimer) clearTimeout(leaveTimer);
      leaveTimer = setTimeout(function () {
        leaveTimer = null;
        if (!hovering) return;
        hovering = false;
        show(0);
        videoB.pause();
        safePlay(videoA);
      }, DEBOUNCE_MS);
    });

    videoA.addEventListener('ended', function () {
      if (hovering) {
        show(1);
        videoA.pause();
        videoB.currentTime = 0;
        safePlay(videoB);
      } else {
        videoA.currentTime = 0;
        safePlay(videoA);
      }
    });

    videoB.addEventListener('ended', function () {
      if (hovering) {
        show(0);
        videoB.pause();
        videoA.currentTime = 0;
        safePlay(videoA);
      } else {
        videoB.currentTime = 0;
        safePlay(videoB);
      }
    });
  }

  function initLazyVideos() {
    var vids = document.querySelectorAll('video[data-src]:not([data-video]):not([data-hero-video])');
    if (!vids.length || !VIDEOS_ENABLED) return;

    vids.forEach(function (v) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            loadVideoSrc(v);
            var p = v.play();
            if (p && p.catch) p.catch(function () {});
            io.disconnect();
          }
        });
      }, { threshold: 0.25 });
      io.observe(v);
    });
  }

  function initCrosshairScene() {
    if (window.__ZG_MOTION__) return; // GSAP layer drives this scene
    var scene = document.querySelector('.zg-tiles__inner');
    if (!scene || !('IntersectionObserver' in window)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          scene.classList.add('is-drawn');
          io.disconnect();
        }
      });
    }, { threshold: 0.2 });
    io.observe(scene);
  }

  function initHeroParallax() {
    if (window.__ZG_MOTION__) return; // GSAP layer drives the parallax
    var layer = document.querySelector('.zg-hero__parallax');
    var content = document.querySelector('.zg-hero__content');
    var hero = document.querySelector('.zg-hero');
    if (!layer || !hero || REDUCED_MOTION) return;
    var ticking = false;
    function update() {
      ticking = false;
      var y = window.scrollY;
      if (y > hero.offsetHeight) return;
      layer.style.transform = 'translateY(' + (y * 0.28).toFixed(1) + 'px)';
      if (content) content.style.transform = 'translateY(' + (y * 0.14).toFixed(1) + 'px)';
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
  }

  function initHeroVideo() {
    var v = document.querySelector('[data-hero-video]');
    if (!v || !VIDEOS_ENABLED) return;
    if (v.dataset.srcWebm) {
      // <source> children so browsers without H.264 fall back to WebM
      var mp4 = document.createElement('source');
      mp4.src = v.dataset.src;
      mp4.type = 'video/mp4; codecs="avc1.640028"';
      var webm = document.createElement('source');
      webm.src = v.dataset.srcWebm;
      webm.type = 'video/webm; codecs="vp9"';
      v.appendChild(mp4);
      v.appendChild(webm);
    } else {
      loadVideoSrc(v);
    }
    v.addEventListener('canplay', function () {
      var p = v.play();
      if (p && p.then) {
        p.then(function () { v.classList.add('is-playing'); }).catch(function () {});
      } else {
        v.classList.add('is-playing');
      }
    }, { once: true });
    v.load();
  }

  function initNavReturn() {
    var nav = document.querySelector('.zg-nav');
    if (!nav) return;
    var lastY = window.scrollY;
    window.addEventListener('scroll', function () {
      var y = window.scrollY;
      var threshold = window.innerHeight * 0.9;
      if (y > threshold) {
        nav.classList.add('zg-nav--stuck');
        if (y < lastY - 2) nav.classList.add('zg-nav--shown');
        else if (y > lastY + 2) nav.classList.remove('zg-nav--shown');
      } else if (y < 10) {
        nav.classList.remove('zg-nav--stuck', 'zg-nav--shown');
      }
      lastY = y;
    }, { passive: true });
  }

  function initReveals() {
    var els = document.querySelectorAll('[data-reveal]');
    if (!els.length) return;
    if (!('IntersectionObserver' in window)) {
      els.forEach(function (e) { e.classList.add('is-inview'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var group = el.closest('[data-reveal-group]');
        if (group) {
          var members = Array.prototype.slice.call(group.querySelectorAll('[data-reveal]'));
          el.style.setProperty('--reveal-delay', (members.indexOf(el) * 90) + 'ms');
        }
        el.classList.add('is-inview');
        io.unobserve(el);
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
    els.forEach(function (e) { io.observe(e); });
  }

  function initFooterFade() {
    var footers = document.querySelectorAll('.zg-footer, .zg-topic-footer');
    footers.forEach(function (f) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            f.classList.add('is-inview');
            io.disconnect();
          }
        });
      }, { threshold: 0.4 });
      io.observe(f);
    });
  }

  function initWorldMapPing() {
    var maps = document.querySelectorAll('.zg-worldmap');
    if (!maps.length) return;

    maps.forEach(function (svg) {
      var dot = svg.querySelector('.zg-dot');
      var rings = svg.querySelectorAll('.zg-ring');
      if (!dot || !rings.length) return;

      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            dot.classList.add('play');
            rings.forEach(function (r) { r.classList.add('play'); });
            io.disconnect();
          }
        });
      }, { threshold: 0.3 });

      io.observe(svg);
    });
  }

  function initNavSheenVisibility() {
    var sheenEls = document.querySelectorAll('.zg-nav--sheen');
    if (!sheenEls.length) return;

    document.addEventListener('visibilitychange', function () {
      var state = document.hidden ? 'paused' : 'running';
      sheenEls.forEach(function (el) {
        el.style.animationPlayState = state;
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initVideoCrossfade();
    initLazyVideos();
    initHeroVideo();
    initCrosshairScene();
    initHeroParallax();
    initNavReturn();
    initReveals();
    initFooterFade();
    initWorldMapPing();
    initNavSheenVisibility();
  });
})();
