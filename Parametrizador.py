# coding=utf-8
# __author__ = 'Mario Romera Fernández'

"""
Proyecto Captor 2015
Ejecutable de extraccion de un vector de caracteristicas por cada audio contenido en una ruta
"""

from AudioFile import AudioFile
import Energy
from features import mfcc
from Config import *
import glob
import os
import sys
import psutil
import numpy as np
import time
import SpectralFlux


def normalizacion(vector):
    """
    :param vector:
    :return: vector estandarizado
    """

    MEAN = np.mean(vector, axis=0)
    STD = np.std(vector, axis=0)
    vectorNorm = []
    ft = vector.copy()

    if np.count_nonzero(STD) < STD.size:
        print 'error en el vector, valores nulos'
        return
    else:
        for nSamples in range(vector.shape[0]):
            ft[nSamples, :] = (ft[nSamples, :] - MEAN) / STD
        vectorNorm.append(ft)
        vectorNorm = np.array(vectorNorm)[0]

        return vectorNorm


def extractor_audio(buffer, fs):
    '''
    :param buffer: string list del audio a vectorizar
    :return: una fila del vector
    '''

    s = AudioFile.open_frombuffer(buffer)
    sf = s.frames(fs)
    num_ventanas = len(sf)
    lenv = np.round(s.sampleRate * VENTANA)
    vector = np.zeros([num_ventanas, NUM_PARAMETROS], dtype=np.float32)

    for indf, frame in enumerate(sf):
        Espectro = frame.spectrum()
        acumulado = 0
        for param in zip(PARAMETROS, TIPO_PARAMETROS):
            if not param[1]:
                vector[indf, acumulado] = getattr(Energy, param[0])(frame, windowSize=lenv, solape=SOLAPE)
            else:
                vector[indf, acumulado] = Espectro.mean()  # getattr(Espectro, param[0])()
            acumulado = acumulado + 1

        if MFCC > 0:
            mfcc_features = mfcc(s, samplerate=s.sampleRate, winlen=VENTANA, numcep=MFCC)
            mfcc_means = np.mean(mfcc_features, 0)
            for i in range(0, MFCC):
                vector[indf, acumulado] = mfcc_means[i]
                acumulado = acumulado + 1

            if DELTAS:
                delta = np.zeros(MFCC)
                dobledelta = np.zeros(MFCC)

                for i in range(0, MFCC):
                    diferencias = np.diff(mfcc_features[:, i])
                    delta[i] = np.sum(diferencias)
                    dobledelta[i] = np.sum(np.diff(diferencias))

                for i in range(0, MFCC):
                    vector[indf, acumulado] = delta[i]
                    acumulado = acumulado + 1

                for i in range(0, MFCC):
                    vector[indf, acumulado] = dobledelta[i]
                    acumulado = acumulado + 1

        if CHROMA > 0:
            array_chroma = Espectro.chroma()

            for i in range(0, CHROMA):
                vector[indf, acumulado] = array_chroma[i]
                acumulado = acumulado + 1

        if FLUX > 0:
            spectral_frames = s.frames(lenv)
            spectra = [f.spectrum_dct() for f in spectral_frames]
            flujo = SpectralFlux.spectralFlux(spectra, rectify=True)

            for i in range(0, FLUX):
                vector[indf, acumulado] = flujo[i]
                acumulado = acumulado + 1

    return vector


def extractor(origen, destino=''):
    """
    Metodo extractor de features (caracteristicas o descriptores) de un array de tipo PCM
    Se realizara mediante segmentacion por segundos del array de muestras de audio.
    Por cada segundo tendremos una fila de un vector 1D de longitud el numero de parametros que extraigamos
    Al final se almacena esta matriz de dimensiones NumSegundosxNumParametros en formato npy en una ruta designada
    Un archivo por cada audio
    O tambien,si no le damos un destino, genera un vector uniendo todos los audios y lo devuelve

    :param s: ruta de los arrays originales para parametrizar
    :type s: string
    :param p: ruta donde se almacenaran los vectores parametrizados
    :type p: string

    Actualmente en config tenemos establecido este set de features:
    Vector de 20 parametros:
    lst_energy - hzcrr - centroid - spread - variance - rolloff - mean - crest - mfcc (8)
    """

    if not os.path.isdir(origen):
        if not os.path.isfile(origen):
            print 'Directorio o nombre de archivos de origen no valido o sin extension (wav/mp3)'
            sys.exit()
        else:
            origen = origen
    else:
        origen = os.path.join(origen, '*.wav')

    if not glob.glob(origen):
        print 'no hay archivos de formato wav en el directorio'
        sys.exit()

    vectortotal = []
    primero = True

    print 'Inicio del parametrizador. Extraccion segundo a segundo y con %i parametros' % NUM_PARAMETROS

    for filename in (glob.glob(origen)):
        print 'Vectorizando archivo: ', filename
        t1 = time.time()
        s = AudioFile.open(filename)
        sf = s.frames(s.sampleRate)
        num_ventanas = len(sf)
        lenv = np.round(s.sampleRate * VENTANA)
        vector = np.zeros([num_ventanas, NUM_PARAMETROS], dtype=np.float32)

        for indf, frame in enumerate(sf):
            print len(frame)
            if len(frame) < s.sampleRate:
                print 'fuera'
                break
            Espectro = frame.spectrum()
            acumulado = 0

            for param in zip(PARAMETROS, TIPO_PARAMETROS):
                if not param[1]:
                    vector[indf, acumulado] = getattr(Energy, param[0])(frame, windowSize=lenv, solape=SOLAPE)
                else:
                    vector[indf, acumulado] = Espectro.mean()  # getattr(Espectro, param[0])()
                acumulado = acumulado + 1

            if MFCC > 0:
                mfcc_features = mfcc(frame, samplerate=s.sampleRate, winlen=VENTANA, numcep=MFCC)
                mfcc_means = np.mean(mfcc_features, 0)
                for i in range(0, MFCC):
                    vector[indf, acumulado] = mfcc_means[i]
                    acumulado = acumulado + 1

                if DELTAS:
                    delta = np.zeros(MFCC)
                    dobledelta = np.zeros(MFCC)

                    for i in range(0, MFCC):
                        diferencias = np.diff(mfcc_features[:, i])
                        delta[i] = np.sum(diferencias)
                        dobledelta[i] = np.sum(np.diff(diferencias))

                    for i in range(0, MFCC):
                        vector[indf, acumulado] = delta[i]
                        acumulado = acumulado + 1

                    for i in range(0, MFCC):
                        vector[indf, acumulado] = dobledelta[i]
                        acumulado = acumulado + 1

            if CHROMA > 0:
                array_chroma = Espectro.chroma()

                for i in range(0, CHROMA):
                    vector[indf, acumulado] = array_chroma[i]
                    acumulado = acumulado + 1

            if FLUX > 0:
                spectral_frames = frame.frames(lenv)
                spectra = [f.spectrum_dct() for f in spectral_frames]
                flujo = SpectralFlux.spectralFlux(spectra, rectify=True)

                for i in range(0, FLUX):
                    vector[indf, acumulado] = flujo[i]
                    acumulado = acumulado + 1

        print 'Tiempo de parametrizacion (minutos): '
        print (time.time() - t1) / 60

        archivo = os.path.split(filename)[1].split('.')[0]
        ruta = os.path.join(destino, archivo)

        if destino:
            np.save(ruta, vector)
        if primero:
            vectortotal = np.array(vector)
        else:
            vectortotal = np.append(vectortotal, np.array(vector), axis=0)
        primero = False

    return vectortotal


def extractor_var(origen, framelen=0.25, destino=''):
    """
    Metodo extractor de features (caracteristicas o descriptores) de un array de tipo PCM
    Se realizara mediante segmentacion por segundos del array de muestras de audio.
    Por cada segundo tendremos una fila de un vector 1D de longitud el numero de parametros que extraigamos
    Al final se almacena esta matriz de dimensiones NumSegundosxNumParametros en formato npy en una ruta designada
    Un archivo por cada audio
    O tambien,si no le damos un destino, genera un vector uniendo todos los audios y lo devuelve

    :param s: ruta de los arrays originales para parametrizar
    :type s: string
    :param p: ruta donde se almacenaran los vectores parametrizados
    :type p: string

    Actualmente en config tenemos establecido este set de features:
    Vector de 20 parametros:
    lst_energy - hzcrr - centroid - spread - variance - rolloff - mean - crest - mfcc (8)
    """

    if not os.path.isdir(origen):
        if not os.path.isfile(origen):
            print 'Directorio o nombre de archivos de origen no valido o sin extension (wav/mp3)'
            sys.exit()
        else:
            origen = origen
    else:
        origen = os.path.join(origen, '*.wav')

    if not glob.glob(origen):
        print 'no hay archivos de formato wav en el directorio'
        sys.exit()

    vectortotal = []
    primero = True

    print 'Inicio del parametrizador. Extraccion segundo a segundo y con %i parametros' % NUM_PARAMETROS

    for filename in (glob.glob(origen)):
        print '\nVectorizando archivo: ', filename
        t1 = time.time()
        s = AudioFile.open(filename)
        sf = s.frames(s.sampleRate * framelen)
        num_ventanas = len(sf)
        lenv = np.round(s.sampleRate * VENTANA)
        vector = np.zeros([num_ventanas, NUM_PARAMETROS], dtype=np.float32)
        for indf, frame in enumerate(sf):
            print len(frame)
            if len(frame) < s.sampleRate:
                break
            Espectro = frame.spectrum()
            acumulado = 0

            for param in zip(PARAMETROS, TIPO_PARAMETROS):
                if not param[1]:
                    vector[indf, acumulado] = getattr(Energy, param[0])(frame, windowSize=lenv, solape=SOLAPE)
                else:
                    vector[indf, acumulado] = Espectro.mean()  # getattr(Espectro, param[0])()
                acumulado = acumulado + 1

            if MFCC > 0:
                mfcc_features = mfcc(frame, samplerate=s.sampleRate, winlen=VENTANA, numcep=MFCC)
                mfcc_means = np.mean(mfcc_features, 0)
                for i in range(0, MFCC):
                    vector[indf, acumulado] = mfcc_means[i]
                    acumulado = acumulado + 1
                if DELTAS:
                    delta = np.zeros(MFCC)
                    dobledelta = np.zeros(MFCC)
                    for i in range(0, MFCC):
                        diferencias = np.diff(mfcc_features[:, i])
                        delta[i] = np.sum(diferencias)
                        dobledelta[i] = np.sum(np.diff(diferencias))
                    for i in range(0, MFCC):
                        vector[indf, acumulado] = delta[i]
                        acumulado = acumulado + 1
                    for i in range(0, MFCC):
                        vector[indf, acumulado] = dobledelta[i]
                        acumulado = acumulado + 1
            if CHROMA > 0:
                array_chroma = Espectro.chroma()
                for i in range(0, CHROMA):
                    vector[indf, acumulado] = array_chroma[i]
                    acumulado = acumulado + 1
            if FLUX > 0:
                spectral_frames = frame.frames(lenv)
                spectra = [f.spectrum_dct() for f in spectral_frames]
                flujo = SpectralFlux.spectralFlux(spectra, rectify=True)
                for i in range(0, FLUX):
                    vector[indf, acumulado] = flujo[i]
                    acumulado = acumulado + 1

        print 'Tiempo de parametrizacion (minutos): '
        print (time.time() - t1) / 60

        archivo = os.path.split(filename)[1].split('.')[0]
        ruta = os.path.join(destino, archivo)

        if destino:
            np.save(ruta, vector)
        if primero:
            vectortotal = np.array(vector)
        else:
            vectortotal = np.append(vectortotal, np.array(vector), axis=0)
        primero = False

    return vectortotal


if __name__ == '__main__':

    path = 'D:\\archivos_captor\zpa'
    destino = 'D:\\archivos_captor\zpa'

    extractor(path, destino=destino)
