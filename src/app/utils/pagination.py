"""
Utilidades de paginación
"""
from ..config import POSTS_POR_PAGINA


def generar_paginas(pagina_actual, total_paginas, rango=2):
    """
    Genera un listado de números de página para mostrar en paginación
    Muestra siempre la primera y última, plus rango alrededor de la actual
    
    Args:
        pagina_actual (int): Número de página actual
        total_paginas (int): Total de páginas disponibles
        rango (int): Rango de páginas a mostrar alrededor de la actual. Default: 2
        
    Returns:
        list: Lista con números de página e indicadores de "..."
    """
    paginas = []

    for p in range(1, total_paginas + 1):
        if (
            p == 1 or
            p == total_paginas or
            abs(p - pagina_actual) <= rango
        ):
            paginas.append(p)
        elif paginas and paginas[-1] != "...":
            paginas.append("...")

    return paginas


def obtener_datos_paginados(cursor, consulta_datos, consulta_total, params_datos=(),
                            params_total=(), pagina=None):
    """
    Ejecuta una consulta paginada y devuelve los resultados junto con metadata de paginación
    
    Args:
        cursor: Cursor de base de datos
        consulta_datos (str): SELECT principal con placeholders para (%s, %s) al final (LIMIT y OFFSET)
        consulta_total (str): SELECT COUNT(*) para obtener el total
        params_datos (tuple): Parámetros para consulta_datos (sin LIMIT ni OFFSET)
        params_total (tuple): Parámetros para consulta_total
        pagina (int): Número de página actual
        
    Returns:
        tuple: (resultados, paginas) - Resultados paginados y lista de páginas a mostrar
    """
    offset = (pagina - 1) * POSTS_POR_PAGINA
    cursor.execute(consulta_total, params_total)
    total = cursor.fetchone()['total']

    cursor.execute(consulta_datos, (*params_datos, POSTS_POR_PAGINA, offset))
    resultados = cursor.fetchall()

    total_paginas = (total + POSTS_POR_PAGINA - 1) // POSTS_POR_PAGINA
    paginas = generar_paginas(pagina, total_paginas)
    return resultados, paginas
