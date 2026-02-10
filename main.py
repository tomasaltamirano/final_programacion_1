import pygame
import sys
from modules.logica_juego import Juego
from modules.config import ANCHO, ALTO, FPS
from modules.utilidades import cargar_sonido

pygame.init()
pygame.mixer.init()
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Agrupados UTN - Examen Final")
reloj = pygame.time.Clock()

fuente_n = pygame.font.SysFont("Silkscreen", 15, bold=True)
fuente_g = pygame.font.SysFont("Silkscreen", 15, bold=True)

sonidos = {
    "menu_select": cargar_sonido("assets/sounds/Menu_Select.wav", 0.5),
    "next_level": cargar_sonido("assets/sounds/next_level.mp3", 0.5),
    "acierto": cargar_sonido("assets/sounds/pickupCoin.wav", 0.5),
    "error": cargar_sonido("assets/sounds/wrong.mp3", 0.5),
    "game_over": cargar_sonido("assets/sounds/you_lose.mp3", 0.5),
}

pygame.mixer.music.load("assets/sounds/Soundtrack.mp3")
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1)

juego = Juego("data/datos.csv", sonidos)

ejecutando = True
while ejecutando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False

        elif evento.type == pygame.MOUSEBUTTONDOWN:
            juego.ejecutar_eventos(evento.pos)

        elif evento.type == pygame.KEYDOWN:
            juego.procesar_teclado(evento)

    juego.dibujar(pantalla, fuente_n, fuente_g)
    pygame.display.flip()
    reloj.tick(FPS)

pygame.quit()
sys.exit()
