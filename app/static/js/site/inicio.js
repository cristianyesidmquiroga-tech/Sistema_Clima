// inicio.js — carrusel de vistas (rota cada 4s, pausa al pasar el mouse) + noticias del dia

function iniciarCarrusel() {
  const cont = document.getElementById('gwiCarrusel');
  const puntosCont = document.getElementById('gwiPuntos');
  if (!cont || !puntosCont) return;
  const slides = Array.from(cont.querySelectorAll('.gwi-slide'));
  if (!slides.length) return;

  let indice = 0;
  let pausado = false;

  slides.forEach((_, i) => {
    const punto = document.createElement('button');
    if (i === 0) punto.classList.add('activo');
    punto.addEventListener('click', () => mostrar(i));
    puntosCont.appendChild(punto);
  });
  const puntos = Array.from(puntosCont.children);

  function mostrar(i) {
    slides[indice].classList.remove('activa');
    puntos[indice].classList.remove('activo');
    indice = i;
    slides[indice].classList.add('activa');
    puntos[indice].classList.add('activo');
  }

  setInterval(() => {
    if (pausado) return;
    mostrar((indice + 1) % slides.length);
  }, 4000);

  cont.addEventListener('mouseenter', () => { pausado = true; });
  cont.addEventListener('mouseleave', () => { pausado = false; });
}

async function cargarNoticias() {
  const cont = document.getElementById('gwiNoticias');
  if (!cont) return;
  try {
    const res = await fetch('/api/noticias');
    const noticias = await res.json();
    if (!noticias.length) {
      cont.innerHTML = '<p class="gwi-noticias-vacio">Todavía no hay noticias publicadas hoy.</p>';
      return;
    }
    cont.innerHTML = noticias.map(n => `
      <article class="gwi-noticia">
        ${n.imagen_url ? `<img src="${n.imagen_url}" alt="">` : ''}
        <div class="cuerpo">
          <div class="etiqueta ${n.tipo}">${n.tipo}</div>
          <h4>${n.titulo}</h4>
          <p>${n.texto}</p>
          <time>${new Date(n.fecha_publicacion).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}</time>
        </div>
      </article>
    `).join('');
  } catch (e) {
    cont.innerHTML = '<p class="gwi-noticias-vacio">No se pudieron cargar las noticias.</p>';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  iniciarCarrusel();
  cargarNoticias();
});
