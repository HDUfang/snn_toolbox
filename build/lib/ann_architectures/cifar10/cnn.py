# coding=utf-8

"""
Train a (fairly simple) deep CNN on the CIFAR10 small images dataset.

GPU run command:
THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python cifar10_cnn.py

Gets to about 0.5 test loss or 83% accuracy after 65 epochs.

"""

from __future__ import absolute_import
from __future__ import print_function

from keras.datasets import cifar10
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.optimizers import SGD
from keras.utils import np_utils

from snntoolbox.io_utils.plotting import plot_history

batch_size = 32
nb_classes = 10
nb_epoch = 150

data_augmentation = True

# Input image dimensions
img_rows, img_cols = 32, 32
img_channels = 3

# Data set
(X_train, y_train), (X_test, y_test) = cifar10.load_data()
X_train = X_train.astype("float32")
X_test = X_test.astype("float32")
X_train /= 255
X_test /= 255
Y_train = np_utils.to_categorical(y_train, nb_classes)
Y_test = np_utils.to_categorical(y_test, nb_classes)
print('X_train shape:', X_train.shape)
print(X_train.shape[0], 'train samples')
print(X_test.shape[0], 'test samples')

model = Sequential()

model.add(Convolution2D(32, 3, 3, border_mode='same',
                        input_shape=(img_channels, img_rows, img_cols)))
model.add(Activation('relu'))
model.add(Convolution2D(32, 3, 3, border_mode='same'))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Convolution2D(32, 3, 3))
model.add(Activation('relu'))
model.add(Convolution2D(32, 3, 3))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(512))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(nb_classes))
model.add(Activation('softmax'))

sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd,
              metrics=['accuracy'])

if not data_augmentation:
    print("Not using data augmentation or normalization")
#    early_stopping = EarlyStopping(monitor='val_loss', patience=3)
    history = model.fit(X_train, Y_train, batch_size=batch_size,
                        validation_data=(X_test, Y_test), nb_epoch=nb_epoch)
    score = model.evaluate(X_test, Y_test)
else:
    print("Using real time data augmentation")

    gcn = True
    zca = True

    # This will do preprocessing and realtime data augmentation
    traingen = ImageDataGenerator(featurewise_center=gcn,
                                  featurewise_std_normalization=gcn,
                                  zca_whitening=zca,
                                  rotation_range=10,
                                  width_shift_range=0.1,
                                  height_shift_range=0.1,
                                  horizontal_flip=True)

    # Compute quantities required for featurewise normalization
    # (std, mean, and principal components if ZCA whitening is applied)
    traingen.fit(X_train)

    trainflow = traingen.flow(X_train, Y_train, batch_size=batch_size)

    testgen = ImageDataGenerator(featurewise_center=gcn,
                                 featurewise_std_normalization=gcn,
                                 zca_whitening=zca)

    testgen.fit(X_test)

    testflow = testgen.flow(X_test, Y_test, batch_size=batch_size)

    # Fit the model on the batches generated by datagen.flow()
    history = model.fit_generator(trainflow, nb_epoch=nb_epoch,
                                  samples_per_epoch=len(X_train),
                                  validation_data=testflow,
                                  nb_val_samples=len(X_test))

    score = model.evaluate_generator(testflow, val_samples=len(X_test))

plot_history(history)

print('Test score:', score[0])
print('Test accuracy:', score[1])

model.save('{:2.2f}.h5'.format(score[1]*100))
