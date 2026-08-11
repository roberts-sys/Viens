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
    var vids = document.querySelectorAll('video[data-src]:not([data-video])');
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

  function initWorldMapPing() {
    var maps = document.querySelectorAll('.zg-worldmap');
    if (!maps.length) return;

    maps.forEach(function (svg) {
      var dot = svg.querySelector('.zg-dot');
      var ring = svg.querySelector('.zg-ring');
      if (!dot || !ring) return;

      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            dot.classList.add('play');
            ring.classList.add('play');
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
    initWorldMapPing();
    initNavSheenVisibility();
  });
})();
