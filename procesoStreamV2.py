# coding=utf-8
# __author__ = 'Mario Romera Fernández'
# __license__ = 'GNU General Public License v2.0'

"""
Acceso al mezclador estéreo mediante comando FFMPEG que devuelve dos buffers de datosanuncios
Análisis de dichos buffers para
    -Vectorizar
    -Detectar anuncios de la base de datosanuncios
    -Detectar menciones por palabras
Almacenamiento de un wav de un canal a 44100 de duración configurable

PARA DETECTAR PRESENCIA; HA DE SER MAYOR QUE 0.001; en RMS 4.51276e-05
"""

import datetime
import os
import sys
import wave
from socket import gethostname
from subprocess import Popen, PIPE
import numpy as np
from MySQLdb.cursors import DictCursor
from dejavuCAPTOR.recognize import AudioRecognizer
from pocketsphinx import Decoder
from Parametrizador import extractor_audio
from utilidades import to_unicode
from varsUtilsCaptorRadioV2 import NUM_PARAMETROS, cargar_conexion_sql_local, cargar_conexion_mysql_local, \
    cargar_djv_local, cargar_programa_anuncio, extraer_datos_emisora

cnx_as400 = cargar_conexion_sql_local()
cnx_mysql = cargar_conexion_mysql_local()

cursor_as400 = cnx_as400.cursor()
cursor_mysql = cnx_mysql.cursor(DictCursor)

djv = cargar_djv_local()

CODIGO_MEDIO = 'RD'
UMBRAL = 1e-75
vector = np.zeros(NUM_PARAMETROS)
UMBRAL_FINGERPRINT = 150
INTERVALO = 600
VENTANA = 3
LONG_HUELLA = 10
NOMBRE_PC_RED = gethostname()
RUTA_ARCHIVOS = "C:/CaptoRadio/archivos"
RUTA_RED = u"\\\\\\\\{}\\\\{}".format(NOMBRE_PC_RED, "archivos")
FFMPEG_EXE = "C:/ffmpeg/bin/ffmpeg.exe"

NOMBRE_EMISORA = u"INTERECONOMIA CADENA"
ultima_mencion = {"id": 0, "hora": datetime.datetime.min}
t_inicio = datetime.datetime.now()


def reconocer_huella(in_data, djv, inicio_huella, datos_emisora):
    audio = np.fromstring(in_data, np.int16)
    # comparamos con al BBDD de fingerprints cual es el que más se parece
    anuncio_encontrado = djv.recognize(AudioRecognizer, audio)
    # si el audio supera el umbral de coincidencia con un anuncio guardado
    if anuncio_encontrado is None:
        return None
    else:
        if anuncio_encontrado["confidence"] > UMBRAL_FINGERPRINT:

            # extraemos la información del anuncio original
            query = (u"SELECT * "
                     u"FROM songs "
                     u"WHERE song_id = '{}'".format(anuncio_encontrado["song_id"]))
            cursor_mysql.execute(query)
            anuncio_original = cursor_mysql.fetchone()
            # calculamos el inicio del anuncio
            inicio_anuncio = comienzo + inicio_huella - datetime.timedelta(seconds=LONG_HUELLA) - datetime.timedelta(
                microseconds=(VENTANA * 1000000) / 2) - datetime.timedelta(seconds=anuncio_encontrado['offset_seconds'])
            print u"inicio_anuncio: {}".format(inicio_anuncio)

            # extraemos el código del programa al que pertenece el anuncio
            codigo_programa = cargar_programa_anuncio(inicio_anuncio, datos_emisora["onda"], datos_emisora["cadena"],
                                                      datos_emisora["emisora"], cursor_mysql)

            # si existe alguna ocurrencia con un inicio similar extraemos su confidence para compararlo despues
            query = (u"SELECT * "
                     u"FROM ocurrencias "
                     u"WHERE nombre_cinta = '{}' "
                     u"AND emisora_anuncio = '{}' "
                     u"AND fecha_ocurrencia BETWEEN '{}' AND '{}'").format(nombre_archivo, NOMBRE_EMISORA,
                                                                           inicio_anuncio - datetime.timedelta(
                                                                               seconds=10),
                                                                           inicio_anuncio + datetime.timedelta(
                                                                               seconds=anuncio_original["len"]))
            cursor_mysql.execute(query)
            coincidendias = cursor_mysql.fetchall()
            print u"coincidendias {} {}".format(len(coincidendias), coincidendias)

            if len(coincidendias) == 0:
                query = (u"INSERT INTO ocurrencias "
                         u"(fecha_encontrado, fecha_ocurrencia, id_anuncio, emisora_anuncio, duracion_anuncio, "
                         u"nombre_cinta, confidence, codigo_medio, codigo_marca_modelo, nombre_marca, "
                         u"nombre_modelo, compartido, forma_publicidad, total_inserciones_bloque, "
                         u"numero_insercion_dentro_bloque, codigo_programa, codigo_marketing_directo, "
                         u"codigo_operador, descripcion) "
                         u"VALUES ('{}', '{}', '{}', '{}', '{}', "
                         u"'{}', '{}', '{}', '{}', '{}', "
                         u"'{}', '{}', '{}', '{}', "
                         u"'{}', '{}', '{}', "
                         u"'{}', '{}')").format(datetime.datetime.now(), inicio_anuncio,
                                                anuncio_original["song_id"], NOMBRE_EMISORA,
                                                anuncio_original["len"], nombre_archivo,
                                                anuncio_encontrado["confidence"], CODIGO_MEDIO,
                                                anuncio_original["codigo_marca_modelo"],
                                                anuncio_original["nombre_marca"],
                                                anuncio_original["nombre_modelo"],
                                                anuncio_original["compartido"], "", "", "", codigo_programa, "",
                                                "", anuncio_original["texto_mencion"])
                cursor_mysql.execute(query)
                cnx_mysql.commit()
                print u"insert sin coincidencias"
            else:
                borrados = 0
                for coincidencia in coincidendias:
                    if int(anuncio_encontrado["song_id"]) == int(coincidencia["id_anuncio"]):
                        borrados += 1
                        print u"mismo id"
                        if int(anuncio_encontrado["confidence"]) > int(coincidencia["confidence"]):
                            query = (u"DELETE FROM ocurrencias "
                                     u"WHERE id_anuncio='{}' "
                                     u"AND fecha_ocurrencia='{}' "
                                     u"AND nombre_cinta='{}' "
                                     u"AND emisora_anuncio='{}'").format(coincidencia["id_anuncio"],
                                                                         coincidencia["fecha_ocurrencia"],
                                                                         nombre_archivo, NOMBRE_EMISORA)
                            cursor_mysql.execute(query)
                            cnx_mysql.commit()
                            borrados -= 1
                            print u"borrado coincidencia"
                        else:
                            print u"no borrado"
                    else:
                        borrados += 1
                        print u"diferente id"
                        if coincidencia["fecha_ocurrencia"] + datetime.timedelta(
                                seconds=int(coincidencia["duracion_anuncio"])) > inicio_anuncio:
                            print u"coinciden en el tiempo"
                            if int(anuncio_encontrado["confidence"]) > int(coincidencia["confidence"]):
                                query = (u"DELETE FROM ocurrencias "
                                         u"WHERE id_anuncio='{}' "
                                         u"AND fecha_ocurrencia='{}' "
                                         u"AND nombre_cinta='{}' "
                                         u"AND emisora_anuncio='{}'").format(coincidencia["id_anuncio"],
                                                                             coincidencia["fecha_ocurrencia"],
                                                                             nombre_archivo, NOMBRE_EMISORA)
                                cursor_mysql.execute(query)
                                cnx_mysql.commit()
                                borrados -= 1
                                print u"borrado coincidencia diferente id"
                            else:
                                print u"no borrado"
                if borrados == 0:
                    query = (u"INSERT INTO ocurrencias "
                             u"(fecha_encontrado, fecha_ocurrencia, id_anuncio, emisora_anuncio, duracion_anuncio, "
                             u"nombre_cinta, confidence, codigo_medio, codigo_marca_modelo, nombre_marca, "
                             u"nombre_modelo, compartido, forma_publicidad, total_inserciones_bloque, "
                             u"numero_insercion_dentro_bloque, codigo_programa, codigo_marketing_directo, "
                             u"codigo_operador, descripcion) "
                             u"VALUES ('{}', '{}', '{}', '{}', '{}', "
                             u"'{}', '{}', '{}', '{}', '{}', "
                             u"'{}', '{}', '{}', '{}', "
                             u"'{}', '{}', '{}', "
                             u"'{}', '{}')").format(datetime.datetime.now(), inicio_anuncio,
                                                    anuncio_original["song_id"], NOMBRE_EMISORA,
                                                    anuncio_original["len"], nombre_archivo,
                                                    anuncio_encontrado["confidence"], CODIGO_MEDIO,
                                                    anuncio_original["codigo_marca_modelo"],
                                                    anuncio_original["nombre_marca"],
                                                    anuncio_original["nombre_modelo"],
                                                    anuncio_original["compartido"], "", "", "", codigo_programa, "",
                                                    "", anuncio_original["texto_mencion"])
                    cursor_mysql.execute(query)
                    cnx_mysql.commit()
                    print u"actualizado coincidencias"
        return anuncio_encontrado


def parametrizar(datos_buffer, nomfile):
    global vector
    vector_aux = extractor_audio(datos_buffer, 44100)
    vector = np.vstack((vector_aux, vector))


def guardar_wav(buffer, nombre, fs, numc):
    nombre_wav = os.path.basename(nombre)
    output = wave.open(nombre, 'w')
    output.setparams((numc, 2, fs, 1, 'NONE', 'not compressed'))
    output.writeframes(buffer)
    output.close()
    with cnx_mysql:
        query = (u"INSERT INTO cintas "
                 u"(nombre_cinta, emisora_cinta, estado_cinta, vector_cinta, targets_cinta, usuario_cinta) "
                 u"VALUES ('{}', '{}', '{}', '{}', '{}', '{}')").format(RUTA_RED + u"\\\\" + nombre_wav,
                                                                        NOMBRE_EMISORA, u"A",
                                                                        RUTA_RED + u"\\\\" + nombre_archivo + u".npy",
                                                                        RUTA_RED + u"\\\\" + nombre_archivo + u".txt",
                                                                        1)
        cursor_mysql.execute(query)


def add_word_dictionary(palabra):
    vocales_k = u"aouáóú"
    vocales_j = u"eiéí"
    palabra = to_unicode(palabra)
    letras = u""
    saltar_letra = False
    with open("C:/sphinx/voxforge-es-0.2/etc/voxforge_es_sphinx.dic", "a") as diccionario:
        for index, letra in enumerate(palabra):
            if not saltar_letra:
                try:
                    if letra == u"r" and index == 0:
                        letras += u"rr "
                    elif letra == u"c" and palabra[index + 1] == u"h":
                        letras += u"ch "
                        saltar_letra = True
                    elif letra == u"r" and palabra[index + 1] == u"r":
                        letras += u"rr "
                        saltar_letra = True
                    elif letra == u"c" and palabra[index + 1] in vocales_k:
                        letras = letras + u"k " + palabra[index + 1] + u" "
                        saltar_letra = True
                    elif letra == u"c" and palabra[index + 1] in vocales_j:
                        letras = letras + u"z " + palabra[index + 1] + u" "
                        saltar_letra = True
                    elif letra == u"q" and palabra[index + 1] == u"u":
                        letras += u"k "
                        saltar_letra = True
                    elif letra == u"g" and palabra[index + 1] == u"u":
                        letras += u"g "
                        saltar_letra = True
                    elif letra == u"g" and palabra[index + 1] in vocales_j:
                        letras += letras + u"j " + palabra[index + 1] + u" "
                        saltar_letra = True
                    elif letra == u"l" and palabra[index + 1] == u"l":
                        letras += u"ll "
                        saltar_letra = True
                    elif letra == u"ñ":
                        letras += u"gn "
                    elif letra == u"v":
                        letras += u"b "
                    elif letra == u"ü":
                        letras += u"u "
                    else:
                        letras += u"{}".format(letra + " ")
                except IndexError:
                    letras += u"{}".format(letra + " ")
            else:
                saltar_letra = False
        letras = letras[:-1]
        aescribir = palabra + u" " + letras + "\n"

        print u"añadido {}".format(aescribir)

        diccionario.write(aescribir.encode("utf-8"))


def reconocer(buf, decoder, menciones):
    global ultima_mencion
    for mencion in menciones:
        abuscar = mencion["texto_mencion"].replace("...", " ").replace(".", " ").lower().encode("utf-8")
        decoder.set_keyphrase('kw', abuscar)
        decoder.set_search('kw')
        in_speech_bf = True
        decoder.start_utt()

        texto = []
        inicio_mencion = comienzo + datetime.timedelta(seconds=contador * VENTANA)

        hipotesis = ''

        if buf:
            decoder.process_raw(buf, False, False)

            try:
                if decoder.hyp().hypstr != '':
                    # en decoder.hyp esta la cadena entera de reconocidos, en hipotesis tambien se va actualizando
                    if decoder.hyp().hypstr != hipotesis:
                        hipotesis = decoder.hyp().hypstr

                        print 'encontrado en: '
                        print 'Partial decoding result:', decoder.hyp().hypstr
                        texto.append(hipotesis)

            except AttributeError:
                pass

            if decoder.get_in_speech():
                sys.stdout.write('.')
                sys.stdout.flush()
            if decoder.get_in_speech() != in_speech_bf:
                in_speech_bf = decoder.get_in_speech()

                if not in_speech_bf:
                    decoder.end_utt()
                    try:
                        if decoder.hyp().hypstr != '':
                            print 'Resultado parcial:', decoder.hyp().hypstr

                    except AttributeError:
                        pass
                    hipotesis = ''
                    decoder.start_utt()

        if texto:
            print 'resultados'
            print texto
            print mencion["song_id"], ultima_mencion["id"]
            if mencion["song_id"] != ultima_mencion["id"] and abs(
                            inicio_mencion - ultima_mencion["hora"]).seconds > 300:
                # extraemos la información del anuncio original
                query = (u"SELECT * "
                         u"FROM songs "
                         u"WHERE song_id = '{}'".format(mencion["song_id"]))
                cursor_mysql.execute(query)
                anuncio_original = cursor_mysql.fetchone()
                # extraemos el código del programa al que pertenece el anuncio
                codigo_programa = cargar_programa_anuncio(inicio_mencion, datos_emisora["onda"],
                                                          datos_emisora["cadena"],
                                                          datos_emisora["emisora"], cursor_mysql)
                query = (u"INSERT INTO ocurrencias "
                         u"(fecha_encontrado, fecha_ocurrencia, id_anuncio, emisora_anuncio, duracion_anuncio, "
                         u"nombre_cinta, confidence, codigo_medio, codigo_marca_modelo, nombre_marca, "
                         u"nombre_modelo, compartido, forma_publicidad, total_inserciones_bloque, "
                         u"numero_insercion_dentro_bloque, codigo_programa, codigo_marketing_directo, "
                         u"codigo_operador, descripcion) "
                         u"VALUES ('{}', '{}', '{}', '{}', '{}', "
                         u"'{}', '{}', '{}', '{}', '{}', "
                         u"'{}', '{}', '{}', '{}', "
                         u"'{}', '{}', '{}', "
                         u"'{}', '{}')").format(datetime.datetime.now(), inicio_mencion,
                                                anuncio_original["song_id"], NOMBRE_EMISORA,
                                                anuncio_original["len"], nombre_archivo,
                                                0, CODIGO_MEDIO,
                                                anuncio_original["codigo_marca_modelo"],
                                                anuncio_original["nombre_marca"],
                                                anuncio_original["nombre_modelo"],
                                                anuncio_original["compartido"], anuncio_original["forma_publicidad"],
                                                "",
                                                "", codigo_programa, "",
                                                "", anuncio_original["texto_mencion"])
                cursor_mysql.execute(query)
                cnx_mysql.commit()
                ultima_mencion = {"id": anuncio_original["song_id"], "hora": inicio_mencion}


if __name__ == '__main__':

    datos_emisora = extraer_datos_emisora(NOMBRE_EMISORA, cursor_mysql)

    # comando de lectura de ffmpeg, 2 buffers, 0 - 16 kHz, 1 - 44.1 kHz
    ffmpeg = [
        Popen([
            FFMPEG_EXE,
            "-f", "dshow",
            "-i", "audio=Mezcla est\xe9reo (Realtek High Definition Audio)",
            "-acodec", "pcm_s16le",
            "-ac", "1",
            "-ar", "16000", "-f", "s16le",
            "-"], shell=True, stdout=PIPE, stderr=open(os.devnull, "w")),
        Popen([
            FFMPEG_EXE,
            "-f", "dshow",
            "-i", "audio=Mezcla est\xe9reo (Realtek High Definition Audio)",
            "-af", 'volume=1dB',  # IMPORTANTE -- audio subido para vector
            "-acodec", "pcm_s16le",
            "-ac", "1",
            "-ar", "44100", "-f", "s16le",
            "-"],
            shell=True, stdout=PIPE, stderr=open(os.devnull, "w"))]

    ##-----------------CONFIGURACION DEL SISTEMA DE PALABRAS EN MENCIONES--------------------##

    # añadimos las menciones a buscar
    query = (u"SELECT song_id, texto_mencion "
             u"FROM songs "
             u"WHERE forma_publicidad = 'ME' or 'MP' or 'MC';")
    cursor_mysql.execute(query)
    menciones = cursor_mysql.fetchall()
    palabras_dic = []
    with open("C:/sphinx/voxforge-es-0.2/etc/voxforge_es_sphinx.dic", "r") as f:
        for line in f:
            palabras_dic.append(to_unicode(line.split()[0]))
    for mencion in menciones:
        for palabra in mencion["texto_mencion"].replace("...", " ").replace(".", " ").lower().split():
            palabra_a_comparar = to_unicode(palabra.lower())
            if palabra_a_comparar not in palabras_dic:
                add_word_dictionary(palabra_a_comparar)
                palabras_dic.append(palabra_a_comparar)

    hmdir = "C:/sphinx/voxforge-es-0.2/model_parameters/voxforge_es_sphinx.cd_ptm_3000"
    lmdir = 'C:/sphinx/voxforge-es-0.2/etc/voxforge_es_sphinx.transcription.test.lm'
    dictd = 'C:/sphinx/voxforge-es-0.2/etc/voxforge_es_sphinx.dic'

    config = Decoder.default_config()
    config.set_string('-hmm', hmdir)
    config.set_string('-lm', lmdir)
    config.set_string('-dict', dictd)
    config.set_float('-kws_threshold', 1e-75)
    decoder = Decoder(config)

    # comienzo en tiempo real
    # -------------------------
    comienzo = datetime.datetime.now()
    print u"Empieza el proceso en: {}".format(comienzo.strftime("%H:%M:%S"))
    nombre_archivo = comienzo.strftime("%Y%m%d%H%M%S").decode("ASCII")

    mv = ''
    parahuella = ''
    paramencion = ''
    buftotal = ''
    menciones_encontradas = []
    reconocido = []
    contador = 0
    while datetime.datetime.now() < comienzo + datetime.timedelta(seconds=INTERVALO):

        # BUFFERS
        buf16 = ffmpeg[0].stdout.read(16000 * VENTANA * 2)
        buf44 = ffmpeg[1].stdout.read(44100 * VENTANA * 2)

        buf_int = np.fromstring(buf44, np.int16)
        buf_data = buf_int.astype('float32') / 32767.0

        tam44 = len(buf44)
        tam16 = len(buf16)
        if np.sqrt(np.mean(np.square(buf_data))) < UMBRAL:
            print np.sqrt(np.mean(np.square(buf_data)))
            print u"en silencio"
        else:
            inicio_huella = datetime.timedelta(seconds=contador * VENTANA)
            parametrizar(buf_data, os.path.join(RUTA_ARCHIVOS, nombre_archivo + '.npy'))

            # menciones
            if len(paramencion) >= tam16 * LONG_HUELLA / VENTANA:
                reconocer(paramencion, decoder, menciones)
                paramencion = paramencion[tam16:] + buf16
            else:
                paramencion += buf16

            # anuncios
            if len(parahuella) >= tam44 * LONG_HUELLA / VENTANA:
                reconocer_huella(parahuella, djv, inicio_huella, datos_emisora)
                parahuella = parahuella[tam44:] + buf44

            else:
                parahuella += buf44

        contador += 1
        buftotal += buf44

    print u"Acaba el intervalo, guardamos el *npy y el *wav"
    print os.path.join(RUTA_ARCHIVOS, nombre_archivo)
    np.save(os.path.join(RUTA_ARCHIVOS, nombre_archivo + '.npy'), vector[:-1])
    guardar_wav(buftotal, os.path.join(RUTA_ARCHIVOS, nombre_archivo + '.wav'), 44100, 1)
    cnx_mysql.close()
    print datetime.datetime.now() - t_inicio
