# coding=utf-8
# __author__ = 'Mario Romera Fernández'

"""
Proyecto Captor 2015
Ejecutable por linea de comandos para indexar vectores en zonas de posibles anuncios
Uso:
>>indexador.py -ruta_orig c:/ruta/de/vectores.npy -ruta_indices c:/ruta/de/indices.txt -m sklearn.modeloelegido
"""
import numpy as np
from sklearn.preprocessing import Imputer
import sys
import os
import glob
from Utils import storage, features
import argparse
import pylab as plt

parser = argparse.ArgumentParser(
    description='Funcion que detecta los posibles segundos donde estan los bloques de anuncios de un archivo '
                'vectorizado, con un modelo previamente entrenado')
parser.add_argument('--ruta_archivos', default='D:\\archivos_captor\\pruebas', help='Ruta de origen de los vectores')
parser.add_argument('-m', '--modelo', default='D:\\archivos_captor\modelos\ExtraTreesClassifier_Mar0418.pkl',
                    help='modelo clasificador')
parser.add_argument('--ruta_indices', default='D:\\archivos_captor', help='Ruta donde dejar los txt con indices')
args = parser.parse_args()
path = args.ruta_archivos + '/*.npy'
rutamodelo, modelo = os.path.split(args.modelo)
model = storage.load_model(modelo, ruta=rutamodelo)
probabilidad = False

print '\nModelo Clasificador: ', model

for filename in glob.glob(path):

    nomfile = os.path.split(filename)[1]
    print 'Indexando archivo: ' + nomfile
    vector = np.load(filename)
    tamvector = len(vector)
    if len(vector) == 0:
        print 'error en la carga de archivos'
        print sys.exit()
    try:
        y_test = model.predict(vector)
    except:
        # posibles casos de fallo en la prediccion
        # - Que tenga en el vector valores Inf o NaN - se pueden sustituir
        imp = Imputer(missing_values='NaN', strategy='mean', axis=0)
        vector = imp.fit_transform(vector)
        y_test = model.predict(vector)

    # FILTRO DE ELIMINACION DE POSITIVOS AISLADOS
    tam = len(y_test)

    # SI TIENE EL METODO PROBABILIDAD, SE PUEDE CAMBIAR DE UMBRAL
    try:
        y2 = model.predict_proba(vector)
        y0 = [i[1] for i in y2]
        probabilidad = True
    except:
        print 'no se puede obtener probabilidades con este metodo'
        probabilidad = False

    umbral = 0.35

    if probabilidad:
        y_test = np.zeros(tam, dtype=np.bool)
        for pos, m in enumerate(y0):
            if m > umbral:
                y_test[pos] = 1
    else:
        y_test = y_test.astype(np.bool)

    y_filt = features.filtrado_binario(y_test, 2)
    y_zonas = np.zeros(tam, dtype=np.bool)
    intervalo = 20

    for pos in np.arange(0, tam, intervalo):

        if np.sum(y_test[pos:pos + intervalo]) > 5:
            y_zonas[pos - intervalo:pos + intervalo] = 1
    plantilla = y_zonas + y_filt
    posant = 0
    for posicion, valor in enumerate(plantilla):

        if valor and 0 < (posicion - posant) < 40:
            plantilla[posant:posicion] = 1
            posant = posicion
        if valor:
            posant = posicion
    plantilla_final = features.filtrado_binario(plantilla, 5)

    # INDEXACION -- DONDE PUEDEN ENCONTRARSE LOS BLOQUES DE ANUNCIOS
    plt.figure()
    plt.plot(plantilla_final)
    plt.plot(y_test)
    plt.ylim([-0.01, 1.05])
    plt.show()
    indices = np.where(plantilla_final[:-1] != plantilla_final[1:])[0]
    print 'Limites de los bloques (en segundos)', indices
    np.set_printoptions(threshold=np.nan)
    with open(os.path.join(args.ruta_indices, nomfile + '_index1' + '.txt'), 'wb') as f:
        for n in indices:
            f.write(str(n) + ', ')
    for nc in range(0, len(indices), 2):
        np.save(os.path.join(args.ruta_indices, nomfile.split('.')[0] + '_corte' + str(nc)),
                vector[indices[nc]:indices[nc + 1], :])
