# coding=utf-8
# __author__ = 'Mario Romera Fernández'

"""
Proyecto Captor 2015
Ejecutable por linea de comandos para indexar vectores en zonas de posibles anuncios

Uso:
>>indexador.py -ruta_orig c:/ruta/de/vectores.npy -ruta_indices c:/ruta/de/indices.txt -m sklearn.modeloelegido
O directamente ejecutado por IDE (con los parametros por defecto)

"""
import numpy as np
from sklearn.preprocessing import Imputer
import sys
import os
import glob
from Utils import storage, features
import argparse
import datetime
import Parametrizador
import pylab as plt


def bloques_porlinea():
    parser = argparse.ArgumentParser(
        description='Funcion que detecta los posibles segundos donde estan los bloques de anuncios de un archivo '
                    'vectorizado, con un modelo previamente entrenado')
    parser.add_argument('--ruta_archivos', default='D:\\archivos_captor\\pruebas',
                        help='Ruta de origen de los vectores y audios')
    parser.add_argument('-m', '--modelo', default='D:\\archivos_captor\modelos\ExtraTreesClassifier_Apr0816.pkl',
                        help='modelo clasificador')
    parser.add_argument('--ruta_indices', default='D:\\archivos_captor', help='Ruta donde dejar los txt con indices')
    args = parser.parse_args()

    vectorpath = args.ruta_archivos + '/*.npy'
    rutamodelo, modelo = os.path.split(args.modelo)
    model = storage.load_model(modelo, ruta=rutamodelo)

    # Booleano para uso de umbral de deteccion distinto a 0.5 por medio de la prediccion con probabilidad
    probabilidad = False

    print '\nModelo Clasificador: ', model

    # Bucle que recorre todos los archivos de la ruta
    for vectorname in glob.glob(vectorpath):

        nomfile = os.path.split(vectorname)[1].split('.')[0]
        nompath = os.path.split(vectorname)[0]
        print 'Indexando archivo: ' + nomfile
        vector = np.load(vectorname)
        tamvector = len(vector)
        # sampleRate, audio = wavfileread(os.path.join(nompath, nomaudio))
        if len(vector) == 0:
            print 'error en la carga de archivos'
            print sys.exit()

        # Prediccion
        if probabilidad:
            try:
                y = model.predict_proba(vector)
                yp = [i[1] for i in y]
                probabilidad = True
            except:
                print 'no se puede obtener probabilidades con este metodo'
                probabilidad = False
            # NUEVO UMBRAL DE DETECCION
            umbral = 0.4
            y_test = np.zeros(len(yp), dtype=np.bool)
            for pos, m in enumerate(yp):
                if m > umbral:
                    y_test[pos] = 1
        else:
            try:
                y_test = model.predict(vector)
            except:
                # posibles casos de fallo en la prediccion
                # - Que tenga en el vector valores Inf o NaN - se pueden sustituir

                imp = Imputer(missing_values='NaN', strategy='mean', axis=0)

                vector = imp.fit_transform(vector)
                y_test = model.predict(vector)
            y_test = y_test.astype(np.bool)

        # Prediccion
        tam = len(y_test)
        y_test = features.filtrado_binario(y_test, 3)
        # Primer procesado del resultado : zonas rellenando positivos aislados
        y_zonas = np.zeros(tam, dtype=np.bool)
        # intervalo de recorrido por el resultado
        intervalo = 25
        for pos in np.arange(0, tam, intervalo):
            if np.sum(y_test[pos:pos + intervalo]) > 1 and pos > (2 * intervalo):
                y_zonas[pos - (2 * intervalo):pos + (2 * intervalo)] = 1
            elif np.sum(y_test[pos:pos + intervalo]) > 1 and pos <= (2 * intervalo):
                y_zonas[0:pos + (2 * intervalo)] = 1

        # Unimos el resultado con el procesado por no dejar ningun positivo de momento
        plantilla = y_zonas + y_test

        # Union entre dos positivos o zonas de positivos cercanas (menos de 50 s)
        posant = 0
        for posicion, valor in enumerate(plantilla):

            if valor and 0 < (posicion - posant) < 50:
                plantilla[posant:posicion] = 1
                posant = posicion
            if valor:
                posant = posicion

        # Filtramos (quitamos aislados)
        plantilla_final = features.filtrado_binario(plantilla, 1)
        # Pasamos a tipo int
        plantilla_final = plantilla_final.astype(np.int16)

        # INDEXACION -- DONDE PUEDEN ENCONTRARSE LOS BLOQUES DE ANUNCIOS

        inicios = np.where(np.diff(plantilla_final) == 1)[0] + 1
        finales = np.where(np.diff(plantilla_final) == -1)[0] + 1

        if np.size(inicios) > np.size(finales):
            finales = np.append(finales, tam)
        elif np.size(inicios) < np.size(finales):
            inicios = np.append(0, inicios)

        indices = zip(inicios, finales)

        ##ESCRIBIMOS ARCHIVO DE TEXTO FINAL
        with open(os.path.join(args.ruta_indices, nomfile + '_indices' + '.txt'), 'wb') as f:
            f.write('INDICES PARA ARCHIVO ' + nomfile)
            for n, bloque in enumerate(indices):
                f.write('\n\n Bloque numero ' + str(n) + ' (' + str(
                    datetime.timedelta(seconds=int(bloque[0]))) + ' - ' + str(
                    datetime.timedelta(seconds=int(bloque[1]))) + ')\n')

            f.write('\n Duracion : ' + str(tamvector))


def bloques_poraudio(nombrearchivo, rutamodelo='D:\\archivos_captor\modelos\ExtraTreesClassifier_Apr0816.pkl'):

    rutamodelo, modelo = os.path.split(rutamodelo)
    model = storage.load_model(modelo, ruta=rutamodelo)
    rutaarchivo, archivo = os.path.split(nombrearchivo)
    nombrebase = archivo.split('.')[0]
    nomfile = os.path.basename(nombrearchivo)
    print 'Indexando archivo: ' + nomfile
    print nombrearchivo
    vector = Parametrizador.extractor(nombrearchivo)

    if len(vector) == 0:
        print 'error en la carga de archivos'
        print sys.exit()
    tiempo = datetime.datetime(int(archivo[:4]), int(archivo[4:6]), int(archivo[6:8]), int(archivo[8:10]),
                               int(archivo[10:12]), int(archivo[12:14]), 0)

    # Prediccion
    try:
        y_test = model.predict(vector)
    except:
        # posibles casos de fallo en la prediccion
        # - Que tenga en el vector valores Inf o NaN - se pueden sustituir

        imp = Imputer(missing_values='NaN', strategy='mean', axis=0)

        vector = imp.fit_transform(vector)
        y_test = model.predict(vector)
        y_test = y_test.astype(np.bool)

    # Prediccion
    tam = len(y_test)
    y_test = features.filtrado_binario(y_test, 3)
    # Primer procesado del resultado : zonas rellenando positivos aislados
    y_zonas = np.zeros(tam, dtype=np.bool)
    # intervalo de recorrido por el resultado
    intervalo = 25

    for pos in np.arange(0, tam, intervalo):
        if np.sum(y_test[pos:pos + intervalo]) > 1 and pos > (2 * intervalo):
            y_zonas[pos - (2 * intervalo):pos + (2 * intervalo)] = 1
        elif np.sum(y_test[pos:pos + intervalo]) > 1 and pos <= (2 * intervalo):
            y_zonas[0:pos + (2 * intervalo)] = 1

    # Unimos el resultado con el procesado por no dejar ningun positivo de momento
    plantilla = y_zonas + y_test

    # Union entre dos positivos o zonas de positivos cercanas (menos de 50 s)
    posant = 0
    for posicion, valor in enumerate(plantilla):
        if valor and 0 < (posicion - posant) < 50:
            plantilla[posant:posicion] = 1
            posant = posicion
        if valor:
            posant = posicion

    # Filtramos (quitamos aislados)
    plantilla_final = features.filtrado_binario(plantilla, 1)
    # Pasamos a tipo int
    plantilla_final = plantilla_final.astype(np.int16)

    # INDEXACION -- DONDE PUEDEN ENCONTRARSE LOS BLOQUES DE ANUNCIOS

    inicios = np.where(np.diff(plantilla_final) == 1)[0] + 1
    finales = np.where(np.diff(plantilla_final) == -1)[0] + 1

    if np.size(inicios) > np.size(finales):
        finales = np.append(finales, tam)
    elif np.size(inicios) < np.size(finales):
        inicios = np.append(0, inicios)

    indices = zip(inicios, finales)
    marcas = {}
    for orden, par in enumerate(indices):
        marcas[nombrebase + '_bloque' + str(orden + 1)] = (
        (tiempo + datetime.timedelta(seconds=int(par[0])), tiempo + datetime.timedelta(seconds=int(par[1]))))
    print marcas
    return marcas


def bloques_porvector(nombrearchivo, rutamodelo='D:\\archivos_captor\modelos\ExtraTreesClassifier_Apr0816.pkl'):
    """suponemos que nombrearchivo es la ruta del archivo, wav o vector (npy)"""

    rutamodelo, modelo = os.path.split(rutamodelo)
    model = storage.load_model(modelo, ruta=rutamodelo)
    rutaarchivo, archivo = os.path.split(nombrearchivo)
    nombrebase = archivo.split('.')[0]
    vectorname = nombrebase + '.npy'

    try:
        vector = np.load(os.path.join(rutaarchivo, vectorname))
        print "vector cargado correctamente"
    except:
        print 'No existe el vector, parametrizamos el audio'
        vector = Parametrizador.extractor(nombrearchivo, rutaarchivo)

    if len(vector) == 0:  # or len(vectorname) != 18:
        print 'Error en la carga de archivos'
        print sys.exit()

    # si el nombre no es el formato especifico
    try:
        tiempo = datetime.datetime(int(archivo[:4]), int(archivo[4:6]), int(archivo[6:8]), int(archivo[8:10]),
                                   int(archivo[10:12]), int(archivo[12:14]), 0)

    except:
        tiempo = datetime.datetime.now()

    # Prediccion
    try:
        y_test = model.predict(vector)
    except:
        # posibles casos de fallo en la prediccion
        # - Que tenga en el vector valores Inf o NaN - se pueden sustituir

        imp = Imputer(missing_values='NaN', strategy='mean', axis=0)
        vector = imp.fit_transform(vector)
        y_test = model.predict(vector)
        y_test = y_test.astype(np.bool)

    # Prediccion
    # print y_test
    tam = len(y_test)
    ##quitamos to do lo que tenga menos de 3 segundos
    y_test = features.filtrado_binario(y_test, 4)
    # Primer procesado del resultado : zonas rellenando positivos aislados
    y_zonas = np.zeros(tam, dtype=np.bool)
    # intervalo de recorrido por el resultado  --- inicio 25 s
    intervalo = 25

    for pos in np.arange(0, tam, intervalo):
        if np.sum(y_test[pos:pos + intervalo]) > 1 and pos > (2 * intervalo):
            y_zonas[pos - (2 * intervalo):pos + (2 * intervalo)] = 1
        elif np.sum(y_test[pos:pos + intervalo]) > 1 and pos <= (2 * intervalo):
            y_zonas[0:pos + (2 * intervalo)] = 1

    # Unimos el resultado con el procesado por no dejar ningun positivo de momento
    plantilla = y_zonas + y_test

    # Union entre dos positivos o zonas de positivos cercanas (menos de 50 s)
    posant = 0
    for posicion, valor in enumerate(plantilla):

        if valor and 0 < (posicion - posant) < 50:
            plantilla[posant:posicion] = 1
            posant = posicion
        if valor:
            posant = posicion

    # Filtramos (quitamos aislados)
    plantilla_final = features.filtrado_binario(plantilla, 1)
    # Pasamos a tipo int
    plantilla_final = plantilla_final.astype(np.int16)

    # INDEXACION -- DONDE PUEDEN ENCONTRARSE LOS BLOQUES DE ANUNCIOS

    inicios = np.where(np.diff(plantilla_final) == 1)[0] + 1
    finales = np.where(np.diff(plantilla_final) == -1)[0] + 1

    if np.size(inicios) > np.size(finales):
        finales = np.append(finales, tam)
    elif np.size(inicios) < np.size(finales):
        inicios = np.append(0, inicios)

    indices = zip(inicios, finales)
    print indices
    marcas = {}
    for orden, par in enumerate(indices):
        marcas[nombrebase + '_bloque' + str(orden + 1)] = (
        (tiempo + datetime.timedelta(seconds=int(par[0])), tiempo + datetime.timedelta(seconds=int(par[1]))))
        print (tiempo + datetime.timedelta(seconds=int(par[0]))).time(), (
        tiempo + datetime.timedelta(seconds=int(par[1]))).time()
    return marcas


if __name__ == '__main__':
    bloques_porvector('D:\\i+d\\Captor\\20150329133001_5dB.npy')
