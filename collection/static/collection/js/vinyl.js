(function () {
  const lightbox = document.getElementById('lightbox');
  if (!lightbox) return;

  const img = document.getElementById('lightbox-image');
  const caption = document.getElementById('lightbox-caption');
  const btnClose = lightbox.querySelector('.lightbox-close');
  const btnPrev = lightbox.querySelector('.lightbox-prev');
  const btnNext = lightbox.querySelector('.lightbox-next');

  let sources = [];
  let captions = [];
  let currentIndex = 0;

  function collectSources() {
    const buttons = Array.from(document.querySelectorAll('[data-lightbox-src]'));
    sources = buttons.map((b) => b.dataset.lightboxSrc);
    captions = buttons.map((b) => b.dataset.lightboxCaption || '');
    return buttons;
  }

  function show(index) {
    if (!sources.length) return;
    currentIndex = (index + sources.length) % sources.length;
    img.src = sources[currentIndex];
    caption.textContent = captions[currentIndex] || '';
    lightbox.hidden = false;
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.classList.add('lightbox-open');
  }

  function hide() {
    lightbox.hidden = true;
    lightbox.setAttribute('aria-hidden', 'true');
    img.src = '';
    document.body.classList.remove('lightbox-open');
  }

  function bindButtons() {
    const buttons = collectSources();
    buttons.forEach((btn, index) => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.dataset.lightboxIndex, 10);
        show(Number.isNaN(idx) ? index : idx);
      });
    });
    btnPrev.style.visibility = sources.length > 1 ? 'visible' : 'hidden';
    btnNext.style.visibility = sources.length > 1 ? 'visible' : 'hidden';
  }

  btnClose.addEventListener('click', hide);
  btnPrev.addEventListener('click', () => show(currentIndex - 1));
  btnNext.addEventListener('click', () => show(currentIndex + 1));

  lightbox.addEventListener('click', (e) => {
    if (e.target === lightbox) hide();
  });

  document.addEventListener('keydown', (e) => {
    if (lightbox.hidden) return;
    if (e.key === 'Escape') hide();
    if (e.key === 'ArrowLeft') show(currentIndex - 1);
    if (e.key === 'ArrowRight') show(currentIndex + 1);
  });

  bindButtons();
})();
