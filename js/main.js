(function () {
  'use strict';

  var REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

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

  /* The hero cycles six stills with a slow push-in, the same read as the video
     it replaces but at a third of the bytes and no decode cost. Only the first
     frame ships a src; the rest are pulled in one ahead of when they are needed,
     so first paint pays for one image, not six. */
  function initHeroSlides() {
    var wrap = document.querySelector('[data-hero-slides]');
    if (!wrap) return;
    var slides = wrap.querySelectorAll('.zg-hero__slide');
    if (slides.length < 2 || REDUCED_MOTION) return;

    var HOLD = 6000;   // must match the .is-active push-in duration in the CSS
    var FADE = 1600;   // must match the .zg-hero__slide opacity transition
    var i = 0;
    var timer = null;

    function ensure(n) {
      var s = slides[n % slides.length];
      if (s && !s.getAttribute('src') && s.dataset.src) s.setAttribute('src', s.dataset.src);
    }

    function step() {
      var cur = slides[i];
      i = (i + 1) % slides.length;
      var next = slides[i];
      // is-leaving keeps the same animation-name, so the outgoing frame carries on
      // drifting while it fades instead of snapping back to its start scale.
      cur.classList.remove('is-active');
      cur.classList.add('is-leaving');
      next.classList.add('is-active');
      window.setTimeout(function () { cur.classList.remove('is-leaving'); }, FADE);
      ensure(i + 1);
    }

    function start() {
      if (timer) return;
      timer = window.setInterval(step, HOLD);
    }
    function stop() {
      if (!timer) return;
      window.clearInterval(timer);
      timer = null;
    }

    ensure(1);
    start();

    // A hero cycling behind a hidden tab is pure wasted decode work.
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stop(); else start();
    });
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

  // Cursor-tracked spotlight on the tiles. Reading the rect is a forced layout,
  // so it happens at most once per frame -- high-poll-rate mice fire pointermove
  // several times between paints.
  function initTileGlow() {
    if (REDUCED_MOTION) return;
    if (!window.matchMedia('(hover: hover)').matches) return;
    var tiles = document.querySelectorAll('.zg-tile');
    if (!tiles.length) return;

    tiles.forEach(function (tile) {
      var glow = document.createElement('div');
      glow.className = 'zg-tile__glow';
      // above the image/wash/grain, below the badge and caption
      tile.insertBefore(glow, tile.querySelector('.zg-tile__badge'));

      var ticking = false;
      var lastX = 0, lastY = 0;

      function place() {
        var rect = tile.getBoundingClientRect();
        if (!rect.width || !rect.height) return;
        tile.style.setProperty('--mx', ((lastX - rect.left) / rect.width * 100).toFixed(1) + '%');
        tile.style.setProperty('--my', ((lastY - rect.top) / rect.height * 100).toFixed(1) + '%');
      }

      // Place the glow before the opacity fade starts. Without this it spends
      // its first frames at dead centre -- or wherever the pointer left it last
      // time -- and visibly slides across the tile as it fades in.
      tile.addEventListener('pointerenter', function (e) {
        lastX = e.clientX;
        lastY = e.clientY;
        place();
      }, { passive: true });

      tile.addEventListener('pointermove', function (e) {
        lastX = e.clientX;
        lastY = e.clientY;
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function () {
          ticking = false;
          place();
        });
      }, { passive: true });
    });
  }

  // Blur-crossfade the hero accent word through a short list of synonyms. The
  // words sit stacked in a single grid cell (see .zg-morph__stack), so the box
  // is intrinsically as wide as the longest of them and nothing here has to
  // measure text. A measured px width was wrong twice over: it is taken before
  // Inter swaps in over the fallback font, and it does not follow the type
  // dropping from 56px/700 to 33px/800 under the 768px breakpoint.
  // Project photos open in a modal that pages within its own set. <dialog>
  // carries the focus trap, Escape and background-inert for free, which a
  // hand-rolled overlay would all have to reimplement.
  function initLightbox() {
    var dlg = document.querySelector('[data-lightbox]');
    if (!dlg || !dlg.showModal) return;

    var img = dlg.querySelector('[data-lightbox-img]');
    var cap = dlg.querySelector('[data-lightbox-caption]');
    var count = dlg.querySelector('[data-lightbox-count]');
    var prev = dlg.querySelector('[data-lightbox-prev]');
    var next = dlg.querySelector('[data-lightbox-next]');
    var shots = [];
    var i = 0;
    var opener = null;

    function show() {
      var im = shots[i].querySelector('img');
      img.src = im.currentSrc || im.src;
      img.alt = im.alt;
      cap.textContent = im.alt;
      count.textContent = (i + 1) + ' / ' + shots.length;
      // a single-photo set has nothing to page to
      prev.hidden = next.hidden = shots.length < 2;
    }

    function step(d) {
      i = (i + d + shots.length) % shots.length;
      show();
    }

    document.addEventListener('click', function (e) {
      var shot = e.target.closest('.zg-project__shot');
      if (shot) {
        /* Scope to the strip, not the parent node: in the feature layout the
           build frames sit inside .zg-project__build and the hero inside
           .zg-project__print, so parentNode would page only one of the two.
           querySelectorAll is a descendant query in document order, so the
           nesting costs nothing here. */
        var scope = shot.closest('.zg-project__strip') || shot.parentNode;
        shots = Array.prototype.slice.call(
          scope.querySelectorAll('.zg-project__shot'));
        i = shots.indexOf(shot);
        opener = shot;
        show();
        dlg.showModal();
        return;
      }
      if (!dlg.open) return;
      if (e.target.closest('[data-lightbox-prev]')) step(-1);
      else if (e.target.closest('[data-lightbox-next]')) step(1);
      else if (e.target.closest('[data-lightbox-close]') || e.target === dlg) dlg.close();
    });

    dlg.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { e.preventDefault(); step(1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); step(-1); }
    });

    // send focus back where it came from, or the page loses its place
    dlg.addEventListener('close', function () { if (opener) opener.focus(); });
  }

  /* Before/after wipe. One custom property per input event -- a range fires at
     most once per pointer sample, so there is nothing here worth throttling. */
  function initCompare() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-compare]'), function (r) {
      var box = r.closest('.zg-compare');
      if (!box) return;
      function set() { box.style.setProperty('--pos', r.value + '%'); }
      r.addEventListener('input', set);
      set();
    });
  }

  function initMorphs() {
    if (REDUCED_MOTION) return;
    // every stack on the page, not just the first: the hero title and the
    // architecture panel each carry one
    Array.prototype.forEach.call(document.querySelectorAll('.zg-morph__stack'), initMorph);
  }

  function initMorph(stack) {
    var words = stack.querySelectorAll('.zg-morph__w');
    if (words.length < 2) return;

    var i = 0;

    // Per-stack cadence: the architecture panel turns over faster than the
    // hero, which holds each phrase long enough to be read as a claim.
    var period = parseInt(stack.getAttribute('data-interval'), 10) || 3400;

    // Opted-in stacks size to the word actually showing, so a short word does
    // not leave a gap mid-sentence. Measured live rather than baked: the
    // widths move with the breakpoint and with a late font swap.
    var fit = stack.hasAttribute('data-fit');

    function fitWidth() {
      if (!fit) return;
      stack.style.width = words[i].getBoundingClientRect().width.toFixed(1) + 'px';
    }

    if (fit) {
      fitWidth();
      if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitWidth);
      var rt;
      window.addEventListener('resize', function () {
        clearTimeout(rt);
        // remeasure from the natural width, not the one we just pinned
        rt = setTimeout(function () { stack.style.width = ''; fitWidth(); }, 150);
      }, { passive: true });
    }
    var timer = null;
    var onscreen = true;

    function step() {
      words[i].classList.remove('is-on');
      i = (i + 1) % words.length;
      words[i].classList.add('is-on');
      fitWidth();
    }

    function sync() {
      var run = onscreen && !document.hidden;
      if (run && !timer) timer = setInterval(step, period);
      else if (!run && timer) { clearInterval(timer); timer = null; }
    }

    // Repainting a blurred word every 3.4s behind the fold buys nothing.
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        onscreen = entries[0].isIntersecting;
        sync();
      }, { threshold: 0 }).observe(stack);
    }

    document.addEventListener('visibilitychange', sync);
    sync();
  }

  function initFormSubmitSpinner() {
    var form = document.querySelector('.zg-contact__form');
    var btn = form && form.querySelector('.zg-form__submit');
    if (!form || !btn) return;
    var idleHTML = btn.innerHTML;
    var loadingLabel = btn.dataset.loadingLabel || 'Loading...';

    form.addEventListener('submit', function () {
      if (btn.disabled) return;
      // Deferred: disabling a submit button synchronously inside the submit
      // handler can cancel the submission in some browsers.
      setTimeout(function () {
        btn.disabled = true;
        btn.setAttribute('aria-busy', 'true');
        btn.innerHTML = '<svg class="zg-form__spinner" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9" stroke-opacity=".25"></circle><path d="M21 12a9 9 0 0 0-9-9"></path></svg>' + loadingLabel;
      }, 0);
    });

    // Backing out of /thanks restores this page from bfcache with the button
    // still disabled and spinning. Hand it back in its idle state.
    window.addEventListener('pageshow', function (e) {
      if (!e.persisted) return;
      btn.disabled = false;
      btn.removeAttribute('aria-busy');
      btn.innerHTML = idleHTML;
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
    initHeroSlides();
    initCrosshairScene();
    initHeroParallax();
    initNavReturn();
    initReveals();
    initFooterFade();
    initWorldMapPing();
    initNavSheenVisibility();
    initTileGlow();
    initMorphs();
    initLightbox();
    initCompare();
    initFormSubmitSpinner();
  });
})();
