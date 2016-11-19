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
from keras.layers.convolutional import Convolution2D, AveragePooling2D
from keras.optimizers import SGD
from keras.utils import np_utils

from snntoolbox.io_utils.plotting import plot_history

batch_size = 128
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
model.add(AveragePooling2D(pool_size=(2, 2)))
model.add(Dropout(0.25))

model.add(Convolution2D(64, 3, 3))
model.add(Activation('relu'))
model.add(Convolution2D(64, 3, 3))
model.add(Activation('relu'))
model.add(AveragePooling2D(pool_size=(2, 2)))
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
else:
    print("Using real time data augmentation")

    # This will do preprocessing and realtime data augmentation
    datagen = ImageDataGenerator(
        featurewise_center=False,  # set input mean to 0 over the dataset
        samplewise_center=False,  # set each sample mean to 0
        # divide inputs by std of the dataset
        featurewise_std_normalization=False,
        samplewise_std_normalization=False,  # divide each input by its std
        zca_whitening=False,  # apply ZCA whitening
        # randomly rotate images in the range (degrees, 0 to 180)
        rotation_range=0,
        # randomly shift images horizontally (fraction of total width)
        width_shift_range=0.1,
        # randomly shift images vertically (fraction of total height)
        height_shift_range=0.1,
        horizontal_flip=True,  # randomly flip images
        vertical_flip=False)  # randomly flip images

    # Compute quantities required for featurewise normalization
    # (std, mean, and principal components if ZCA whitening is applied)
    datagen.fit(X_train)

    # Fit the model on the batches generated by datagen.flow()
    history = model.fit_generator(
        datagen.flow(X_train, Y_train, batch_size=batch_size),
        samples_per_epoch=X_train.shape[0], validation_data=(X_test, Y_test),
        nb_epoch=nb_epoch)

plot_history(history)

score = model.evaluate(X_test, Y_test, batch_size=batch_size)
print('Test score:', score[0])
print('Test accuracy:', score[1])

filename = '{:2.2f}'.format(score[1] * 100)+".avg.pool"
open(filename + '.json', 'w').write(model.to_json())
model.save_weights(filename + '.h5', overwrite=True)
