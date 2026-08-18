/* Cookie consent for Google Analytics.
   GoatCounter is cookieless and needs no consent, so it stays in the page
   markup and runs regardless. Only gtag waits on an explicit opt-in. */
(function () {
  var KEY = 'zg-consent';
  var GA_ID = 'G-6C978YY53L';

  var COPY = {
    lv: {
      text: 'Mēs izmantojam sīkdatnes, lai saprastu, kā vietne tiek lietota.',
      accept: 'Piekrītu',
      decline: 'Noraidīt',
      label: 'Piekrišana sīkdatnēm'
    },
    en: {
      text: 'We use cookies to understand how this site is used.',
      accept: 'Accept',
      decline: 'Decline',
      label: 'Cookie consent'
    }
  };

  function remembered() {
    try { return localStorage.getItem(KEY); } catch (e) { return null; }
  }

  function remember(value) {
    try { localStorage.setItem(KEY, value); } catch (e) {}
  }

  function loadAnalytics() {
    var tag = document.createElement('script');
    tag.async = true;
    tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(tag);

    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', GA_ID);
  }

  var choice = remembered();
  if (choice === 'granted') { loadAnalytics(); return; }
  if (choice === 'denied') { return; }

  var t = COPY[document.documentElement.lang === 'en' ? 'en' : 'lv'];

  var bar = document.createElement('div');
  bar.className = 'zg-consent';
  bar.setAttribute('role', 'dialog');
  bar.setAttribute('aria-label', t.label);
  bar.innerHTML =
    '<p class="zg-consent__text">' + t.text + '</p>' +
    '<div class="zg-consent__actions">' +
      '<button type="button" class="zg-consent__btn" data-consent="denied">' + t.decline + '</button>' +
      '<button type="button" class="zg-consent__btn zg-consent__btn--accept" data-consent="granted">' + t.accept + '</button>' +
    '</div>';

  bar.addEventListener('click', function (event) {
    var answer = event.target.getAttribute('data-consent');
    if (!answer) return;
    remember(answer);
    if (answer === 'granted') loadAnalytics();
    bar.remove();
  });

  document.body.appendChild(bar);
})();
