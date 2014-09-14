#!/usr/bin/python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------#
#                                                                       #
# This file is part of the Horus Project                                #
#                                                                       #
# Copyright (C) 2014 Mundo Reader S.L.                                  #
#                                                                       #
# Date: June 2014                                                       #
# Author: Jesús Arroyo Torrens <jesus.arroyo@bq.com>                    #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU General Public License as published by  #
# the Free Software Foundation, either version 3 of the License, or     #
# (at your option) any later version.                                   #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
# GNU General Public License for more details.                          #
#                                                                       #
# You should have received a copy of the GNU General Public License     #
# along with this program. If not, see <http://www.gnu.org/licenses/>.  #
#                                                                       #
#-----------------------------------------------------------------------#

"""
PLY file point cloud loader.

	- Binary, which is easy and quick to read.
	- Ascii, which is harder to read, as can come with windows, mac and unix style newlines.

This module also contains a function to save objects as an PLY file.

http://en.wikipedia.org/wiki/PLY_(file_format)
"""

__author__ = "Jesús Arroyo Torrens <jesus.arroyo@bq.com>"
__license__ = "GNU General Public License v3 http://www.gnu.org/licenses/gpl.html"

import os
import struct
import numpy as np

from horus.util import model

def _loadAscii(m, f, dtype, count):
	fields = dtype.fields

	v = 0
	c = 0

	if 'c' in fields:
		c += 3
	if 'n' in fields:
		c += 3

	i = 0
	while i < count:
		i += 1
		data = f.readline().split(' ')
		if data is not None:
			m._addVertex(data[v],data[v+1],data[v+2],data[c],data[c+1],data[c+2])

def _loadBinary(m, f, dtype, count):
	data = np.fromfile(f, dtype=dtype , count=count)

	fields = dtype.fields
	m.vertexCount = count

	if 'v' in fields:
		m.vertexes = data['v']
	else:
		m.vertexes = np.zeros((count,3))

	if 'n' in fields:
		m.normal = data['n']
	else:
		m.normal = np.zeros((count,3))

	if 'c' in fields:
		m.colors = data['c']
	else:
		m.colors = 255 * np.ones((count,3))

def loadScene(filename):
	obj = model.Model(filename, isPointCloud=True)
	m = obj._addMesh()
	f = open(filename, "rb")

	dtype = []
	count = 0
	format = None
	header = ''
	line = ''

	while line != 'end_header\n':
		line = f.readline()
		header += line
	#-- Discart faces
	header = header.split('element face ')[0].split('\n')

	if header[0] == 'ply':

		for line in header:
			if 'format ' in line:
				format = line.split(' ')[1]
				break

		if format is not None:
			if format == 'ascii':
				fm = ''
			elif format == 'binary_big_endian':
				fm = '>'
			elif format == 'binary_little_endian':
				fm = '<'

		df = {'float' : fm+'f', 'uchar' : fm+'B'}
		dt = {'x' : 'v', 'nx' : 'n', 'red' : 'c', 'alpha' : 'a'}
		ds = {'x' : 3, 'nx' : 3, 'red' : 3, 'alpha' : 1}

		for line in header:
			if 'element vertex ' in line:
				count = int(line.split('element vertex ')[1])
			elif 'property ' in line:
				props = line.split(' ')
				if props[2] in dt.keys():
					dtype = dtype + [(dt[props[2]], df[props[1]], (ds[props[2]],))]

		dtype = np.dtype(dtype)

		if format is not None:
			if format == 'ascii':
				m._prepareVertexCount(count)
				_loadAscii(m, f, dtype, count)
			elif format == 'binary_big_endian' or format == 'binary_little_endian':
				_loadBinary(m, f, dtype, count)

		f.close()
		obj._postProcessAfterLoad()
		return obj

	else:
		print "Error: incorrect file format."
		f.close()
		return None

def saveScene(filename, _object):
	f = open(filename, 'wb')
	saveSceneStream(f, _object)
	f.close()

def saveSceneStream(stream, _object):
	m = _object._mesh

	binary = True

	if m is not None:
		frame  = "ply\n"
		if binary:
			frame += "format binary_little_endian 1.0\n"
		else:
			frame += "format ascii 1.0\n"
		frame += "comment Generated by Horus software\n"
		frame += "element vertex {0}\n".format(m.vertexCount)
		frame += "property float x\n"
		frame += "property float y\n"
		frame += "property float z\n"
		frame += "property uchar red\n"
		frame += "property uchar green\n"
		frame += "property uchar blue\n"
		frame += "element face 0\n"
		frame += "property list uchar int vertex_indices\n"
		frame += "end_header\n"
		if m.vertexCount > 0:
			points = m.vertexes
			colors = m.colors
			if binary:
				for i in range(m.vertexCount):
					frame += struct.pack("<fffBBB", points[i,0], points[i,1], points[i,2] , colors[i,0], colors[i,1], colors[i,2])
			else:
				for i in range(m.vertexCount):
					frame += "{0} {1} {2} {3} {4} {5}\n".format(points[i,0], points[i,1], points[i,2] , colors[i,0], colors[i,1], colors[i,2])
		stream.write(frame)