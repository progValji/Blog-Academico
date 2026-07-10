from datetime import datetime
from html.parser import HTMLParser
from html import escape

VOID_TAGS = {'area','base','br','col','embed','hr','img','input',
             'link','meta','param','source','track','wbr'}

class _TruncadorHTML(HTMLParser):
    def __init__(self, limite):
        super().__init__(convert_charrefs=True)
        self.limite = limite
        self.contador = 0
        self.pila = []
        self.salida = []
        self.truncado = False

    def handle_starttag(self, tag, attrs):
        if self.truncado:
            return
        attrs_str = ''.join(
            f' {k}="{escape(v, quote=True)}"' if v is not None else f' {k}'
            for k, v in attrs
        )
        self.salida.append(f'<{tag}{attrs_str}>')
        if tag not in VOID_TAGS:
            self.pila.append(tag)

    def handle_endtag(self, tag):
        if self.truncado:
            return
        self.salida.append(f'</{tag}>')
        for i in range(len(self.pila) - 1, -1, -1):
            if self.pila[i] == tag:
                del self.pila[i]
                break

    def handle_data(self, data):
        if self.truncado:
            return
        restante = self.limite - self.contador
        if len(data) <= restante:
            self.salida.append(escape(data))
            self.contador += len(data)
        else:
            corte = data.rfind(' ', 0, restante)
            if corte == -1:
                corte = restante
            self.salida.append(escape(data[:corte]) + '...')
            self.contador = self.limite
            self.truncado = True

    def resultado(self):
        html = ''.join(self.salida)
        # cierra cualquier tag que haya quedado abierto, en orden inverso
        html += ''.join(f'</{t}>' for t in reversed(self.pila))
        return html

def init_filters(app):
    @app.template_filter('tiempo_relativo')
    def tiempo_relativo(fecha):
        ahora = datetime.now()
        diferencia = ahora - fecha

        segundos = diferencia.total_seconds()

        if segundos < 60:
            return f"{int(segundos)} segundos"
        
        minutos = segundos / 60
        if minutos < 60:
            return f"{int(minutos)} minutos"
        
        horas = minutos / 60
        if horas < 24:
            return f"{int(horas)} horas"
        
        if fecha.year == ahora.year:
            return fecha.strftime("%d %b") 
        else:
            return fecha.strftime("%d %b %Y") 
        
    @app.template_filter('crear_preview')
    def crear_preview(texto, limite=250):
        parser = _TruncadorHTML(limite)
        parser.feed(texto)
        parser.close()
        if not parser.truncado:
            return texto  # no hizo falta truncar
        return parser.resultado()