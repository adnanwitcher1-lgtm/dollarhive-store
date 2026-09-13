// DollarHive — small progressive-enhancement helpers.
// No framework, just plain JS as required by the tech stack.

document.addEventListener('DOMContentLoaded', function () {
  // Auto-dismiss Django messages after 5 seconds.
  document.querySelectorAll('.dh-alert').forEach(function (alertEl) {
    setTimeout(function () {
      alertEl.style.transition = 'opacity .4s ease';
      alertEl.style.opacity = '0';
      setTimeout(function () { alertEl.remove(); }, 400);
    }, 5000);
  });

  // Flash-sale countdown: counts down to the next midnight (local
  // time), then automatically resets for the next day. Purely a
  // frontend display — no backend/sale-end date needed.
  var timerEl = document.getElementById('flash-sale-timer');
  if (timerEl) {
    var tick = function () {
      var now = new Date();
      var midnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 0);
      var diff = midnight - now;

      if (diff <= 0) {
        timerEl.textContent = '00h 00m 00s';
        return;
      }

      var hours = Math.floor(diff / (1000 * 60 * 60));
      var minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      var seconds = Math.floor((diff % (1000 * 60)) / 1000);

      var pad = function (n) { return n < 10 ? '0' + n : '' + n; };
      timerEl.textContent = pad(hours) + 'h ' + pad(minutes) + 'm ' + pad(seconds) + 's';
    };
    tick();
    setInterval(tick, 1000);
  }

  // Gentle fade/slide-in for sections marked with .dh-reveal as they
  // scroll into view. Purely cosmetic — falls back gracefully if the
  // browser doesn't support IntersectionObserver.
  var revealEls = document.querySelectorAll('.dh-reveal');
  if (revealEls.length) {
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('dh-in-view');
            io.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12 });
      revealEls.forEach(function (el) { io.observe(el); });
    } else {
      revealEls.forEach(function (el) { el.classList.add('dh-in-view'); });
    }
  }
});
