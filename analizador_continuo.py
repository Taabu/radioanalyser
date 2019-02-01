# coding=utf-8
# __author__ = 'Mario Romera Fernández'

import datetime
import glob
import os
import wave
import numpy as np
from MySQLdb.cursors import DictCursor
from dejavuCAPTOR.recognize import AudioRecognizer
from varsUtilsCaptorRadioV2 import cargar_conexion_mysql_local, cargar_djv_local


def cargarProgramas(inicio_anuncio, cursor):
    dias_semana = {0: "D",
                   1: "L",
                   2: "M",
                   3: "X",
                   4: "J",
                   5: "V",
                   6: "S",
                   7: "D"}

    query = (u"SELECT codigo "
             u"FROM captor.programas "
             u"WHERE dia_semana = '{}' "
             u"AND emisora = '{}' "
             u"AND hora_emision < '{}' "
             u"ORDER BY hora_emision DESC LIMIT 1;").format(dias_semana[inicio_anuncio.isoweekday()],
                                                            emisora_cinta["emision"], inicio_anuncio.time())

    cursor.execute(query)
    codigoPrograma = cursor.fetchone()

    return codigoPrograma["codigo"]


def extraer_tiempo_grabacion(archivo):
    """

    :param archivo: nombre del archivo
    :return: datetime.datetime
    """
    nombre = os.path.splitext(os.path.basename(archivo))[0]
    anho = int(nombre[0:4])
    mes = int(nombre[4:6])
    dia = int(nombre[6:8])
    hora = int(nombre[8:10])
    minuto = int(nombre[10:12])
    segundo = int(nombre[12:14])
    milisegundo = 0
    return datetime.datetime(anho, mes, dia, hora, minuto, segundo, milisegundo), nombre


def reconocedor(audio_file, djv, cnx, emisora):
    cursor_mysql = cnx_mysql.cursor(DictCursor)

    SOLAPE = 3
    TAMANHO_CORTE = 10

    nuevos = 0
    actualizados = 0

    wav = wave.open(audio_file, "r")
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = wav.getparams()

    inicio_grabacion, nombre_cinta = extraer_tiempo_grabacion(audio_file)

    for i in np.arange(0, nframes, framerate * SOLAPE):

        wav.setpos(i)
        frames = wav.readframes(TAMANHO_CORTE * framerate)

        s = np.fromstring(frames, np.int16)
        s = s[:]

        anuncio_encontrado = djv.recognize(AudioRecognizer, s)
        if anuncio_encontrado["confidence"] > 150:
            t = datetime.timedelta(seconds=int(i / 44100)) + inicio_grabacion  # tiempo al inicio del trozo a analizar
            t2 = t - datetime.timedelta(seconds=np.ceil(anuncio_encontrado["offset_seconds"]))  # inicio del anuncio
            t3 = t2 + datetime.timedelta(seconds=anuncio_encontrado["len"])  # final del anuncio
            cursor_mysql.execute("SELECT * FROM songs WHERE song_id = %s", (anuncio_encontrado["song_id"],))
            anuncio_original = cursor_mysql.fetchone()

            cursor_mysql.execute(
                "SELECT * FROM ocurrencias WHERE nombre_cinta = %s and emisora_anuncio = %s and anho = %s and mes = %s "
                "and dia = %s and hora = %s and minuto = %s and segundo < %s and segundo > %s",
                (nombre_cinta, emisora, t2.year, t2.month, t2.day, t2.hour, t2.minute, t2.second + 10, t2.second - 10))
            coincidendias = cursor_mysql.fetchall()

            if len(coincidendias) == 0:
                cursor_mysql.execute(
                    "INSERT INTO ocurrencias (fecha_anuncio, id_anuncio, emisora_anuncio, duracion_anuncio, "
                    "nombre_cinta, confidence, codigo_medio, grupo, cadena, emision, anho, mes, dia, hora, minuto, "
                    "segundo, codigo_marca_modelo, nombre_marca, nombre_modelo, compartido, forma_publicidad, "
                    "total_inserciones_bloque, numero_insercion_dentro_bloque, codigo_programa, "
                    "codigo_marketing_directo, codigo_operador, codigo_version, descripcion) VALUES (%s, %s, %s, %s, "
                    "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (datetime.datetime.now(),
                     anuncio_original["song_id"], emisora, anuncio_original["len"], nombre_cinta,
                     anuncio_encontrado["confidence"], 'RD',
                     emisora_cinta["grupo"], emisora_cinta["cadena"], emisora_cinta["emision"], t2.year,
                     t2.month, t2.day, t2.hour, t2.minute,
                     t2.second, anuncio_original["codigo_marca_modelo"], anuncio_original["nombre_marca"],
                     anuncio_original["nombre_modelo"],
                     anuncio_original["compartido"], "", "", "", cargarProgramas(t2, cursor_mysql), "", "",
                     anuncio_original["song_id"], anuncio_original["texto_mencion"]))
                cnx.commit()
                nuevos += 1
            else:
                borrados = 0
                for coincidencia in coincidendias:
                    if int(anuncio_encontrado["song_id"]) == int(coincidencia["codigo_version"]):
                        borrados += 1
                        if int(anuncio_encontrado["confidence"]) > int(coincidencia["confidence"]):
                            cursor_mysql.execute(
                                "DELETE FROM ocurrencias WHERE id_anuncio=%s and fecha_anuncio=%s and nombre_cinta=%s "
                                "and emisora_anuncio=%s",
                                (coincidencia["codigo_version"], coincidencia["fecha_anuncio"], nombre_cinta, emisora))
                            cnx.commit()
                            borrados -= 1
                    else:
                        borrados += 1
                        if datetime.datetime(year=int(coincidencia["anho"]), month=int(coincidencia["mes"]),
                                             day=int(coincidencia["dia"]), hour=int(coincidencia["hora"]),
                                             minute=int(coincidencia["minuto"]),
                                             second=int(coincidencia["segundo"])) \
                                + datetime.timedelta(seconds=int(coincidencia["duracion_anuncio"])) > t2:
                            if int(anuncio_encontrado["confidence"]) > int(coincidencia["confidence"]):
                                cursor_mysql.execute("DELETE FROM ocurrencias WHERE id_anuncio=%s and fecha_anuncio=%s",
                                                     (coincidencia["codigo_version"], coincidencia["fecha_anuncio"]))
                                cnx.commit()
                                borrados -= 1

                if borrados == 0:
                    cursor_mysql.execute(
                        "INSERT INTO ocurrencias (fecha_anuncio, id_anuncio, emisora_anuncio, duracion_anuncio, "
                        "nombre_cinta, confidence, codigo_medio, grupo, cadena, emision, anho, mes, dia, hora, minuto, "
                        "segundo, codigo_marca_modelo, nombre_marca, nombre_modelo, compartido, forma_publicidad, "
                        "total_inserciones_bloque, numero_insercion_dentro_bloque, codigo_programa, "
                        "codigo_marketing_directo, codigo_operador, codigo_version, descripcion) VALUES (%s, %s, %s, "
                        "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, "
                        "%s, %s)",
                        (datetime.datetime.now(),
                         anuncio_original["song_id"], emisora, anuncio_original["len"], nombre_cinta,
                         anuncio_encontrado["confidence"], 'RD',
                         emisora_cinta["grupo"], emisora_cinta["cadena"], emisora_cinta["emision"], t2.year,
                         t2.month, t2.day, t2.hour, t2.minute,
                         t2.second, anuncio_original["codigo_marca_modelo"], anuncio_original["nombre_marca"],
                         anuncio_original["nombre_modelo"],
                         anuncio_original["compartido"], "", "", "", cargarProgramas(t2, cursor_mysql), "", "",
                         anuncio_original["song_id"], anuncio_original["texto_mencion"]))
                    cnx.commit()
                    actualizados += 1

    return nuevos, actualizados


if __name__ == "__main__":

    lista_carpetas = [("E:\\finde\\archivos\prueba_analizador_continuo", 2)]

    carpeta = lista_carpetas[0][0]
    emisora = lista_carpetas[0][1]

    cnx_mysql = cargar_conexion_mysql_local()
    djv = cargar_djv_local()

    while True:

        emisora_cinta = {}

        if emisora == 1:
            emisora_cinta = {"grupo": "GSER", "cadena": "CSER", "emision": "SERC"}
        elif emisora == 2:
            emisora_cinta = {"grupo": "INTE", "cadena": "INTE", "emision": "INTE"}
        elif emisora == 3:
            emisora_cinta = {"grupo": "ESRA", "cadena": "ESRA", "emision": "ESRM"}

        cont = 0
        for wav in glob.glob("{}/*.wav".format(carpeta)):
            tiempo_inicial = datetime.datetime.now()
            nuevos, actualizados = reconocedor(wav, djv, cnx_mysql, emisora)
            tiempo_final = datetime.datetime.now()
            cont += 1
            print "Anuncios nuevos:{}".format(nuevos)
            print "Anuncios actualizados:{}".format(actualizados)
            print "Tiempo empleado:{}".format(tiempo_final - tiempo_inicial)
            print "Terminado archivo:{} {}".format(wav, emisora_cinta["grupo"] + "/" + emisora_cinta["cadena"] + "/" +
                                                   emisora_cinta["emision"])
            print "\n"
            break
        break
