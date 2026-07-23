// ──────────────────────────────────────────────────────────────
// weather-fx.js  —  Efectos animados del cielo (lluvia, estrellas)
// ──────────────────────────────────────────────────────────────

const fxCanvas  = document.getElementById('weatherCanvas');
const fxCtx     = fxCanvas.getContext('2d');

let fxMode      = null; // 'sunny' | 'cloudy' | 'rainy' | 'night'
let particles   = [];
let fxAnimFrame = null;

function resizeCanvas() {
  fxCanvas.width  = window.innerWidth;
  fxCanvas.height = window.innerHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

// ─── PARTÍCULAS DE LLUVIA ────────────────────────────────────
function createRainDrop() {
  return {
    x:     Math.random() * fxCanvas.width,
    y:     Math.random() * -fxCanvas.height,
    len:   Math.random() * 18 + 8,
    speed: Math.random() * 6 + 8,
    alpha: Math.random() * 0.4 + 0.2
  };
}

function createStar() {
  return {
    x:     Math.random() * fxCanvas.width,
    y:     Math.random() * fxCanvas.height * 0.6,
    r:     Math.random() * 1.5 + 0.3,
    alpha: Math.random(),
    blink: Math.random() * 0.02 + 0.005,
    dir:   Math.random() > 0.5 ? 1 : -1
  };
}

function initParticles() {
  particles = [];
  if (fxMode === 'rainy') {
    for (let i = 0; i < 180; i++) particles.push(createRainDrop());
  } else if (fxMode === 'night') {
    for (let i = 0; i < 120; i++) particles.push(createStar());
  }
}

// ─── BUCLE DE ANIMACIÓN ───────────────────────────────────────
function drawFrame() {
  fxCtx.clearRect(0, 0, fxCanvas.width, fxCanvas.height);

  if (fxMode === 'rainy') {
    fxCtx.strokeStyle = 'rgba(180,210,255,0.5)';
    fxCtx.lineWidth = 1;

    particles.forEach(p => {
      fxCtx.globalAlpha = p.alpha;
      fxCtx.beginPath();
      fxCtx.moveTo(p.x, p.y);
      fxCtx.lineTo(p.x - 2, p.y + p.len);
      fxCtx.stroke();

      p.y += p.speed;
      p.x -= 1;

      if (p.y > fxCanvas.height) {
        p.y = Math.random() * -50;
        p.x = Math.random() * fxCanvas.width;
      }
    });
    fxCtx.globalAlpha = 1;

  } else if (fxMode === 'night') {
    particles.forEach(p => {
      p.alpha += p.blink * p.dir;
      if (p.alpha > 1 || p.alpha < 0.1) p.dir *= -1;
      fxCtx.globalAlpha = p.alpha;
      fxCtx.fillStyle = '#ffffff';
      fxCtx.beginPath();
      fxCtx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      fxCtx.fill();
    });
    fxCtx.globalAlpha = 1;
  }

  fxAnimFrame = requestAnimationFrame(drawFrame);
}

// ─── API PÚBLICA ─────────────────────────────────────────────
window.WeatherFX = {
  setMode(mode) {
    if (fxMode === mode) return;
    fxMode = mode;

    // Actualizar clase del cielo en el contenedor (no en el body)
    const container = document.querySelector('.gw-container');
    if (container) {
      container.className = `gw-container sky-${mode}`;
    }

    // El fondo (bg_sunny.png) se mantiene siempre igual según lo solicitado por el usuario,
    // solo cambia el tintado (overlay) a través de --container-bg.

    initParticles();

    if (fxAnimFrame) cancelAnimationFrame(fxAnimFrame);

    // Solo animar si hay partículas
    if (mode === 'rainy' || mode === 'night') {
      drawFrame();
    } else {
      fxCtx.clearRect(0, 0, fxCanvas.width, fxCanvas.height);
    }
  }
};
