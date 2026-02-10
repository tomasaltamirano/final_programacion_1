import time
import random
import pygame
from modules.config import *
from modules.visuales import *
from modules.utilidades import leer_csv, guardar_resultado_json


class Juego:
    def __init__(self, ruta_csv: str, sonidos: dict):
        # 1. Estados del juego
        self.estados = {
            "inicio": True,
            "jugando": False,
            "transicion": False,
            "final": False,
        }
        # 2. Datos del Usuario
        self.nombre = ""
        self.input_rect = pygame.Rect(ANCHO // 2 - 150, ALTO // 2 - 30, 300, 45)
        self.input_activo = False

        # 3. Progresión y Puntuación
        self.elementos_totales = leer_csv(ruta_csv)
        self.nivel_actual = 1
        self.vidas = VIDAS_INICIALES
        self.reinicios_nivel = REINICIOS_MAXIMOS  # Reintentos disponibles para el nivel actual
        self.puntaje_acumulado = 0

        # 4. Lógica de Tablero
        self.tablero = []
        self.seleccionados = []
        self.categorias_completadas = []

        # 5. Tiempos y Comodines
        self.tiempos_niveles = []
        self.tiempo_inicio_nivel = 0
        self.timer_error = 0
        self.timer_transicion = 0
        self.comodines = {"pista": True, "par": True, "vida": True}
        self.pista_activa = None  # Guarda info de la pista mostrada
        self.timer_pista = 0  # Timer para mostrar la pista

        # 6. Controles adicionales
        self.pausado = False
        self.sonido_activo = True
        self.tiempo_pausado = 0  # Tiempo acumulado en pausa
        self.tiempo_pausa_inicio = 0  # Momento en que se pausó

        # 7. Sonidos
        self.sonidos = sonidos
        self.volumen = 1.0  # Volumen general (0.0 a 1.0)

        self.mezclar_tablero()

    def _reproducir_sonido(self, nombre: str):
        """Reproduce un sonido si el sonido está activo."""
        if self.sonido_activo and nombre in self.sonidos:
            self.sonidos[nombre].play()

    def procesar_teclado(self, evento):
        """Gestiona el ingreso de texto cuando el input está activo."""
        if self.estados["inicio"] and self.input_activo:
            if evento.key == pygame.K_BACKSPACE:
                self.nombre = self.nombre[:-1]
            elif evento.key == pygame.K_RETURN and self.nombre:
                self.cambiar_pantalla("inicio", "jugando")
            else:
                if len(self.nombre) < 12:
                    self.nombre += evento.unicode

    def ejecutar_eventos(self, pos: tuple):
        """Maneja los clics según el estado actual."""
        if self.timer_error > 0:
            pass  # No procesar clicks durante el error
        elif self.estados["inicio"]:
            self._eventos_inicio(pos)
        elif self.estados["jugando"]:
            self._eventos_jugando(pos)
        elif self.estados["final"]:
            self._eventos_final(pos)

    def _eventos_inicio(self, pos: tuple):
        """Maneja los clics en la pantalla de inicio."""
        if self.input_rect.collidepoint(pos):
            self.input_activo = True
        else:
            self.input_activo = False

        btn_jugar = pygame.Rect(ANCHO // 2 - 100, ALTO // 2 + 80, 200, 50)
        if btn_jugar.collidepoint(pos) and self.nombre:
            self._reproducir_sonido("menu_select")
            self.cambiar_pantalla("inicio", "jugando")

    def _eventos_jugando(self, pos: tuple):
        """Maneja los clics durante el juego."""
        # Botones de control (siempre accesibles)
        boton_control_presionado = self._procesar_botones_control(pos)

        # Solo procesar otros clicks si no se presionó un botón de control y no está pausado
        if not boton_control_presionado and not self.pausado:
            self._procesar_clicks_tablero(pos)
            self._procesar_clicks_comodines(pos)

    def _procesar_botones_control(self, pos: tuple) -> bool:
        """Procesa clicks en botones de control. Retorna True si se presionó alguno."""
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

        # Botones de volumen
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
        """Activa/desactiva todos los sonidos incluyendo música de fondo."""
        self.sonido_activo = not self.sonido_activo
        if self.sonido_activo:
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

    def _ajustar_volumen(self, delta: float):
        """Ajusta el volumen general del juego."""
        self.volumen = max(0.0, min(1.0, self.volumen + delta))
        pygame.mixer.music.set_volume(self.volumen * 0.3)
        for sonido in self.sonidos.values():
            sonido.set_volume(self.volumen)

    def _toggle_pausa(self):
        """Alterna el estado de pausa y gestiona el tiempo pausado."""
        if not self.pausado:
            self.tiempo_pausa_inicio = time.time()
        else:
            self.tiempo_pausado += time.time() - self.tiempo_pausa_inicio
        self.pausado = not self.pausado

    def _procesar_clicks_tablero(self, pos: tuple):
        """Procesa clicks en las cartas del tablero."""
        for item in self.tablero:
            if item["rect"].collidepoint(pos):
                self._gestionar_seleccion(item)

    def _procesar_clicks_comodines(self, pos: tuple):
        """Procesa clicks en los botones de comodines."""
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
            self._reproducir_sonido("menu_select")
            self._usar_comodin_vida()

    def _eventos_final(self, pos: tuple):
        """Maneja los clics en la pantalla final."""
        btn_retry = pygame.Rect(ANCHO // 2 - 185, ALTO - 100, 170, 50)
        btn_exit = pygame.Rect(ANCHO // 2 + 15, ALTO - 100, 170, 50)

        if btn_retry.collidepoint(pos):
            self._reiniciar_partida()
        elif btn_exit.collidepoint(pos):
            pygame.quit()
            import sys

            sys.exit()

    def _reiniciar_partida(self):
        """Reinicia todos los valores para una nueva partida."""
        self.nivel_actual = 1
        self.puntaje_acumulado = 0
        self.reinicios_nivel = REINICIOS_MAXIMOS
        self.tiempos_niveles = []
        self.nombre = ""
        self.mezclar_tablero()
        self.cambiar_pantalla("final", "inicio")

    def _gestionar_seleccion(self, item):
        if item in self.seleccionados:
            self.seleccionados.remove(item)
        elif len(self.seleccionados) < 4:
            self.seleccionados.append(item)
            if len(self.seleccionados) == 4:
                self.verificar_grupo()

    def verificar_grupo(self):
        """Valida la categoría de los 4 elementos seleccionados."""
        if self._es_grupo_valido():
            self._procesar_acierto()
        else:
            self._procesar_error()

    def _es_grupo_valido(self) -> bool:
        """Verifica si todos los elementos seleccionados son de la misma categoría."""
        cat = self.seleccionados[0]["categoria"]
        return all(i["categoria"] == cat for i in self.seleccionados)

    def _procesar_acierto(self):
        """Procesa cuando el jugador agrupa correctamente."""
        self._reproducir_sonido("acierto")
        self.categorias_completadas.append(list(self.seleccionados))
        for i in self.seleccionados:
            self.tablero.remove(i)
        self.puntaje_acumulado += 100
        self.seleccionados = []
        # Pasar de nivel cuando el tablero esté vacío
        if len(self.tablero) == 0:
            self.finalizar_nivel()

    def _procesar_error(self):
        """Procesa cuando el jugador agrupa incorrectamente."""
        self._reproducir_sonido("error")
        self.vidas -= 1  # Solo resta vida
        self.timer_error = pygame.time.get_ticks() + 1000
        # La verificación de muerte se hace en el update o loop principal

    def finalizar_nivel(self):
        """Calcula tiempo y avanza o termina el juego."""
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
        """Guarda las estadísticas del juego en un archivo JSON."""
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
        # Reinicia el tablero para el nivel actual con 4 categorías de la dificultad correspondiente.

        # 1. Filtrar elementos por dificultad del nivel actual
        elementos_nivel = [
            elem
            for elem in self.elementos_totales
            if elem.get("dificultad", 1) == self.nivel_actual
        ]

        # 2. Agrupar elementos por categoría
        categorias_dict = {}
        for elemento in elementos_nivel:
            cat = elemento["categoria"]
            if cat not in categorias_dict:
                categorias_dict[cat] = []
            categorias_dict[cat].append(elemento)

        # 3. Filtrar solo las categorías que tienen 4 elementos completos
        categorias_completas = [
            cat for cat, items in categorias_dict.items() if len(items) == 4
        ]

        # 4. Seleccionar 4 categorías al azar (o menos si no hay suficientes)
        cantidad = min(4, len(categorias_completas))
        if cantidad < 4:
            print(
                f"AVISO: Nivel {self.nivel_actual} tiene solo {len(categorias_completas)} categorías. Usando todas."
            )

        if cantidad == 0:
            print(f"ERROR: No hay categorías para el nivel {self.nivel_actual}")
        else:
            categorias_seleccionadas = random.sample(categorias_completas, cantidad)

            # 5. Construir el tablero con los elementos de las categorías seleccionadas
            self.tablero = []
            for cat in categorias_seleccionadas:
                self.tablero.extend(categorias_dict[cat])

            # 6. Mezclar el tablero para que no estén agrupados
            random.shuffle(self.tablero)

            # 7. Resetear estado
            self.categorias_completadas = []
            self.seleccionados = []
            # Solo resetear vidas y reintentos si no es un reintento (el reintento ya las restauró antes)
            if not es_reintento:
                self.vidas = VIDAS_INICIALES
                self.reinicios_nivel = REINICIOS_MAXIMOS  # Restaurar reintentos para el nuevo nivel
            self.tiempo_inicio_nivel = time.time()
            self.tiempo_pausado = 0  # Resetear tiempo pausado

    def _usar_comodin_pista(self):
        """Marca una carta aleatoria del tablero con el número 1 por 3 segundos."""
        if self.tablero:
            # Elegir una carta al azar del tablero
            carta_pista = random.choice(self.tablero)

            self.pista_activa = carta_pista  # Guardamos la referencia a la carta
            self.timer_pista = pygame.time.get_ticks() + 3000  # 3 segundos
            self.comodines["pista"] = False

    def _usar_comodin_par(self):
        """Selecciona automáticamente 2 elementos de la misma categoría."""
        if self.tablero:
            # Limpiar selección actual
            self.seleccionados = []

            # Obtener una categoría del tablero actual
            categorias_en_tablero = {}
            for item in self.tablero:
                cat = item["categoria"]
                if cat not in categorias_en_tablero:
                    categorias_en_tablero[cat] = []
                categorias_en_tablero[cat].append(item)

            # Elegir una categoría al azar y seleccionar 2 elementos
            categoria = random.choice(list(categorias_en_tablero.keys()))
            elementos = categorias_en_tablero[categoria][:2]
            self.seleccionados = elementos
            self.comodines["par"] = False

    def _usar_comodin_vida(self):
        """Recupera una vida perdida (máximo 3)."""
        if self.vidas < VIDAS_INICIALES:
            self.vidas += 1
        self.comodines["vida"] = False

    def cambiar_pantalla(self, de: str, a: str):
        self.estados[de] = False
        self.estados[a] = True

    def dibujar(self, pantalla, fuente, fuente_g):
        """Orquesta el dibujo según el estado activo."""
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
        """Dibuja la pantalla de inicio."""
        dibujar_inicio(
            pantalla,
            fuente_g,
            fuente,
            self.nombre,
            self.input_rect,
            self.input_activo,
        )

    def _actualizar_estado_jugando(self):
        """Actualiza el estado del juego (sin renderizar)."""
        tiempo_actual = pygame.time.get_ticks()

        # Si se acabaron las vidas del intento actual
        if self.vidas <= 0 and self.timer_error == 0:
            if self.reinicios_nivel > 0:
                # CASO A: Aún quedan reinicios -> Reiniciamos el nivel
                self.reinicios_nivel -= 1
                self.vidas = VIDAS_INICIALES  # Restauramos las vidas
                self.mezclar_tablero(es_reintento=True)  # Mezclamos las MISMAS cartas
                # Opcional: Mostrar mensaje "Nivel Reiniciado. Intentos restantes: X"
            else:
                # CASO B: No quedan reinicios -> Game Over real
                self._reproducir_sonido("game_over")
                self.guardar_estadisticas(ganador=False)
                self.cambiar_pantalla("jugando", "final")

        # Limpiar selección después del error
        if self.timer_error > 0 and tiempo_actual > self.timer_error:
            self.seleccionados = []
            self.timer_error = 0

    def _dibujar_jugando(self, pantalla, fuente):
        """Dibuja la pantalla de juego."""
        dibujar_tablero(pantalla, self, fuente)
        dibujar_comodines(pantalla, self, fuente)
        self._dibujar_hud(pantalla, fuente)
        dibujar_botones_control(pantalla, self, fuente)

    def _dibujar_hud(self, pantalla, fuente):
        """Dibuja el HUD con puntos, vidas, reintentos, timer y nivel."""
        txt_puntos = fuente.render(
            f"PUNTOS: {self.puntaje_acumulado}", True, (255, 215, 0)
        )
        txt_vidas = fuente.render(f"VIDAS: {self.vidas}", True, (255, 100, 100))
        txt_reinicios = fuente.render(
            f"REINTENTOS: {self.reinicios_nivel}/{REINICIOS_MAXIMOS}",
            True,
            (200, 200, 200),
        )

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
        """Actualiza el estado de la transición."""
        restante = (self.timer_transicion - pygame.time.get_ticks()) / 1000
        if restante <= 0:
            self.mezclar_tablero()
            self.cambiar_pantalla("transicion", "jugando")

    def _dibujar_transicion(self, pantalla, fuente_g):
        """Dibuja la pantalla de transición."""
        restante = (self.timer_transicion - pygame.time.get_ticks()) / 1000
        dibujar_transicion(pantalla, restante, self.nivel_actual, fuente_g)

    def _dibujar_final(self, pantalla, fuente, fuente_g):
        """Dibuja la pantalla final."""
        dibujar_pantalla_final(pantalla, self, fuente_g, fuente)
