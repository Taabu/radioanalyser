# coding=utf-8
# __author__ = 'Mario Romera Fernández'

"""
Proyecto Captor 2015

Ejecutable de prueba de diferentes metodos de Machine Learning para clasificar vectores
en publicidad - no publicidad
"""

import numpy as np
import os
import time
import pylab as pl
import logging
from sklearn.linear_model import RidgeClassifier
from sklearn.svm import LinearSVC, SVC
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier, ExtraTreesClassifier, \
    GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestCentroid
from sklearn.utils.extmath import density
from sklearn import metrics
from sklearn.cross_validation import StratifiedShuffleSplit
import sys
from Utils import storage, features
import glob

# carpeta con los archivos wav y txt, con los mismos nombres cada par
vectorpath = 'D:\\archivos_captor\\vectores_ini_ser_norm\*.npy'  # 'D:\\archivos_captor\\vectores_20\*.npy'
targetpath = 'D:\\archivos_captor\\vectores_ini_ser_norm\*.txt'  # 'D:\\archivos_captor\\vectores_20\*.txt'

# Archivo LOG con la informacion del test

nombre_clasificacionreport = 'clasificacion' + '_' + time.asctime()[4:-5].replace(' ', '').replace(':', '') + '.log'

logging.basicConfig(filename='D:/i+d/Captor/prototipo_2/docs/' + nombre_clasificacionreport, level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info('---------RUTA ARCHIVOS--------')
logger.info(str(vectorpath))

targets = []
vector = []
nombres_archivo = []
primero = True

for targetname, filename in zip(glob.glob(targetpath), glob.glob(vectorpath)):
    print 'Recuperando vector ', filename, targetname

    targetsaux = []

    nombres_archivo.append(os.path.split(filename)[1])

    vectoraux = np.load(filename)
    print vectoraux.shape
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

logger.info('---------ARCHIVOS ENTRENADOS--------')
logger.info(str(nombres_archivo))
logger.info('------RESULTADOS CLASIFICACION %s -----' % time.asctime())

nvector, ntargets = features.undersampling(vector, targets)

# Selector balanceado de indices de pruebas train -test
indices = StratifiedShuffleSplit(ntargets, 3, test_size=0.3)


#######################################################################################################################
######## BUCLE DE CLASIFICADORES A ENTRENAR - TESTEAR CON SUS RESULTADOS #############################################

def benchmark(clf):
    print 'en benchmark'
    logger.info('_' * 80)
    logger.info("Entrenamiento: ")
    logger.info(clf)
    t0 = time.time()

    clf.fit(X_train, y_train)

    train_time = time.time() - t0
    logger.info("tiempo de entrenamiento: %0.3fs" % train_time)

    t0 = time.time()
    pred = clf.predict(X_test)
    test_time = time.time() - t0
    logger.info("tiempo de test:  %0.3fs" % test_time)

    precision = metrics.precision_score(y_test, pred)
    score = metrics.recall_score(y_test, pred)
    funo = metrics.f1_score(y_test, pred)
    logger.info("f1-score:   %0.3f" % score)

    if hasattr(clf, 'coef_'):
        logger.info("dimensionalidad: %d" % clf.coef_.shape[1])
        logger.info("densidad: %f" % density(clf.coef_))

    logger.info("Informe de clasificacion:")
    logger.info(metrics.classification_report(y_test, pred))

    logger.info("Matriz de confusion:")
    logger.info(metrics.confusion_matrix(y_test, pred))

    clf_descr = str(clf).split('(')[0]

    return precision, score, funo, train_time, test_time


results = []
print len(indices)
for train_index, test_index in indices:
    print 'enbucle'
    results_provisional = []

    clf_names = []
    X_train, X_test = vector[train_index], vector[test_index]
    y_train, y_test = targets[train_index], targets[test_index]

    # Clasificadores a usar

    for clf, name in (
            (RidgeClassifier(alpha=1.0,max_iter=None, normalize=False, solver='cholesky', tol=0.0001),
             "Ridge Classifier"),

            (ExtraTreesClassifier(bootstrap=False, compute_importances=None, criterion='gini', max_depth=None,
                                  max_features=None,
                                  max_leaf_nodes=None, min_density=None, min_samples_leaf=1, min_samples_split=3,
                                  n_estimators=100, n_jobs=-1), "Extra Tree"),
            (RandomForestClassifier(criterion='entropy', max_depth=None, max_features=None, max_leaf_nodes=None,
                                    min_density=None, min_samples_leaf=1,
                                    min_samples_split=2, n_estimators=100, n_jobs=-1, ), "Random Forest"),
            (GradientBoostingClassifier(init=None, learning_rate=0.1, loss='deviance',
                                        max_depth=3, max_features=None, max_leaf_nodes=None,
                                        min_samples_leaf=1, min_samples_split=3, n_estimators=100,
                                        random_state=None, subsample=1.0), "Gradient Boosting"),
            (AdaBoostClassifier(algorithm='SAMME.R', base_estimator=None,
                                learning_rate=0.1, n_estimators=100, random_state=None), "AdaBoost"),

            (LinearSVC(class_weight='auto', multi_class='ovr', dual=False, loss='l2', penalty='l1',
                       tol=0.01, C=1000), "LinearSVC"),
            # (SVC(kernel='poly'),"SVC"),
            (KNeighborsClassifier(algorithm='kd_tree', leaf_size=100, metric='minkowski', n_neighbors=10, p=2,
                                  weights='uniform'), "kNN")):
        logger.info('=' * 80)
        logger.info(name)
        results_provisional.append(benchmark(clf))
        clf_names.append(name)

    results.append(results_provisional)

logger.info('\n\n---------RESULTADOS PROMEDIADOS --------')
logger.info('---------########################## --------')

############# GRAFICA DE RESULTADO COMPARATIVO FINAL ##################################################################


results = [[x[i] for x in results] for i in range(len(clf_names))]

results = np.mean(results, 1)
indices = np.arange(len(results))
results = np.transpose(results)

precision, score, funo, training_time, test_time = results

training_time = np.array(training_time) / np.max(training_time)
test_time = np.array(test_time) / np.max(test_time)

pl.figure(figsize=(12, 8))
pl.title("Resultados")
pl.barh(indices, score, .2, label="Recall", color='r')
pl.barh(indices + .3, funo, .2, label="F1", color='y')
pl.barh(indices + .6, precision, .2, label="Precision", color='k')
# pl.barh(indices + .3, training_time, .2, label="training time", color='g')
# pl.barh(indices + .6, test_time, .2, label="test time", color='b')
pl.yticks(())
pl.legend(loc='best')
pl.subplots_adjust(left=.25)
pl.subplots_adjust(top=.95)
pl.subplots_adjust(bottom=.05)

for i, c in enumerate(clf_names):
    pl.text(0.33, i, c, size=14)
    logger.info('Recall y F1 score para el modelo %s ' % c)
    logger.info('Recall -> ' + str(score[i]))
    logger.info('F 1 -> ' + str(funo[i]))

pl.xlim([0.5, 1.0])
pl.show()
