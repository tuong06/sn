(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const root = document.documentElement;

  /* ---------- Nhạc nền ---------- */
  const bgm = $('#bgm');
  const musicBtn = $('.music');
  const TARGET = 0.55;
  let fadeRaf = 0;
  let wantMusic = false;     // người xem muốn nghe nhạc (bật hay tắt bằng tay)
  let duckedByVideo = false; // nhạc đang tạm dừng vì phim đang phát

  function setMusicUi(on) {
    musicBtn.setAttribute('aria-pressed', String(on));
    musicBtn.setAttribute('aria-label', on ? 'Nhạc nền đang bật, bấm để tắt' : 'Nhạc nền đang tắt, bấm để bật');
  }

  function fadeTo(target, ms, done) {
    cancelAnimationFrame(fadeRaf);
    const from = bgm.volume;
    const t0 = performance.now();
    const step = (now) => {
      const k = Math.min(1, (now - t0) / ms);
      bgm.volume = Math.max(0, Math.min(1, from + (target - from) * k));
      if (k < 1) fadeRaf = requestAnimationFrame(step);
      else if (done) done();
    };
    fadeRaf = requestAnimationFrame(step);
  }

  function musicOn() {
    bgm.volume = 0;
    const p = bgm.play();
    setMusicUi(true);
    fadeTo(TARGET, 1200);
    if (p && p.catch) p.catch(() => { setMusicUi(false); wantMusic = false; });
  }

  function musicOff() {
    setMusicUi(false);
    fadeTo(0, 450, () => bgm.pause());
  }

  musicBtn.addEventListener('click', () => {
    wantMusic = !wantMusic;
    duckedByVideo = false;
    if (wantMusic) musicOn(); else musicOff();
  });

  // tắt tab hoặc chuyển ứng dụng thì dừng nhạc, quay lại thì phát tiếp
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) { if (!bgm.paused) bgm.pause(); }
    else if (wantMusic && !duckedByVideo) musicOn();
  });

  /* ---------- Màn mở quà ---------- */
  const gate = $('.gate');
  const outside = [$('header.hero'), $('main'), $('footer.foot'), musicBtn];
  outside.forEach((el) => { el.inert = true; });

  function openGift(withMusic) {
    if (root.classList.contains('is-open')) return;
    if (withMusic) { wantMusic = true; musicOn(); }
    root.classList.add('is-open');
    outside.forEach((el) => { el.inert = false; });
    gate.setAttribute('aria-hidden', 'true');
    setTimeout(() => { gate.hidden = true; }, 1200);
    $('.hero-name').focus({ preventScroll: true });
  }
  $$('.gate button').forEach((b) => b.addEventListener('click', () => openGift(b.dataset.music === 'on')));
  $('.gate-open').focus({ preventScroll: true });

  /* ---------- Ảnh lộ dần khi cuộn tới ---------- */
  const plates = $$('.pl');
  if ('IntersectionObserver' in window) {
    root.classList.add('reveal');
    const io = new IntersectionObserver((es) => {
      es.forEach((e) => {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    plates.forEach((p) => io.observe(p));
  }

  /* ---------- Xem ảnh lớn ---------- */
  const box = $('.lightbox');
  const big = $('img', box);
  const count = $('.lb-count');
  const pins = $$('.pl button');
  const full = (i) => $('img', pins[i]).getAttribute('src').replace('-s.jpg', '.jpg');
  let at = 0;

  function show(i) {
    at = (i + pins.length) % pins.length;
    const thumb = $('img', pins[at]);
    big.classList.add('loading');
    big.onload = () => big.classList.remove('loading');
    big.src = full(at);
    big.alt = thumb.alt;
    count.textContent = `${at + 1} / ${pins.length}`;
    // tải trước ảnh kế bên để bấm qua lại không phải chờ
    [at + 1, at - 1].forEach((j) => { new Image().src = full((j + pins.length) % pins.length); });
  }

  pins.forEach((b, i) => b.addEventListener('click', () => { show(i); box.showModal(); }));
  $('.lb-prev').addEventListener('click', () => show(at - 1));
  $('.lb-next').addEventListener('click', () => show(at + 1));
  $('.lb-close').addEventListener('click', () => box.close());
  box.addEventListener('click', (e) => { if (e.target === box || e.target === big) box.close(); });
  box.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') show(at - 1);
    if (e.key === 'ArrowRight') show(at + 1);
  });
  box.addEventListener('close', () => pins[at].focus());

  let x0 = null;
  box.addEventListener('touchstart', (e) => { x0 = e.touches[0].clientX; }, { passive: true });
  box.addEventListener('touchend', (e) => {
    if (x0 === null) return;
    const dx = e.changedTouches[0].clientX - x0;
    if (Math.abs(dx) > 50) show(at + (dx < 0 ? 1 : -1));
    x0 = null;
  }, { passive: true });

  /* ---------- Phim: chọn đoạn nào phát đoạn đó, nhạc nền nhường tiếng ---------- */
  const player = $('#player');
  const clips = $$('.clips button');
  clips.forEach((b) => b.addEventListener('click', () => {
    clips.forEach((o) => o.setAttribute('aria-pressed', String(o === b)));
    const n = b.dataset.v;
    player.poster = `assets/video/v${n}.jpg`;
    player.src = `assets/video/v${n}.mp4`;
    player.setAttribute('aria-label', $('.clip-t', b).textContent);
    player.play().catch(() => {});
  }));
  player.addEventListener('ended', () => {
    const i = clips.findIndex((b) => b.getAttribute('aria-pressed') === 'true');
    if (i < clips.length - 1) clips[i + 1].click();
    else resumeAfterVideo();
  });
  player.addEventListener('play', () => {
    if (wantMusic && !bgm.paused) { duckedByVideo = true; musicOff(); }
  });
  function resumeAfterVideo() {
    if (duckedByVideo && wantMusic) { duckedByVideo = false; musicOn(); }
  }
  player.addEventListener('pause', () => { if (!player.ended) resumeAfterVideo(); });
  if ('IntersectionObserver' in window) {
    new IntersectionObserver((es) => {
      es.forEach((e) => { if (!e.isIntersecting && !player.paused) player.pause(); });
    }, { threshold: 0.15 }).observe(player);
  }

  /* ---------- Thổi nến ---------- */
  const wish = $('.wish');
  const wishBtn = $('.wish-btn');
  const wishText = $('.wish-text');

  function chime() {
    // vài nốt chuông nhỏ (Fa trưởng) khi nến tắt
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    const ac = new AC();
    const notes = [72, 76, 79, 84].map((m) => 440 * 2 ** ((m + 5 - 69) / 12));
    notes.forEach((f, k) => {
      const t = ac.currentTime + 0.35 + k * 0.12;
      [1, 2.01, 4.17].forEach((r, j) => {
        const o = ac.createOscillator();
        const g = ac.createGain();
        o.frequency.value = f * r;
        g.gain.setValueAtTime(0, t);
        g.gain.linearRampToValueAtTime([0.12, 0.04, 0.02][j], t + 0.004);
        g.gain.exponentialRampToValueAtTime(0.0001, t + [1.6, 0.6, 0.25][j]);
        o.connect(g).connect(ac.destination);
        o.start(t);
        o.stop(t + 1.7);
      });
    });
    setTimeout(() => ac.close(), 3200);
  }

  wishBtn.addEventListener('click', () => {
    const blown = wish.classList.toggle('blown');
    if (blown) {
      wishText.textContent = 'Điều ước đã được gửi đi. Chúc mừng sinh nhật, Thu Huệ.';
      wishBtn.textContent = 'Thắp lại nến';
      chime();
    } else {
      wishText.textContent = 'Ước xong thì thổi nến nhé.';
      wishBtn.textContent = 'Thổi nến';
    }
  });
})();
