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
    // textContent en vez de innerHTML: los datos vienen de un formulario admin
    cont.replaceChildren(...noticias.map((n) => {
      const articulo = document.createElement('article');
      articulo.className = 'gwi-noticia';

      if (n.imagen_url) {
        const img = document.createElement('img');
        img.src = n.imagen_url;
        img.alt = '';
        articulo.appendChild(img);
      }

      const cuerpo = document.createElement('div');
      cuerpo.className = 'cuerpo';

      const etiqueta = document.createElement('div');
      etiqueta.className = `etiqueta ${n.tipo}`;
      etiqueta.textContent = n.tipo;
      cuerpo.appendChild(etiqueta);

      const h4 = document.createElement('h4');
      h4.textContent = n.titulo;
      cuerpo.appendChild(h4);

      const p = document.createElement('p');
      p.textContent = n.texto;
      cuerpo.appendChild(p);

      const time = document.createElement('time');
      time.textContent = new Date(n.fecha_publicacion).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
      cuerpo.appendChild(time);

      articulo.appendChild(cuerpo);
      return articulo;
    }));
  } catch (e) {
    cont.innerHTML = '<p class="gwi-noticias-vacio">No se pudieron cargar las noticias.</p>';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  iniciarCarrusel();
  cargarNoticias();
});
