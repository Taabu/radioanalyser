# coding=utf-8
# __author__ = 'Mario Romera Fernández'

import pyaudio
soundObj = pyaudio.PyAudio()

# Learn what your OS+Hardware can do
defaultCapability = soundObj.get_default_host_api_info()
print defaultCapability
print "default_input:{}".format(soundObj.get_default_input_device_info())
print "default_ouput:{}".format(soundObj.get_default_output_device_info())

count = soundObj.get_device_count()
devices = []
for i in range(count):
    devices.append(soundObj.get_device_info_by_index(i))

for i, dev in enumerate(devices):
    print "\n%d - %s" % (i, dev['name'])
    print dev

# See if you can make it do what you want
for i in range(count):
    try:
        isSupported = soundObj.is_format_supported(input_format=pyaudio.paInt16, input_channels=2, rate=44100,
                                                   input_device=i)
        print isSupported, i
    except:
        pass