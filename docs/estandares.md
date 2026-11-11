# Estándares de calidad — imtcolombia / Sistema Clima

Checklist propio, adaptado a este proyecto (Flask + Jinja2 + CSS/JS planos,
sin bundler ni framework JS). Construido a partir de tres listas de
referencia reconocidas en la comunidad front-end, filtrando solo lo
aplicable a este stack:

- [Front-End Checklist](https://github.com/binhnguyennus/front-end-checklist) (binhnguyennus)
- [Front-End Design Checklist](https://github.com/thedaviddias/Front-End-Design-Checklist) (thedaviddias)
- [Front-End Performance Checklist](https://github.com/thedaviddias/Front-End-Performance-Checklist) (thedaviddias)

Estado verificado el 2026-08-15 contra el código real (no es una lista
genérica copiada — cada ✅/⬜ se revisó contra archivos concretos del repo).
`✅` = confirmado en el código. `⬜` = falta o no se pudo confirmar.
`🔎` = pendiente de auditar manualmente (no basta con leer código).

---

## 1. Reglas propias del proyecto (ya en vigor, no negociables)

- **Tamaño de archivo:** ningún archivo fuente supera ~700 líneas. Al
  llegar al límite, dividir por función (ver cómo se dividió
  `dashboard.js` en `app/static/js/dashboard/*.js`).
- **Comentarios:** mínimos, solo para un "por qué" no obvio (restricción
  oculta, workaround). Nunca narrar qué hace el código.
- **Verificación:** antes de reportar tamaños/estado de archivos, contar
  líneas reales — no confiar en cifras de memoria.
- **Overlays con zoom/escala:** todo elemento posicionado en absoluto que
  escale con zoom debe tener su contenedor con `overflow:hidden` +
  `position:relative` explícitos, sin asumir que una librería externa lo
  hace por defecto.

## 2. `<head>` y metadatos

- ✅ `<!DOCTYPE html>`, `<meta charset="UTF-8">`, `<meta name="viewport">`
- ✅ `lang="es"` en `<html>`
- ✅ Favicon (`logo-imt-icono.svg`), `apple-touch-icon`, `manifest.json`
- ⬜ **`<meta name="description">`** — no está en `_base.html`. Cada
  página pública debería tener una descripción única (impacta SEO y cómo
  se ve el link compartido).
- ⬜ **Open Graph / Twitter Card** (`og:title`, `og:description`,
  `og:image`, `twitter:card`) — no existen. Importante si se comparte el
  sitio en redes/WhatsApp: sin esto, el preview del link sale vacío o feo.
- ⬜ **`<link rel="canonical">`** — no está. Relevante porque `_forzar_www`
  ya redirige `nuestroclima.co` → `www`, pero conviene declarar la URL
  canónica explícitamente por página.
- 🔎 `X-UA-Compatible` — no aplica (solo relevante para IE viejo, se puede
  omitir sin problema en 2026).

## 3. HTML

- ✅ Elementos semánticos HTML5 (`<nav>`, `<main>`, `<footer>`) en `_base.html`
- ✅ Páginas de error propias (`errores/404.html`, `errores/500.html`)
- 🔎 Enlaces externos con `target="_blank"` deberían llevar
  `rel="noopener noreferrer"` — revisar si hay alguno en `paginas/*.html`
- 🔎 W3C validator / HTML lint — no corrido en este proyecto todavía

## 4. CSS

- ✅ Sin preprocesador (CSS plano), consistente con "sin bundler"
- ✅ Dividido por módulo (`site/tokens.css`, `site/layout.css`,
  `dashboard/*.css`) en vez de un solo archivo gigante
- 🔎 Contraste de color (texto vs. fondo) — no auditado con herramienta;
  revisar sobre todo textos grises claros (`.copy`, `.enlaces`) en el footer
- 🔎 CSS sin usar (unused CSS) — no medido

## 5. Imágenes

- ✅ Logo en SVG (escala perfecta, peso mínimo) — buena práctica ya aplicada
- 🔎 **`alt` en imágenes** — revisar que todo `<img>` (logo, capturas
  satelitales, iconos de estación) tenga texto alternativo real, no solo
  `alt=""` o el nombre del archivo
- 🔎 Lazy loading (`loading="lazy"`) en imágenes fuera del viewport inicial
  (capturas históricas del Reporte Vélez, por ejemplo) — no confirmado
- 🔎 Dimensiones (`width`/`height`) explícitas en `<img>` para evitar salto
  de layout (CLS) mientras carga

## 6. JavaScript

- ✅ Módulos separados por responsabilidad (`core`, `realtime`, `history`,
  `map-rain`, `map-satellite`, `ui-listeners`, `main`)
- 🔎 Minificación/concatenación — no se aplica (consistente con "sin
  bundler"; aceptable a esta escala, pero revisar si el peso de página
  crece mucho con ArcGIS 3.x + módulos propios)
- 🔎 `noscript` — no confirmado si existe un fallback para JS desactivado

## 7. Seguridad (la parte más madura del proyecto)

- ✅ HTTPS forzado (redirect 301 `nuestroclima.co` → `www`, además Coolify/Traefik)
- ✅ HSTS (`Strict-Transport-Security`, agregado en el diff pendiente de commitear)
- ✅ CSP (`Content-Security-Policy`) con allowlist explícita de dominios
- ✅ `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`
- ✅ `Permissions-Policy` (cámara/micrófono/geo/pagos desactivados)
- ✅ Rate limiting (Flask-Limiter + Redis, límites distintos CO vs. extranjero)
- ✅ Comparación timing-safe del PASSKEY (`hmac.compare_digest`), fail-closed
- ✅ `DB_USER`/`DB_PASS` sin default débil (obligatorias por env var)
- 🔎 CSRF — no aplica directamente (no hay formularios de sesión con
  cookies clásicas más allá de `/admin/noticias`; revisar si ese formulario
  necesita protección CSRF explícita)

## 8. Performance

- ✅ Cache con Redis en endpoints pesados (`Flask-Caching`)
- ✅ `SEND_FILE_MAX_AGE_DEFAULT = 0` en dev, pero revisar cache headers en prod
- 🔎 Peso total de página — no medido con PageSpeed/Lighthouse todavía
  (candidato a medir una vez esté el sitio provincial reformado)
- 🔎 `preconnect`/`dns-prefetch` hacia `js.arcgis.com`, `fonts.googleapis.com`,
  `gibs.earthdata.nasa.gov` — no están; ayudaría a que el mapa cargue más rápido
- ⬜ Gzip/Brotli — no confirmado si Traefik/Coolify lo aplica por defecto
  (revisar configuración de Coolify, no es algo que controle el código Flask)

## 9. Accesibilidad

- 🔎 Navegación por teclado en el mapa de lluvias y modales de estación —
  no probada explícitamente
- 🔎 Roles ARIA en el modal de estación (`station-modal.css`) — no confirmado
- 🔎 Contraste de color — ver punto 4

## 10. Diseño (de Front-End Design Checklist)

- ✅ Sistema de color definido: colores de la bandera colombiana
  (`#FAC725` amarillo, `#185FA5` azul, `#E24B4A` rojo, `#042C53`/`#0C447C`
  navy) para la identidad de IMT
- ✅ Logo con variantes claras: ícono solo (`logo-imt-icono.svg`) vs.
  versión completa con wordmark (pendiente crear, ver tarea abajo)
- 🔎 Estados de enlaces/botones (hover, focus, active) — no auditado
  visualmente en esta sesión
- 🔎 Diseño responsive mobile-first confirmado por breakpoints — revisar
  `site/layout.css` y `dashboard/*.css` en pantallas chicas

## 11. SEO

- ⬜ `robots.txt` — no existe en el proyecto
- ⬜ `sitemap.xml` — no existe
- 🔎 Jerarquía de encabezados (un solo `<h1>` por página) — no auditado

---

## Gaps priorizados (lo que más impacto tiene y falta)

1. `robots.txt` + `sitemap.xml` — bajo esfuerzo, impacto real en SEO
2. `<meta name="description">` + Open Graph por página — bajo esfuerzo,
   mejora cómo se ve el sitio al compartirlo
3. Auditoría de contraste de color y `alt` en imágenes — para
   accesibilidad real, no solo checklist
4. Medir performance real (Lighthouse) una vez esté la reforma provincial,
   antes de decidir si vale la pena optimizar el peso de ArcGIS 3.x
