// site.js — banner de cookies del sitio publico (recuerda la eleccion en localStorage)

function iniciarBannerCookies() {
  const banner = document.getElementById('gwsiteCookies');
  if (!banner) return;
  const elegido = localStorage.getItem('gwsite_cookies');
  if (elegido) return;

  banner.classList.add('visible');
  const guardar = (valor) => {
    localStorage.setItem('gwsite_cookies', valor);
    banner.classList.remove('visible');
  };
  document.getElementById('gwsiteCookiesAceptar')?.addEventListener('click', () => guardar('aceptado'));
  document.getElementById('gwsiteCookiesRechazar')?.addEventListener('click', () => guardar('rechazado'));
}

// Aviso de "sin conexion": aparece si el navegador pierde la conexion
// mientras ya se esta navegando el sitio. No cubre la primera carga sin
// internet (eso necesitaria un Service Worker con cache offline, fuera
// de alcance por ahora).
function iniciarAvisoSinConexion() {
  const aviso = document.createElement('div');
  aviso.id = 'gwsiteSinConexion';
  aviso.style.cssText = 'position:fixed;left:0;right:0;top:0;z-index:300;background:var(--alerta-roja);'
    + 'color:#fff;text-align:center;padding:10px 16px;font-size:13px;font-weight:600;display:none;';
  aviso.textContent = 'Sin conexión a internet — mostrando la última información cargada.';
  document.body.prepend(aviso);

  window.addEventListener('offline', () => { aviso.style.display = 'block'; });
  window.addEventListener('online', () => { aviso.style.display = 'none'; });
}

document.addEventListener('DOMContentLoaded', () => {
  iniciarBannerCookies();
  iniciarAvisoSinConexion();
});
