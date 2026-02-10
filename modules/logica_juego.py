import time
import random
import pygame
from modules.config import *
from modules.visuales import *
from modules.utilidades import leer_csv, guardar_resultado_json


class Juego:
    """Clase principal que gestiona el estado y la lógica del juego.

    Administra las pantallas (inicio, juego, transición, final),
    la selección de cartas, la verificación de grupos, los comodines,
    el sistema de vidas/reintentos y la persistencia de estadísticas.

    Attributes:
        estados: Diccionario con los estados de pantalla activos.
        nombre: Nombre del jugador ingresado en la pantalla de inicio.
        nivel_actual: Número del nivel en curso.
        vidas: Cantidad de vidas restantes del jugador.
        puntaje_acumulado: Puntos totales acumulados.
        tablero: Lista de elementos activos en el tablero.
        comodines: Diccionario con la disponibilidad de cada comodín.
    """

    def __init__(self, ruta_csv: str, sonidos: dict):
        """Inicializa una nueva instancia del juego.

        Args:
            ruta_csv: Ruta al archivo CSV con los elementos del juego.
            sonidos: Diccionario con los objetos de sonido precargados.
        """
        self.estados = {
            "inicio": True,
            "jugando": False,
            "transicion": False,
            "final": False,
        }
        self.nombre = ""
        self.input_rect = pygame.Rect(ANCHO // 2 - 150, ALTO // 2 - 30, 300, 45)
        self.input_activo = False

        self.elementos_totales = leer_csv(ruta_csv)
        self.nivel_actual = 1
        self.vidas = VIDAS_INICIALES
        self.reinicios_nivel = REINICIOS_MAXIMOS
        self.puntaje_acumulado = 0

        self.tablero = []
        self.seleccionados = []
        self.categorias_completadas = []

        self.tiempos_niveles = []
        self.tiempo_inicio_nivel = 0
        self.timer_error = 0
        self.timer_transicion = 0
        self.comodines = {"pista": True, "par": True, "vida": True}
        self.pista_activa = None
        self.timer_pista = 0

        self.pausado = False
        self.sonido_activo = True
        self.tiempo_pausado = 0
        self.tiempo_pausa_inicio = 0

        self.sonidos = sonidos
        self.volumen = 1.0

        self.mezclar_tablero()

    def _reproducir_sonido(self, nombre: str):
        """Reproduce un sonido si el sonido está activo.

        Args:
            nombre: Clave del sonido en el diccionario de sonidos.
        """
        if self.sonido_activo and nombre in self.sonidos:
            self.sonidos[nombre].play()

    def procesar_teclado(self, evento):
        """Gestiona el ingreso de texto cuando el input está activo.

        Permite escribir el nombre del jugador en la pantalla de inicio,
        limitado a 12 caracteres, con soporte para borrar y confirmar.

        Args:
            evento: Evento de tipo KEYDOWN de Pygame.
        """
        if self.estados["inicio"] and self.input_activo:
            if evento.key == pygame.K_BACKSPACE:
                self.nombre = self.nombre[:-1]
            elif evento.key == pygame.K_RETURN and self.nombre:
                self.cambiar_pantalla("inicio", "jugando")
            else:
                if len(self.nombre) < 12:
                    self.nombre += evento.unicode

    def ejecutar_eventos(self, pos: tuple):
        """Maneja los clics del mouse según el estado actual del juego.

        Delega el procesamiento al método correspondiente según la
        pantalla activa (inicio, jugando o final).

        Args:
            pos: Tupla (x, y) con la posición del clic.
        """
        if self.timer_error > 0:
            pass
        elif self.estados["inicio"]:
            self._eventos_inicio(pos)
        elif self.estados["jugando"]:
            self._eventos_jugando(pos)
        elif self.estados["final"]:
            self._eventos_final(pos)

    def _eventos_inicio(self, pos: tuple):
        """Maneja los clics en la pantalla de inicio.

        Activa/desactiva el campo de texto y detecta el clic
        en el botón de jugar.

        Args:
            pos: Tupla (x, y) con la posición del clic.
        """
        if self.input_rect.collidepoint(pos):
            self.input_activo = True
        else:
            self.input_activo = False

        btn_jugar = pygame.Rect(ANCHO // 2 - 100, ALTO // 2 + 80, 200, 50)
        if btn_jugar.collidepoint(pos) and self.nombre:
            self._reproducir_sonido("menu_select")
            self.cambiar_pantalla("inicio", "jugando")

    def _eventos_jugando(self, pos: tuple):
        """Maneja los clics durante el juego.

        Procesa primero los botones de control y, si no se presionó
        ninguno y el juego no está pausado, procesa los clics en
        el tablero y los comodines.

        Args:
            pos: Tupla (x, y) con la posición del clic.
        """
        boton_control_presionado = self._procesar_botones_control(pos)

        if not boton_control_presionado and not self.pausado:
            self._procesar_clicks_tablero(pos)
            self._procesar_clicks_comodines(pos)

    def _procesar_botones_control(self, pos: tuple) -> bool:
        """Procesa clics en los botones de control del HUD inferior.

        Incluye los botones de pausa, reiniciar, salir, sonido
        y controles de volumen.

        Args:
            pos: Tupla (x, y) con la posición del clic.

        Returns:
            bool: True si se presionó algún botón de control.
        """
        btn_pausa = pygame.Rect(20, ALTO - 50, 100, 40)
        btn_reiniciar = pygame.Rect(130, ALTO - 50, 120, 40)
        btn_salir = pygame.Rect(260, ALTO - 50, 100, 40)
        btn_sonido = pygame.Rect(370, ALTO - 50, 120, 40)

        if btn_pausa.collidepoint(pos):
            self._toggle_pausa()
            return True
        elif btn_reiniciar.collidepoint(pos):
            self.mezclar_tablero()
            self.reinicios_nivel = REINICIOS_MAXIMOS
            return True
        elif btn_salir.collidepoint(pos):
            pygame.quit()
            import sys

            sys.exit()
        elif btn_sonido.collidepoint(pos):
            self._toggle_sonido()
            return True

        btn_vol_menos = pygame.Rect(500, ALTO - 50, 40, 40)
        btn_vol_mas = pygame.Rect(545, ALTO - 50, 40, 40)

        if btn_vol_menos.collidepoint(pos):
            self._ajustar_volumen(-0.1)
            return True
        elif btn_vol_mas.collidepoint(pos):
            self._ajustar_volumen(0.1)
            return True

        return False

    def _toggle_sonido(self):
        """Activa o desactiva todos los sonidos incluyendo la música de fondo."""
        self.sonido_activo = not self.sonido_activo
        if self.sonido_activo:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

    def _ajustar_volumen(self, delta: float):
        """Ajusta el volumen general del juego.

        Args:
            delta: Valor a sumar al volumen actual, puede ser
            negativo para reducir. Se limita entre 0.0 y 1.0.
        """
        self.volumen = max(0.0, min(1.0, self.volumen + delta))
        pygame.mixer.music.set_volume(self.volumen * 0.3)
        for sonido in self.sonidos.values():
            sonido.set_volume(self.volumen)

    def _toggle_pausa(self):
        """Alterna el estado de pausa y gestiona el tiempo pausado.

        Al pausar, registra el momento de inicio de la pausa.
        Al reanudar, acumula el tiempo transcurrido en pausa.
        """
        if not self.pausado:
            self.tiempo_pausa_inicio = time.time()
            pygame.mixer.music.pause()  
        else:
            self.tiempo_pausado += time.time() - self.tiempo_pausa_inicio
            pygame.mixer.music.unpause()
        self.pausado = not self.pausado

    def _procesar_clicks_tablero(self, pos: tuple):
        """Procesa clics en las cartas del tablero.

        Args:
            pos: Tupla (x, y) con la posición del clic.
        """
        for item in self.tablero:
            if item["rect"].collidepoint(pos):
                self._gestionar_seleccion(item)

    def _procesar_clicks_comodines(self, pos: tuple):
        """Procesa clics en los botones de comodines.

        Verifica si el clic coincide con algún botón de comodín
        disponible y ejecuta la acción correspondiente.

        Args:
            pos: Tupla (x, y) con la posición del clic.
        """
        btn_pista = pygame.Rect(ANCHO - 150, 100, 130, 40)
        btn_par = pygame.Rect(ANCHO - 150, 160, 130, 40)
        btn_vida = pygame.Rect(ANCHO - 150, 220, 130, 40)

        if btn_pista.collidepoint(pos) and self.comodines["pista"]:
            self._reproducir_sonido("menu_select")
            self._usar_comodin_pista()
        elif btn_par.collidepoint(pos) and self.comodines["par"]:
            self._reproducir_sonido("menu_select")
            self._usar_comodin_par()
        elif btn_vida.collidepoint(pos) and self.comodines["vida"]:
            if self.vidas < VIDAS_INICIALES:
                self._reproducir_sonido("menu_select")
                self._usar_comodin_vida()
            else:
                self._reproducir_sonido("error")

    def _eventos_final(self, pos: tuple):
        """Maneja los clics en la pantalla final.

        Detecta si se presionó el botón de reintentar o el de salir.

        Args:
            pos: Tupla (x, y) con la posición del clic.
        """
        btn_retry = pygame.Rect(ANCHO // 2 - 185, ALTO - 100, 170, 50)
        btn_exit = pygame.Rect(ANCHO // 2 + 15, ALTO - 100, 170, 50)

        if btn_retry.collidepoint(pos):
            self._reiniciar_partida()
        elif btn_exit.collidepoint(pos):
            pygame.quit()
            import sys

            sys.exit()

    def _reiniciar_partida(self):
        """Reinicia todos los valores del juego para una nueva partida."""
        self.nivel_actual = 1
        self.puntaje_acumulado = 0
        self.reinicios_nivel = REINICIOS_MAXIMOS
        self.tiempos_niveles = []
        self.nombre = ""
        self.mezclar_tablero()
        self.cambiar_pantalla("final", "inicio")

    def _gestionar_seleccion(self, item):
        """Gestiona la selección y deselección de cartas.

        Permite seleccionar hasta 4 cartas. Si ya hay 4 seleccionadas,
        se verifica automáticamente el grupo.

        Args:
            item: Diccionario con los datos de la carta seleccionada.
        """
        if item in self.seleccionados:
            self.seleccionados.remove(item)
        elif len(self.seleccionados) < 4:
            self.seleccionados.append(item)
            if len(self.seleccionados) == 4:
                self.verificar_grupo()

    def verificar_grupo(self):
        """Valida si los 4 elementos seleccionados pertenecen a la misma categoría."""
        if self._es_grupo_valido():
            self._procesar_acierto()
        else:
            self._procesar_error()

    def _es_grupo_valido(self) -> bool:
        """Verifica si todos los elementos seleccionados comparten categoría.

        Returns:
            bool: True si todos los seleccionados tienen la misma categoría.
        """
        cat = self.seleccionados[0]["categoria"]
        return all(i["categoria"] == cat for i in self.seleccionados)

    def _procesar_acierto(self):
        """Procesa un agrupamiento correcto.

        Reproduce sonido, mueve las cartas a completadas, suma puntos
        y verifica si se completó el nivel.
        """
        self._reproducir_sonido("acierto")
        self.categorias_completadas.append(list(self.seleccionados))
        for i in self.seleccionados:
            self.tablero.remove(i)
        self.puntaje_acumulado += 100
        self.seleccionados = []
        if len(self.tablero) == 0:
            self.finalizar_nivel()

    def _procesar_error(self):
        """Procesa un agrupamiento incorrecto.

        Reproduce sonido de error, resta una vida y activa el timer
        de visualización del error.
        """
        self._reproducir_sonido("error")
        self.vidas -= 1
        self.timer_error = pygame.time.get_ticks() + 1000

    def finalizar_nivel(self):
        """Calcula el tiempo del nivel y avanza al siguiente o finaliza el juego.

        Si quedan niveles por completar, inicia la transición al siguiente.
        Si se completaron todos, guarda las estadísticas como ganador.
        """
        duracion = time.time() - self.tiempo_inicio_nivel - self.tiempo_pausado
        self.tiempos_niveles.append(duracion)
        if self.nivel_actual < CANT_NIVELES:
            self._reproducir_sonido("next_level")
            self.nivel_actual += 1
            self.timer_transicion = pygame.time.get_ticks() + TIEMPO_TRANSICION
            self.cambiar_pantalla("jugando", "transicion")
        else:
            self.guardar_estadisticas(ganador=True)
            self.cambiar_pantalla("jugando", "final")

    def guardar_estadisticas(self, ganador=False):
        """Guarda las estadísticas del juego en un archivo JSON.

        Args:
            ganador: Indica si el jugador completó todos los niveles.
        """
        from datetime import datetime

        estadisticas = {
            "nombre": self.nombre,
            "puntaje": self.puntaje_acumulado,
            "nivel_alcanzado": self.nivel_actual,
            "niveles_completados": (
                self.nivel_actual - 1 if not ganador else self.nivel_actual
            ),
            "tiempos_por_nivel": [round(t, 2) for t in self.tiempos_niveles],
            "tiempo_total": round(sum(self.tiempos_niveles), 2),
            "ganador": ganador,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        guardar_resultado_json("data/resultados.json", estadisticas)


    def mezclar_tablero(self, es_reintento=False):
        """Reinicia el tablero para el nivel actual."""
        categorias_validas = self._obtener_categorias_validas()
    
        if not categorias_validas:
            print(f"ERROR: No hay categorías para el nivel {self.nivel_actual}")
            return
    
        elementos_seleccionados = self._seleccionar_elementos_aleatorios(categorias_validas)
        self._preparar_tablero(elementos_seleccionados, es_reintento)

    
    def _obtener_categorias_validas(self):
    
        grupos_temporales = {}
        
        for elemento in self.elementos_totales:
            
            dificultad_elem = elemento.get("dificultad", 1)
            
            if dificultad_elem == self.nivel_actual:
                categoria = elemento["categoria"]
                
                if categoria not in grupos_temporales:
                    grupos_temporales[categoria] = []
                grupos_temporales[categoria].append(elemento)

        resultado_final = {}
        
        for categoria, lista_items in grupos_temporales.items():
            
            if len(lista_items) == 4:
                resultado_final[categoria] = lista_items

        return resultado_final

    def _seleccionar_elementos_aleatorios(self, categorias_dict):
        """Selecciona 4 categorías aleatorias y retorna sus elementos."""
        cantidad = min(4, len(categorias_dict))
        
        if cantidad < 4:
            print(f"AVISO: Nivel {self.nivel_actual} tiene solo {cantidad} categorías.")
        
        categorias_seleccionadas = random.sample(list(categorias_dict.keys()), cantidad)
        
        elementos = []
        for cat in categorias_seleccionadas:
            elementos.extend(categorias_dict[cat])
        
        return elementos

    def _preparar_tablero(self, elementos, es_reintento):
        """Mezcla elementos y resetea el estado del nivel."""
        self.tablero = elementos
        random.shuffle(self.tablero)
        
        self.categorias_completadas = []
        self.seleccionados = []
        
        if not es_reintento:
            self.vidas = VIDAS_INICIALES
            self.reinicios_nivel = REINICIOS_MAXIMOS
        
        self.tiempo_inicio_nivel = time.time()
        self.tiempo_pausado = 0

    def _usar_comodin_pista(self):
        """Muestra una pista visual sobre una carta aleatoria durante 3 segundos.

        Selecciona una carta al azar del tablero y la marca con un
        indicador numérico temporal.
        """
        if self.tablero:
            carta_pista = random.choice(self.tablero)

            self.pista_activa = carta_pista
            self.timer_pista = pygame.time.get_ticks() + 3000
            self.comodines["pista"] = False

    def _usar_comodin_par(self):
        """Selecciona automáticamente 2 elementos de la misma categoría.

        Limpia la selección actual, elige una categoría al azar
        del tablero y preselecciona 2 de sus elementos.
        """
        if self.tablero:
            self.seleccionados = []

            categorias_en_tablero = {}
            for item in self.tablero:
                cat = item["categoria"]
                if cat not in categorias_en_tablero:
                    categorias_en_tablero[cat] = []
                categorias_en_tablero[cat].append(item)

            categoria = random.choice(list(categorias_en_tablero.keys()))
            elementos = categorias_en_tablero[categoria][:2]
            self.seleccionados = elementos
            self.comodines["par"] = False

    def _usar_comodin_vida(self):
        """Recupera una vida perdida, sin exceder el máximo de vidas iniciales."""
        if self.vidas < VIDAS_INICIALES:
            self.vidas += 1
        self.comodines["vida"] = False

    def cambiar_pantalla(self, de: str, a: str):
        """Cambia el estado activo entre pantallas del juego.

        Args:
            de: Nombre de la pantalla a desactivar.
            a: Nombre de la pantalla a activar.
        """
        self.estados[de] = False
        self.estados[a] = True

    def dibujar(self, pantalla, fuente, fuente_g):
        """Orquesta el dibujo según el estado de pantalla activo.

        Args:
            pantalla: Superficie principal de Pygame.
            fuente: Fuente de tamaño normal para textos del HUD.
            fuente_g: Fuente de tamaño grande para títulos.
        """
        if self.estados["inicio"]:
            self._dibujar_inicio(pantalla, fuente, fuente_g)
        elif self.estados["jugando"]:
            self._actualizar_estado_jugando()
            self._dibujar_jugando(pantalla, fuente)
        elif self.estados["transicion"]:
            self._actualizar_transicion()
            self._dibujar_transicion(pantalla, fuente_g)
        elif self.estados["final"]:
            self._dibujar_final(pantalla, fuente, fuente_g)

    def _dibujar_inicio(self, pantalla, fuente, fuente_g):
        """Dibuja la pantalla de inicio delegando al módulo visuales.

        Args:
            pantalla: Superficie principal de Pygame.
            fuente: Fuente normal.
            fuente_g: Fuente grande.
        """
        dibujar_inicio(
            pantalla,
            fuente_g,
            fuente,
            self.nombre,
            self.input_rect,
            self.input_activo,
        )

    def _actualizar_estado_jugando(self):
        """Actualiza el estado del juego sin renderizar.

        Verifica si se acabaron las vidas para reiniciar el nivel
        o terminar la partida, y limpia la selección tras un error.
        """
        tiempo_actual = pygame.time.get_ticks()

        if self.vidas <= 0 and self.timer_error == 0:
            if self.reinicios_nivel > 0:
                self.reinicios_nivel -= 1
                self.vidas = VIDAS_INICIALES
                self.mezclar_tablero(es_reintento=True)
            else:
                self._reproducir_sonido("game_over")
                self.guardar_estadisticas(ganador=False)
                self.cambiar_pantalla("jugando", "final")

        if self.timer_error > 0 and tiempo_actual > self.timer_error:
            self.seleccionados = []
            self.timer_error = 0

    def _dibujar_jugando(self, pantalla, fuente):
        """Dibuja la pantalla de juego con tablero, comodines, HUD y controles.

        Args:
            pantalla: Superficie principal de Pygame.
            fuente: Fuente para textos del juego.
        """
        dibujar_tablero(pantalla, self, fuente)
        dibujar_comodines(pantalla, self, fuente)
        self._dibujar_hud(pantalla, fuente)
        dibujar_botones_control(pantalla, self, fuente)

    def _dibujar_hud(self, pantalla, fuente):
        """Dibuja el HUD superior con puntos, vidas, reintentos, timer y nivel.

        Args:
            pantalla: Superficie principal de Pygame.
            fuente: Fuente para los textos del HUD.
        """
        txt_puntos = fuente.render(
            f"PUNTOS: {self.puntaje_acumulado}", True, (255, 215, 0)
        )
        txt_vidas = fuente.render(f"VIDAS: {self.vidas}", True, (255, 100, 100))
        txt_reinicios = fuente.render(
            f"REINTENTOS: {self.reinicios_nivel}/{REINICIOS_MAXIMOS}",
            True,
            (200, 200, 200),
        )

        if self.pausado:
            tiempo_transcurrido = int(
                self.tiempo_pausa_inicio - self.tiempo_inicio_nivel - self.tiempo_pausado
            )
        else:
            tiempo_transcurrido = int(
                time.time() - self.tiempo_inicio_nivel - self.tiempo_pausado
            )
        minutos = tiempo_transcurrido // 60
        segundos = tiempo_transcurrido % 60
        txt_timer = fuente.render(
            f"TIEMPO: {minutos:02d}:{segundos:02d}", True, (100, 200, 255)
        )

        txt_nivel = fuente.render(
            f"NIVEL: {self.nivel_actual}/{CANT_NIVELES}", True, (150, 255, 150)
        )

        pantalla.blit(txt_puntos, (20, 10))
        pantalla.blit(txt_vidas, (200, 10))
        pantalla.blit(txt_reinicios, (350, 10))
        pantalla.blit(txt_timer, (560, 10))
        pantalla.blit(txt_nivel, (720, 10))

    def _actualizar_transicion(self):
        """Actualiza el estado de la transición entre niveles.

        Cuando el timer expira, mezcla el tablero y cambia a la
        pantalla de juego.
        """
        restante = (self.timer_transicion - pygame.time.get_ticks()) / 1000
        if restante <= 0:
            self.mezclar_tablero()
            self.cambiar_pantalla("transicion", "jugando")

    def _dibujar_transicion(self, pantalla, fuente_g):
        """Dibuja la pantalla de transición entre niveles.

        Args:
            pantalla: Superficie principal de Pygame.
            fuente_g: Fuente grande para el texto de transición.
        """
        restante = (self.timer_transicion - pygame.time.get_ticks()) / 1000
        dibujar_transicion(pantalla, restante, self.nivel_actual, fuente_g)

    def _dibujar_final(self, pantalla, fuente, fuente_g):
        """Dibuja la pantalla final con el resumen de estadísticas.

        Args:
            pantalla: Superficie principal de Pygame.
            fuente: Fuente normal para estadísticas.
            fuente_g: Fuente grande para el título.
        """
        dibujar_pantalla_final(pantalla, self, fuente_g, fuente)
