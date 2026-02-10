import pygame
from modules.config import *
from modules.utilidades import cargar_imagen


def dibujar_inicio(pantalla, fuente_g, fuente_n, nombre, rect_input, activo):
    """Dibuja el menú de inicio con el campo de ingreso de nombre.

    Args:
        pantalla: Superficie principal de Pygame.
        fuente_g: Fuente grande para el título.
        fuente_n: Fuente normal para etiquetas y botón.
        nombre: Texto actual del nombre ingresado.
        rect_input: Rectángulo del campo de texto.
        activo: Indica si el campo de texto está activo.

    Returns:
        pygame.Rect: Rectángulo del botón "JUGAR".
    """
    pantalla.fill(COLOR_FONDO)

    txt_titulo = fuente_g.render("AGRUPADOS UTN", True, COLOR_CORRECTO)
    pantalla.blit(txt_titulo, txt_titulo.get_rect(center=(ANCHO // 2, 100)))

    txt_label = fuente_n.render("INGRESE SU NOMBRE:", True, COLOR_TEXTO)
    pantalla.blit(txt_label, txt_label.get_rect(center=(ANCHO // 2, ALTO // 2 - 60)))

    color_border = COLOR_SELECCION if activo else (150, 150, 150)
    pygame.draw.rect(pantalla, (50, 50, 50), rect_input, border_radius=5)
    pygame.draw.rect(pantalla, color_border, rect_input, 3, border_radius=5)

    txt_nombre = fuente_n.render(nombre, True, COLOR_TEXTO)
    pantalla.blit(txt_nombre, (rect_input.x + 10, rect_input.y + 10))

    btn_rect = pygame.Rect(ANCHO // 2 - 100, ALTO // 2 + 80, 200, 50)
    pygame.draw.rect(pantalla, (50, 150, 50), btn_rect, border_radius=10)

    txt_play = fuente_n.render("JUGAR", True, (255, 255, 255))
    pantalla.blit(txt_play, txt_play.get_rect(center=btn_rect.center))

    return btn_rect


def dibujar_pantalla_final(pantalla, juego, fuente_grande, fuente_chica):
    """Dibuja la pantalla final con resumen de estadísticas.

    Muestra el resultado (victoria o derrota), puntaje, niveles
    completados, vidas restantes y tiempos por nivel.

    Args:
        pantalla: Superficie principal de Pygame.
        juego: Instancia de la clase Juego con el estado actual.
        fuente_grande: Fuente para el título.
        fuente_chica: Fuente para las estadísticas y botones.

    Returns:
        tuple: Tupla con los rectángulos (btn_retry, btn_exit).
    """
    pantalla.fill((20, 20, 30))

    gano = juego.vidas > 0 and juego.nivel_actual >= CANT_NIVELES
    
    titulo = "¡FELICITACIONES!" if gano else "GAME OVER"
    color_titulo = (100, 255, 100) if gano else COLOR_ERROR
    txt_titulo = fuente_grande.render(titulo, True, color_titulo)
    pantalla.blit(txt_titulo, txt_titulo.get_rect(center=(ANCHO // 2, 80)))

    stats = [
        f"Jugador: {juego.nombre}",
        f"Puntaje Final: {juego.puntaje_acumulado}",
        f"Niveles Completados: {len(juego.tiempos_niveles)} / {CANT_NIVELES}",
        f"Vidas Restantes: {max(0, juego.vidas)}",
    ]
    
    if juego.tiempos_niveles:
        tiempo_total = sum(juego.tiempos_niveles)
        minutos = int(tiempo_total) // 60
        segundos = int(tiempo_total) % 60
        stats.append(f"Tiempo Total: {minutos:02d}:{segundos:02d}")
        
        for i, tiempo in enumerate(juego.tiempos_niveles):
            m = int(tiempo) // 60
            s = int(tiempo) % 60
            stats.append(f"  Nivel {i+1}: {m:02d}:{s:02d}")

    y_offset = 140
    for linea in stats:
        txt = fuente_chica.render(linea, True, COLOR_TEXTO)
        pantalla.blit(txt, txt.get_rect(center=(ANCHO // 2, y_offset)))
        y_offset += 30

    btn_retry = pygame.Rect(ANCHO // 2 - 185, ALTO - 100, 170, 50)
    btn_exit = pygame.Rect(ANCHO // 2 + 15, ALTO - 100, 170, 50)

    pygame.draw.rect(pantalla, (50, 150, 50), btn_retry, border_radius=5)
    pygame.draw.rect(pantalla, (150, 50, 50), btn_exit, border_radius=5)

    txt_retry = fuente_chica.render("REINTENTAR", True, COLOR_TEXTO)
    txt_exit = fuente_chica.render("SALIR", True, COLOR_TEXTO)

    pantalla.blit(txt_retry, txt_retry.get_rect(center=btn_retry.center))
    pantalla.blit(txt_exit, txt_exit.get_rect(center=btn_exit.center))

    return btn_retry, btn_exit


def dibujar_tablero(pantalla, juego, fuente):
    """Dibuja las categorías completadas y la grilla de cartas restantes.

    Las categorías completadas se muestran en la parte superior con
    sus imágenes o textos. La grilla de cartas activas se muestra
    debajo, con colores que indican el estado de selección.

    Args:
        pantalla: Superficie principal de Pygame.
        juego: Instancia de la clase Juego con el estado actual.
        fuente: Fuente para los textos de las cartas.
    """
    pantalla.fill(COLOR_FONDO)

    y_offset = 50
    for categoria_lista in juego.categorias_completadas:
        nombre_cat = categoria_lista[0]["categoria"]
        txt_cat = fuente.render(f"Categoría: {nombre_cat}", True, COLOR_CORRECTO)
        pantalla.blit(txt_cat, (100, y_offset))

        for i, item in enumerate(categoria_lista):
            x = 100 + (i * (TAMANIO_CARD + 10))
            y = y_offset + 31
            rect = pygame.Rect(x, y, TAMANIO_CARD, TAMANIO_CARD // 2)

            if "imagen" in item:
                img = cargar_imagen(
                    item["imagen"], (TAMANIO_CARD - 40, TAMANIO_CARD - 40)
                )
                img_rect = img.get_rect(center=rect.center)
                pantalla.blit(img, img_rect)
            else:
                texto = fuente.render(item["elemento"], True, (0, 0, 0))
                pantalla.blit(texto, texto.get_rect(center=rect.center))

        y_offset += TAMANIO_CARD // 2 + 50

    grid_y_start = y_offset + 20
    for i, item in enumerate(juego.tablero):
        col, fila = i % 4, i // 4
        x = col * (TAMANIO_CARD + MARGEN) + 100
        y = fila * (TAMANIO_CARD + MARGEN) + grid_y_start

        rect = pygame.Rect(x, y, TAMANIO_CARD, TAMANIO_CARD)
        item["rect"] = rect

        color = COLOR_CARD
        if item in juego.seleccionados:
            if (
                len(juego.seleccionados) > 1
                and item["categoria"] != juego.seleccionados[0]["categoria"]
            ):
                color = COLOR_ERROR
            else:
                color = COLOR_SELECCION

        pygame.draw.rect(pantalla, color, rect, border_radius=10)

        if "imagen" in item:
            img = cargar_imagen(item["imagen"], (TAMANIO_CARD - 10, TAMANIO_CARD - 10))
            img_rect = img.get_rect(center=rect.center)
            pantalla.blit(img, img_rect)
        else:
            texto = fuente.render(item["elemento"], True, COLOR_TEXTO)
            pantalla.blit(texto, texto.get_rect(center=rect.center))
        
        if juego.pista_activa == item and juego.timer_pista > pygame.time.get_ticks():
            pygame.draw.circle(pantalla, (200, 50, 50), (rect.x + 20, rect.y + 20), 18)
            pygame.draw.circle(pantalla, (255, 255, 255), (rect.x + 20, rect.y + 20), 18, 2)
            txt_num = fuente.render("1", True, (255, 255, 255))
            pantalla.blit(txt_num, txt_num.get_rect(center=(rect.x + 20, rect.y + 20)))


def dibujar_transicion(pantalla, segundos, nivel_proximo, fuente_grande):
    """Muestra el temporizador de cuenta regresiva entre niveles.

    Args:
        pantalla: Superficie principal de Pygame.
        segundos: Segundos restantes para la transición.
        nivel_proximo: Número del nivel próximo a iniciar.
        fuente_grande: Fuente para el texto de transición.
    """
    pantalla.fill((20, 20, 20))
    msg = f"NIVEL {nivel_proximo} EN {int(segundos) + 1}..."
    txt = fuente_grande.render(msg, True, COLOR_TEXTO)
    pantalla.blit(txt, txt.get_rect(center=(ANCHO // 2, ALTO // 2)))


def dibujar_comodines(pantalla, juego, fuente):
    """Dibuja los 3 botones de comodines en el lateral derecho.

    Muestra los comodines con color activo o gris según su
    disponibilidad, y gestiona la expiración de la pista activa.

    Args:
        pantalla: Superficie principal de Pygame.
        juego: Instancia de la clase Juego con el estado actual.
        fuente: Fuente para los textos de los botones.

    Returns:
        tuple: Tupla con los rectángulos (btn_pista, btn_par, btn_vida).
    """
    btn_pista = pygame.Rect(ANCHO - 150, 100, 130, 40)
    btn_par = pygame.Rect(ANCHO - 150, 160, 130, 40)
    btn_vida = pygame.Rect(ANCHO - 150, 220, 130, 40)

    comodines = [
        (btn_pista, "PISTA", "pista"),
        (btn_par, "PAR", "par"),
        (btn_vida, "VIDA", "vida"),
    ]

    for rect, texto, clave in comodines:
        color = (100, 100, 100) if not juego.comodines[clave] else (200, 150, 50)
        pygame.draw.rect(pantalla, color, rect, border_radius=5)
        txt_surf = fuente.render(texto, True, COLOR_TEXTO)
        pantalla.blit(txt_surf, txt_surf.get_rect(center=rect.center))

    if juego.timer_pista > 0 and juego.timer_pista <= pygame.time.get_ticks():
        juego.pista_activa = None
        juego.timer_pista = 0

    return btn_pista, btn_par, btn_vida


def dibujar_botones_control(pantalla, juego, fuente):
    """Dibuja los botones de control y la barra de volumen en el HUD inferior.

    Incluye botones de pausa, reiniciar, salir, sonido, controles
    de volumen (+/-), barra de volumen visual y overlay de pausa.

    Args:
        pantalla: Superficie principal de Pygame.
        juego: Instancia de la clase Juego con el estado actual.
        fuente: Fuente para los textos de los botones.

    Returns:
        tuple: Tupla con los rectángulos (btn_pausa, btn_reiniciar,
        btn_salir, btn_sonido).
    """
    btn_pausa = pygame.Rect(20, ALTO - 50, 100, 40)
    btn_reiniciar = pygame.Rect(130, ALTO - 50, 120, 40)
    btn_salir = pygame.Rect(260, ALTO - 50, 100, 40)
    btn_sonido = pygame.Rect(370, ALTO - 50, 120, 40)
    
    btn_vol_menos = pygame.Rect(500, ALTO - 50, 40, 40)
    btn_vol_mas = pygame.Rect(545, ALTO - 50, 40, 40)

    color_pausa = (200, 150, 50) if not juego.pausado else (100, 200, 100)
    color_sonido = (100, 200, 100) if juego.sonido_activo else (200, 100, 100)

    pygame.draw.rect(pantalla, color_pausa, btn_pausa, border_radius=5)
    pygame.draw.rect(pantalla, (150, 100, 50), btn_reiniciar, border_radius=5)
    pygame.draw.rect(pantalla, (180, 50, 50), btn_salir, border_radius=5)
    pygame.draw.rect(pantalla, color_sonido, btn_sonido, border_radius=5)
    
    pygame.draw.rect(pantalla, (100, 100, 150), btn_vol_menos, border_radius=5)
    pygame.draw.rect(pantalla, (100, 100, 150), btn_vol_mas, border_radius=5)

    txt_pausa = "REANUDAR" if juego.pausado else "PAUSA"
    txt_sonido = "SONIDO ON" if juego.sonido_activo else "SONIDO OFF"

    textos = [
        (btn_pausa, txt_pausa),
        (btn_reiniciar, "REINICIAR"),
        (btn_salir, "SALIR"),
        (btn_sonido, txt_sonido),
        (btn_vol_menos, "-"),
        (btn_vol_mas, "+"),
    ]

    for rect, texto in textos:
        txt_surf = fuente.render(texto, True, COLOR_TEXTO)
        pantalla.blit(txt_surf, txt_surf.get_rect(center=rect.center))

    barra_x = 595
    barra_y = ALTO - 45
    barra_ancho = 80
    barra_alto = 30
    
    pygame.draw.rect(pantalla, (50, 50, 50), (barra_x, barra_y, barra_ancho, barra_alto), border_radius=3)
    relleno_ancho = int(barra_ancho * juego.volumen)
    if relleno_ancho > 0:
        pygame.draw.rect(pantalla, (100, 200, 100), (barra_x, barra_y, relleno_ancho, barra_alto), border_radius=3)
    txt_vol = fuente.render(f"{int(juego.volumen * 100)}%", True, COLOR_TEXTO)
    pantalla.blit(txt_vol, txt_vol.get_rect(center=(barra_x + barra_ancho // 2, barra_y + barra_alto // 2)))

    if juego.pausado:
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        pantalla.blit(overlay, (0, 0))
        txt_pause = fuente.render("JUEGO EN PAUSA", True, (255, 255, 255))
        pantalla.blit(txt_pause, txt_pause.get_rect(center=(ANCHO // 2, ALTO // 2)))

    return btn_pausa, btn_reiniciar, btn_salir, btn_sonido
