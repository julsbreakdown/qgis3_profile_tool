# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# 
# Profile
# Copyright (C) 2012  Patrice Verchere
#-----------------------------------------------------------
# 
# licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this progsram; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
# 
#---------------------------------------------------------------------
import qgis
from qgis.core import *
from qgis.gui import *

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
try:
    from qgis.PyQt.QtWidgets import *
except:
    pass



class SelectLineTool:
    
    def getPointTableFromSelectedLine(self, iface, tool, newPoints, layerindex, previousLayer, pointstoDraw ):
        pointstoDraw = []
        #self.previousLayer = previousLayer1
        layer = iface.activeLayer()
        if layer == None or layer.type() != QgsMapLayer.VectorLayer:
            QMessageBox.warning( iface.mainWindow(), "Closest Feature Finder", "No vector layers selected" )
            return [pointstoDraw, layerindex, previousLayer]
        if not layer.hasGeometryType():
            QMessageBox.warning( iface.mainWindow(), "Closest Feature Finder", "The selected layer has either no or unknown geometry" )
            return [pointstoDraw, layerindex, previousLayer]
        # get the point coordinates in the layer's CRS
        point = tool.toLayerCoordinates(layer, QgsPoint(newPoints[0][0],newPoints[0][1]))

        
        if layerindex == None or layer != previousLayer:
            # there's no previously created index or it's not the same layer,
            # then create the index
            layerindex = QgsSpatialIndex()
            #rajout
            f = QgsFeature()
            #
            iter = layer.getFeatures()
            while iter.nextFeature(f):
                layerindex.insertFeature(f)
            # get the feature which has the closest bounding box using the spatial index
        nearest = layerindex.nearestNeighbor( point, 1 )
        featureId = nearest[0] if len(nearest) > 0 else None
        closestFeature = QgsFeature()
        
        try:    #qgis2
            if featureId == None or layer.getFeatures(QgsFeatureRequest(featureId)).next() == False:
                closestFeature = None
        except:    #qgis3
            #if featureId == None or layer.getFeatures(QgsFeatureRequest(featureId)).nextFeature() == False:
            f = QgsFeature()
            if featureId == None or layer.getFeatures(QgsFeatureRequest(featureId)).nextFeature(f) == False:
                closestFeature = None
        
        
        try:    #qgis2
            if layer.geometryType() != QGis.Line and closestFeature != None:
                QMessageBox.warning( iface.mainWindow(), "Closest Feature Finder", "No vector layers selected" )
        except: #qgis3
            if layer.geometryType() != qgis.core.QgsWkbTypes.LineGeometry  and closestFeature != None:
                QMessageBox.warning( iface.mainWindow(), "Closest Feature Finder", "No vector layers selected" )

        booltemp = False
        try:    #qgis2
            if layer.geometryType() != QGis.Point:
                booltemp = True
        except: #qgis
            if layer.geometryType() != qgis.core.QgsWkbTypes.PointGeometry :
                booltemp = True
        
        if booltemp and closestFeature != None:
            # find the furthest bounding box borders
            try:    #qgis2
                closestFeature = layer.getFeatures(QgsFeatureRequest(featureId)).next()
                rect = closestFeature.geometry().boundingBox()
            except: #qgis3 
                f = QgsFeature()
                closestFeature = layer.getFeatures(QgsFeatureRequest(featureId)).nextFeature(f)
                rect = f.geometry().boundingBox()
            
            
            dist_pX_rXmax = abs( point.x() - rect.xMaximum() )
            dist_pX_rXmin = abs( point.x() - rect.xMinimum() )
            if dist_pX_rXmax > dist_pX_rXmin:
                width = dist_pX_rXmax
            else:
                width = dist_pX_rXmin

            dist_pY_rYmax = abs( point.y() - rect.yMaximum() )
            dist_pY_rYmin = abs( point.y() - rect.yMinimum() )
            if dist_pY_rYmax > dist_pY_rYmin:
                height = dist_pY_rYmax
            else:
                height = dist_pY_rYmin

            # create the search rectangle
            rect = QgsRectangle()
            rect.setXMinimum( point.x() - width )
            rect.setXMaximum( point.x() + width )
            rect.setYMinimum( point.y() - height )
            rect.setYMaximum( point.y() + height )
            
            # retrieve all geometries into the search rectangle
            
            iter2 = layer.getFeatures(QgsFeatureRequest(rect))
            # find the nearest feature
            minDist = -1
            featureId = None
            point = QgsGeometry.fromPoint(point)
            f = QgsFeature()    
            while iter2.nextFeature(f):
                geom = f.geometry()
                distance = geom.distance(point)
                if minDist < 0 or distance < minDist:
                    minDist = distance
                    featureId = f.id()
            # get the closest feature
            try:
                closestFeature = layer.getFeatures(QgsFeatureRequest(featureId)).next()
                if featureId == None or layer.getFeatures(QgsFeatureRequest(featureId)).next(f) == False:
                    closestFeature = None
            except:
                f = QgsFeature()
                #closestFeature = layer.getFeatures(QgsFeatureRequest(featureId)).next()
                closestFeature = layer.getFeatures(QgsFeatureRequest(featureId)).nextFeature(f)
                closestFeature = f
                if featureId == None or layer.getFeatures(QgsFeatureRequest(featureId)).nextFeature(f) == False:
                    closestFeature = None
                    
        previousLayer = layer
        iface.mainWindow().statusBar().showMessage("selectline")
        layer.removeSelection()
        
        #closest
        #closestFeature = layer.getFeatures(QgsFeatureRequest(featureId)).next()
        layer.select( closestFeature.id() )
        k = 0
        while not closestFeature.geometry().vertexAt(k) == QgsPoint(0,0):
            point2 = tool.toMapCoordinates(layer, closestFeature.geometry().vertexAt(k) )
            pointstoDraw += [[point2.x(),point2.y()]]
            k += 1
            # replicate last point (bug #6680)
            if k > 0 :
                pointstoDraw += [[point2.x(),point2.y()]]
        return [pointstoDraw, layerindex, previousLayer]
