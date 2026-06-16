"""
Utilidades de limpieza y procesamiento de texto
"""
import bleach


def limpiar_contenido(contenido):
    """
    Limpia y sanitiza contenido HTML permitiendo solo etiquetas seguras
    
    Args:
        contenido (str): Contenido HTML a limpiar
        
    Returns:
        str: Contenido limpiado y sanitizado con enlaces seguros
    """
    allowed_tags = ['b', 'i', 'u', 'p', 'br', 'a']
    allowed_attributes = {
        'a': ['href', 'title', 'rel', 'target']
    }

    contenido_limpio = bleach.clean(
        contenido,
        tags=allowed_tags,
        attributes=allowed_attributes,
        protocols=['http', 'https'],
        strip=True
    )

    def set_target_blank(attrs, new=False):
        """Añade atributos de seguridad a los enlaces"""
        attrs[(None, "target")] = "_blank"
        attrs[(None, "rel")] = "noopener noreferrer"
        return attrs

    resultado = bleach.linkify(contenido_limpio, callbacks=[set_target_blank])
    return resultado
