import csv
import json
import pygame
import os


def leer_csv(ruta):
    """Lee las categorías y elementos desde un archivo CSV.

    Args:
        ruta: Ruta al archivo CSV con los datos del juego.

    Returns:
        list: Lista de diccionarios con los elementos leídos,
        donde el campo 'dificultad' se convierte a entero.
    """
    lista_elementos = []
    with open(ruta, mode="r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            if "dificultad" in fila:
                fila["dificultad"] = int(fila["dificultad"])
            lista_elementos.append(fila)
    return lista_elementos


def guardar_resultado_json(ruta, datos):
    """Guarda estadísticas finales en JSON de forma acumulativa.

    Lee el archivo existente (si lo hay), agrega los nuevos datos
    a la lista y sobreescribe el archivo con la lista actualizada.

    Args:
        ruta: Ruta al archivo JSON de resultados.
        datos: Diccionario con las estadísticas a guardar.
    """
    lista_datos = []

    if os.path.exists(ruta):
        try:
            with open(ruta, "r") as archivo:
                contenido = json.load(archivo)
                if isinstance(contenido, list):
                    lista_datos = contenido
                else:
                    lista_datos = [contenido]
        except (json.JSONDecodeError, ValueError):
            lista_datos = []

    lista_datos.append(datos)

    with open(ruta, "w") as archivo:
        json.dump(lista_datos, archivo, indent=4)


def cargar_imagen(nombre, tamanio):
    """Carga y escala una imagen desde la carpeta assets/img.

    Args:
        nombre: Nombre del archivo de imagen.
        tamanio: Tupla (ancho, alto) para escalar la imagen.

    Returns:
        pygame.Surface: Superficie con la imagen escalada, o una
        superficie roja si la imagen no se encuentra.
    """
    ruta = os.path.join("assets", "img", nombre)
    resultado = None
    try:
        img = pygame.image.load(ruta).convert_alpha()
        resultado = pygame.transform.scale(img, tamanio)
    except:
        superficie = pygame.Surface(tamanio)
        superficie.fill((200, 0, 0))
        resultado = superficie
    return resultado


def cargar_sonido(ruta, volumen=1.0):
    """Carga un archivo de sonido con volumen configurable.

    Args:
        ruta: Ruta al archivo de sonido.
        volumen: Nivel de volumen inicial entre 0.0 y 1.0.

    Returns:
        pygame.mixer.Sound: Objeto de sonido configurado.
    """
    sonido = pygame.mixer.Sound(ruta)
    sonido.set_volume(volumen)
    return sonido
