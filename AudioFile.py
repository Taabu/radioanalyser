# coding=utf-8
# __author__ = 'Mario Romera Fernández'

"""
Clase AudioFile
Carga archivos de audio (wav ,mp3, raw) en una subclase ndarray (numpy array)

"""
from subprocess import Popen, PIPE
import numpy
from numpy import *
import scipy.io.wavfile
import Frame
import pyaudio
import Config


class AudioFile(Frame.Frame):
    def __new__(subtype, shape, dtype=float, buffer=None, offset=0, strides=None, order=None):
        # Crea la instancia ndarray de nuestro tipo, con sus tipicos argumentos de entrada
        # LLama al constructor ndarray, pero devuelve un objeto de nuestro propio tipo
        # Tambien lanza una llamada a InfoArray.__array_finalize__

        obj = numpy.ndarray.__new__(subtype, shape, dtype, buffer, offset, strides,
                                    order)

        obj.sampleRate = 0
        obj.channels = 1
        obj.format = pyaudio.paFloat32

        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        # ``self`` is a new object resulting from
        # ndarray.__new__(InfoArray, ...), therefore it only has
        # attributes that the ndarray.__new__ constructor gave it -
        # i.e. those of a standard ndarray.
        #
        # We could have got to the ndarray.__new__ call in 3 ways:
        # From an explicit constructor - e.g. InfoArray():
        #    obj is None
        #    (we're in the middle of the InfoArray.__new__
        #    constructor, and self.info will be set when we return to
        #    InfoArray.__new__)
        if obj is None:
            return
        # From view casting - e.g arr.view(InfoArray):
        #    obj is arr
        #    (type(obj) can be InfoArray)
        # From new-from-template - e.g infoarr[:3]
        #    type(obj) is InfoArray
        #
        # Note that it is here, rather than in the __new__ method,
        # that we set the default value for 'info', because this
        # method sees all creation of default objects - with the
        # InfoArray.__new__ constructor, but also with
        # arr.view(InfoArray).

        self.sampleRate = getattr(obj, 'sampleRate', None)
        self.channels = getattr(obj, 'channels', None)
        self.format = getattr(obj, 'format', None)

        # We do not need to return anything

    @staticmethod
    def open_frombuffer(buffer, sampleRate=44100):

        # decimar
        # utils.resample(samples,3,4)
        # sampleRate=sampleRate*(3.0/4.0)

        audioFile = buffer.view(AudioFile)
        audioFile.sampleRate = sampleRate
        audioFile.channels = 1
        audioFile.format = pyaudio.paFloat32

        return audioFile

    @staticmethod
    def open(filename, sampleRate=44100):
        """
        Abre un archivo y devuelve una instancia tipo audiofile

        """
        filename = filename.lower()

        if filename.endswith('mp3') or filename.endswith('m4a'):

            ffmpeg = Popen([
                "C:\Users\plr\Downloads\\ffmpeg-20150217-git-2bae7b3-win64-static\\bin\\ffmpeg",
                "-i", filename,
                "-vn", "-acodec", "pcm_s16le",  # Little Endian 16 bit PCM
                "-ac", "1", "-ar", str(sampleRate),  # -ac = audio channels (1)
                "-f", "s16le", "-"],  # -f wav for WAV file
                stdin=PIPE, stdout=PIPE, stderr=open(os.devnull, "w"))

            rawData = ffmpeg.stdout

            mp3Array = numpy.fromstring(rawData.read(), numpy.int16)
            mp3Array = mp3Array.astype('float32') / 32767.0
            audioFile = mp3Array.view(AudioFile)

            audioFile.sampleRate = sampleRate
            audioFile.channels = 1
            audioFile.format = pyaudio.paFloat32

            return audioFile

        elif filename.endswith('wav'):
            sampleRate, samples = scipy.io.wavfile.read(filename)

            # Convert to float
            samples = samples.astype('float32') / 32767.0

            # Get left channel
            if len(samples.shape) > 1:
                samples = samples[:, 0]

            # decimar
            # utils.resample(samples,3,4)
            # sampleRate=sampleRate*(3.0/4.0)

            audioFile = samples.view(AudioFile)
            audioFile.sampleRate = sampleRate
            audioFile.channels = 1
            audioFile.format = pyaudio.paFloat32

        elif filename.endswith('raw'):

            samples = numpy.memmap(filename, dtype='h', mode='r')

            sampleRate = Config.FRECUENCIA_MUESTREO

            # Convert to float
            samples = samples.astype('float32') / 32767.0

            # decimar
            # utils.resample(samples,3,4)
            # sampleRate=sampleRate*(3.0/4.0)

            audioFile = samples.view(AudioFile)
            audioFile.sampleRate = sampleRate
            audioFile.channels = 1
            audioFile.format = pyaudio.paFloat32

        return audioFile
