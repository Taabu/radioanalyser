# coding=utf-8
# __author__ = 'Mario Romera Fernández'

"""
Proyecto Captor 2015
Ejecutable por linea de comandos para entrenar un modelo usado en la clasificacion de audios
Uso:
>>entrenador.py -ruta_orig c:/ruta/de/vectores.npy -ruta_dest c:/ruta/de/modelos -m sklearn.modeloelegido -p parametros del modelo
"""

import numpy as np
import os
import time
import logging
import importlib
# Librerias de posibles modelos a entrenar
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import RidgeClassifier
import sklearn.svm
from sklearn.linear_model import SGDClassifier
from sklearn.hmm import GaussianHMM
from sklearn.naive_bayes import BernoulliNB
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestCentroid
from sklearn import metrics
from sklearn.feature_selection import RFE
from sklearn.linear_model import RandomizedLogisticRegression
from sklearn.cross_validation import StratifiedShuffleSplit, StratifiedKFold
import sys
from itertools import izip
from Utils import storage, features
import glob
import argparse


def entrenador(ruta_orig, ruta_dest, param, model, sample_weight):
    """
    :param ruta_orig: Carpeta con los vectores y archivos de verdad
    :param ruta_dest: Carpeta donde almacenar el modelo
    :param param: Diccionario con la distribucion de parametro
    :param model: Nombre de libreria y modelo formato libreria.modulo.modelo
    :param sample_weight: Pesos previos para ponderar muestras del vector
    :return:
    """

    # carpeta con los archivos npy y txt, con los mismos nombres cada par
    vectorpath = ruta_orig + '/*.npy'  # args.ruta_orig
    targetpath = ruta_orig + '/*.txt'

    targets = []
    vector = []
    nombres_archivo = []
    primero = True

    for targetname, filename in izip(glob.glob(targetpath), glob.glob(vectorpath)):

        targetsaux = []
        try:
            vectoraux = np.load(filename)
        except:
            parser.error('Nombre de ruta inexistente o con formato erroneo. Pruebe a poner solo / en vez de \\')
            print sys.exit()

        print 'Recuperando vector ', filename, targetname
        nombres_archivo.append(os.path.split(filename)[1])
        tamvector = len(vectoraux)
        targetfile = open(targetname, 'r')
        lineas = targetfile.readlines()

        for linea in lineas:
            for i in linea:
                if i.isdigit():
                    targetsaux.append(int(i))
        targetsaux = np.array(targetsaux)
        tamtargets = len(targetsaux)

        if tamtargets != tamvector:
            print 'no coinciden datosanuncios y targets', tamtargets, tamvector
            if tamvector < tamtargets:
                targetsaux = targetsaux[:-(tamtargets - tamvector)]
            else:

                targetsaux = np.append(targetsaux, np.array([targetsaux[-1]] * (tamvector - tamtargets)))

        if primero:
            vector = np.array(vectoraux)
            targets = np.array(targetsaux)

        else:
            vector = np.row_stack([vector, np.array(vectoraux)])
            targets = np.append(targets, np.array(targetsaux), axis=0)
        primero = False

    if len(vector) == 0 or len(targets) == 0:
        print 'error en la carga de archivos'
        print sys.exit()
    elif not len(vector) == len(targets):
        print 'no coinciden el vector de parametros y targets'

    nombre_clasreport = 'entrenamiento' + '_' + time.asctime()[4:-5].replace(' ', '').replace(':', '') + '.log'
    logging.basicConfig(filename='C:\Users\Mario\Desktop\InfoAdex09062015\entrenamiento/' + nombre_clasreport,
                        level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info('------ENTRENANDO CLASIFICADOR %s -----' % time.asctime())
    logger.info('---------ARCHIVOS ENTRENADOS--------')
    logger.info(str(nombres_archivo))
    logger.info('---------NUMERO DE PARAMETROS--------')
    logger.info(str(np.shape(vector)[1]))

    libreria, modelo = model.rsplit('.', 1)

    try:
        clf = getattr(importlib.import_module(libreria), modelo)()
    except:
        print ' error de recuperacion de clasificador'
        sys.exit()

    # set up de parametros
    if param:
        dp = {}
        for parametro in param:
            valor_dp = parametro.split('=')[1]
            if valor_dp.isdigit():
                valor_dp = int(valor_dp)
            elif '.' in valor_dp and not valor_dp == 'SAMME.R':
                valor_dp = float(valor_dp)
            elif valor_dp == 'None':
                valor_dp = None
            elif valor_dp == 'False':
                valor_dp = False
            elif valor_dp == 'True':
                valor_dp = True
            dp[parametro.split('=')[0]] = valor_dp

        clf.set_params(**dp)

    nvector, ntargets = features.undersampling(vector, targets)

    logger.info('_' * 80)
    logger.info("Modelo: ")
    logger.info(clf)
    t0 = time.time()
    if sample_weight:
        sw = np.array(sample_weight)
        print sample_weight
        clf.fit(vector, targets, sample_weight=sw)
    else:
        clf.fit(vector, targets)

    train_time = time.time() - t0
    logger.info("tiempo de entrenamiento: %0.3fs" % train_time)

    # ALMACENAMOS EL MODELO
    clf_descr = str(clf).split('(')[0]

    storage.dump_model(clf, clf_descr + '_' + time.asctime()[4:-11].replace(' ', '') + '.pkl', ruta=ruta_dest)

    return ruta_dest + clf_descr + '_' + time.asctime()[4:-11].replace(' ', '') + '.pkl'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Funcion que entrena un modelo concreto a partir de una ruta de archivos')
    parser.add_argument('--ruta_orig', default='D:/archivos_captor/vectores_ini_cope',
                        help='Ruta de origen de vectores')
    parser.add_argument('--ruta_dest', default='D:/archivos_captor/modelos', help='Ruta de destino del modelo')
    parser.add_argument('-p', '--param', nargs='+',
                        help='Diccionario con la distribucion de parametros como key = value')
    parser.add_argument('-m', '--model', default='sklearn.neighbors.KNeighborsClassifier',
                        help='Nombre de libreria y modelo formato libreria.modulo.modelo')
    parser.add_argument('-s', '--sample_weight', nargs='+', default=[], type=float,
                        help='Pesos previos para ponderar muestras del vector')
    args = parser.parse_args()

    entrenador(args.ruta_orig, args.ruta_orig, args.param, args.model, args.sample_weight)
