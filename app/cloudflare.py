import ipaddress

# Rangos publicados en https://www.cloudflare.com/ips/
RANGOS_CLOUDFLARE = [ipaddress.ip_network(r) for r in (
    '173.245.48.0/20', '103.21.244.0/22', '103.22.200.0/22', '103.31.4.0/22',
    '141.101.64.0/18', '108.162.192.0/18', '190.93.240.0/20', '188.114.96.0/20',
    '197.234.240.0/22', '198.41.128.0/17', '162.158.0.0/15', '104.16.0.0/13',
    '104.24.0.0/14', '172.64.0.0/13', '131.0.72.0/22',
    '2400:cb00::/32', '2606:4700::/32', '2803:f800::/32', '2405:b500::/32',
    '2405:8100::/32', '2a06:98c0::/29', '2c0f:f248::/32',
)]


def es_cloudflare(ip):
    try:
        direccion = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(direccion in red for red in RANGOS_CLOUDFLARE)


class IPDesdeCloudflare:
    # Solo se cree a CF-Connecting-IP si la peticion llega de Cloudflare; si no, cualquiera la falsifica.
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        real = environ.get('HTTP_CF_CONNECTING_IP', '').strip()
        if real and es_cloudflare(environ.get('REMOTE_ADDR', '')):
            try:
                ipaddress.ip_address(real)
            except ValueError:
                return self.app(environ, start_response)
            environ['REMOTE_ADDR'] = real
            pais = environ.get('HTTP_CF_IPCOUNTRY', '').strip().upper()
            if len(pais) == 2 and pais.isalpha() and pais != 'XX':
                environ['nuestroclima.pais'] = pais
        return self.app(environ, start_response)
