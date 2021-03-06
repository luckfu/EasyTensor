from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import sys

import tensorflow as tf

import utils

from est_base import EstBase


class ConvNN(EstBase):
    def __init__(self, input_dim, output_dim, hidden_patches, hidden_dims, \
                 activations, learning_rate, dropout = False, \
                 costfunc = utils.cross_entropy, optimizer='GD'):

        # ((28, 28), 10, [(5, 5), (5, 5), None], [32, 64, 1024], ['relu', 'relu', 'relu'], 0.5)
        '''

        multilayer perceptron class for simple models
        if dropout == True: feed must include drop out probability named 'keep_prob', else feed includes 'input_data', 'target_data'
        hidden_dims and activations are lists of layer dimensions (int) and strings 
        note train_step'''
        # TODO: add different cost functions

        super(ConvNN, self).__init__(input_dim, output_dim, \
                                                   costfunc, learning_rate, optimizer)

        self.input_x_dim, self.input_y_dim = self.input_dim
        self.input_dim = self.input_dim[0]*self.input_dim[1]
        self.hidden_patches = hidden_patches

        self.hidden_dims = hidden_dims
        self.activations = activations
        self.dropout = dropout

        #define placeholders for data
        with tf.name_scope('input'):
            self.input_data = tf.placeholder(tf.float32, [None, self.input_dim], name='input_data')
            self.target_data = tf.placeholder(tf.float32, [None, self.output_dim], name='target_data')

        #define neural network
        self.num_layers = len(hidden_dims)

        self.hidden = []
        self.cnn_count = 0
        self.input_data_adj = tf.reshape( self.input_data, shape=[-1,self.input_x_dim, self.input_y_dim, 1])

        for i in range(self.num_layers):
            if i == 0:
                self.hidden.append(utils.convolution_layer(self.input_data_adj, 1, self.hidden_dims[i], self.hidden_patches[i],\
                                'hidden_{}'.format(i+1), self.activations[i]))
                self.cnn_count += 1
            # hidden_next = layer(self.hidden_previous, hidden_dims[i-1], hidden_dims[i], 'hidden_#number', activations[i])
            else:
                if hidden_patches[i] == None:
                    self.hidden.append(utils.flatten(self.hidden[i-1], self.hidden_dims[i-1], self.hidden_dims[i], self.cnn_count, self.input_x_dim, self.input_y_dim,\
	                                'hidden_{}'.format(i+1), self.activations[i]))
                    self.cnn_count = 0              	
                else:
                    self.hidden.append(utils.convolution_layer(self.hidden[i-1], self.hidden_dims[i-1], self.hidden_dims[i], self.hidden_patches[i],\
                                'hidden_{}'.format(i+1), self.activations[i]))
                    self.cnn_count += 1


        if dropout:
            self.keep_prob = tf.placeholder(tf.float32)
            tf.summary.scalar('dropout_keep_probability', self.keep_prob)
            dropped = tf.nn.dropout(self.hidden[-1], self.keep_prob)

            self.output = utils.perceptron(dropped, self.hidden_dims[-1], self.output_dim, 'output_layer')

        else:
            self.output = utils.perceptron(self.hidden[-1], self.hidden_dims[-1], self.output_dim, 'output_layer')


        #def cost with function, real y and output y 
        with tf.name_scope('cost'):
            self.diff = self.costfunc(self.target_data, self.output)
            with tf.name_scope('total'):
                self.cost= tf.reduce_mean(self.diff)
                tf.summary.scalar('cost', self.cost)

        with tf.name_scope('train'):
            if optimizer=='ADAM':
                self.train_step = tf.train.AdamOptimizer(self.learning_rate).minimize(self.cost)
            elif optimizer=='GD':
                self.train_step = tf.train.GradientDescentOptimizer(self.learning_rate).minimize(self.cost)
            else:# default choice of optimizer to be GD
                self.train_step = tf.train.GradientDescentOptimizer(self.learning_rate).minimize(self.cost)



        with tf.name_scope('accuracy'):
            with tf.name_scope('correct_prediction'):
                correct_prediction = tf.equal(tf.argmax(self.output, 1), tf.argmax(self.target_data, 1))
            with tf.name_scope('accuracy'):
                self.accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
        tf.summary.scalar('accuracy', self.accuracy)
        self.merged = tf.summary.merge_all()

        #define training operation

