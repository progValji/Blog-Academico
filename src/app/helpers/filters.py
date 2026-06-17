from datetime import datetime
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