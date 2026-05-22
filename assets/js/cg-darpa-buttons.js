document.addEventListener('DOMContentLoaded', function () {
  var buttons = Array.prototype.slice.call(document.querySelectorAll('.cg-btn'));

  buttons.forEach(function (button) {
    if (!button.querySelector('.cg-loader-dot')) {
      var loader = document.createElement('span');
      loader.className = 'cg-loader-dot';
      loader.setAttribute('aria-hidden', 'true');
      button.appendChild(loader);
    }

    button.addEventListener('pointermove', function (event) {
      var rect = button.getBoundingClientRect();
      var x = ((event.clientX - rect.left) / rect.width) * 100;
      var y = ((event.clientY - rect.top) / rect.height) * 100;
      var tiltY = ((event.clientX - rect.left) / rect.width - 0.5) * 8;
      var tiltX = (((event.clientY - rect.top) / rect.height - 0.5) * -6);

      button.style.setProperty('--cg-x', x + '%');
      button.style.setProperty('--cg-y', y + '%');
      button.style.setProperty('--cg-tilt-x', tiltX + 'deg');
      button.style.setProperty('--cg-tilt-y', tiltY + 'deg');
    });

    button.addEventListener('pointerleave', function () {
      button.style.setProperty('--cg-x', '50%');
      button.style.setProperty('--cg-y', '50%');
      button.style.setProperty('--cg-tilt-x', '0deg');
      button.style.setProperty('--cg-tilt-y', '0deg');
    });

    button.addEventListener('click', function (event) {
      if (button.disabled || button.classList.contains('is-disabled')) return;

      var rect = button.getBoundingClientRect();
      var ripple = document.createElement('span');
      ripple.className = 'cg-btn__ripple';
      ripple.style.left = (event.clientX - rect.left) + 'px';
      ripple.style.top = (event.clientY - rect.top) + 'px';
      button.appendChild(ripple);

      window.setTimeout(function () {
        ripple.remove();
      }, 700);
    });
  });

  Array.prototype.slice.call(document.querySelectorAll('[data-cg-loading-demo]')).forEach(function (button) {
    button.addEventListener('click', function () {
      if (button.classList.contains('is-loading')) return;
      var originalLabel = button.getAttribute('data-label') || button.textContent.trim();
      button.setAttribute('data-label', originalLabel);
      button.classList.add('is-loading');
      button.setAttribute('aria-busy', 'true');

      window.setTimeout(function () {
        button.classList.remove('is-loading');
        button.removeAttribute('aria-busy');
      }, 1600);
    });
  });
});
