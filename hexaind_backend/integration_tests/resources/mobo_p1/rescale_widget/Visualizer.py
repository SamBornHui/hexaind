# -*- coding: mbcs -*-
#
# Abaqus/Viewer Release 2023 replay file
# Internal Version: 2022_09_28-14.11.55 183150
# Run by lakshmanana on Fri Jul 14 10:54:38 2023
#
from abaqus import *
from abaqusConstants import *
session.Viewport(name='Viewport: 1', origin=(0.0, 0.0), width=259.415649414062, 
    height=127.628707885742)
session.viewports['Viewport: 1'].makeCurrent()
session.viewports['Viewport: 1'].maximize()
from viewerModules import *
from driverUtils import executeOnCaeStartup
executeOnCaeStartup()
o2 = session.openOdb(name='FormingJob.odb')
#: Model: C:/MIP_Tasks/Phase2_Ask1/output/FormingJob.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     11
#: Number of Meshes:             11
#: Number of Element Sets:       17
#: Number of Node Sets:          28
#: Number of Steps:              1
session.viewports['Viewport: 1'].setValues(displayedObject=o2)
session.viewports['Viewport: 1'].makeCurrent()
session.viewports['Viewport: 1'].view.setValues(cameraPosition=(0.528189, 
    0.465707, 20.8215), cameraUpVector=(0, 1, 0))
session.viewports['Viewport: 1'].viewportAnnotationOptions.setValues(triad=OFF, 
    legend=OFF, title=OFF, state=OFF, annotations=OFF, compass=OFF)
session.graphicsOptions.setValues(backgroundStyle=SOLID, 
    backgroundColor='#000000')
session.viewports['Viewport: 1'].odbDisplay.commonOptions.setValues(
    visibleEdges=FEATURE)
#session.viewports['Viewport: 1'].view.setValues(nearPlane=17.2453, 
#    farPlane=24.3977, width=0.878125, height=0.358978, viewOffsetX=0.154707, 
#    viewOffsetY=-0.532365)
#session.viewports['Viewport: 1'].view.setValues(nearPlane=17.2538, 
#    farPlane=24.3892, width=0.776293, height=0.317349, viewOffsetX=0.263701, 
#    viewOffsetY=-0.552546)
session.viewports['Viewport: 1'].view.setValues(nearPlane=17.2538, 
    farPlane=24.3892, width=0.776293, height=0.317349, viewOffsetX=0.252396, 
    viewOffsetY=-0.536043)
#session.viewports['Viewport: 1'].view.setValues(viewOffsetX=0.252396, 
#    viewOffsetY=-0.536043)
session.viewports['Viewport: 1'].animationController.setValues(
    animationType=TIME_HISTORY)
session.viewports['Viewport: 1'].animationController.play(duration=UNLIMITED)
session.imageAnimationOptions.setValues(vpDecorations=ON, vpBackground=ON, 
    compass=OFF, timeScale=1, frameRate=18)
session.writeImageAnimation(
    fileName='FormingAnimation_Script', format=AVI, 
    canvasObjects=(session.viewports['Viewport: 1'], ))
session.viewports['Viewport: 1'].animationController.stop()


session.Viewport(name='Viewport: 1', origin=(0.0, 0.0), width=259.415649414062, 
    height=127.628707885742)
session.viewports['Viewport: 1'].makeCurrent()
session.viewports['Viewport: 1'].maximize()
from viewerModules import *
from driverUtils import executeOnCaeStartup
executeOnCaeStartup()
o2 = session.openOdb(name='SpringbackJob.odb')
#: Model: C:/MIP_Tasks/Phase2_Ask1/output/SpringbackJob.odb
#: Number of Assemblies:         1
#: Number of Assembly instances: 0
#: Number of Part instances:     1
#: Number of Meshes:             1
#: Number of Element Sets:       5
#: Number of Node Sets:          8
#: Number of Steps:              1
session.viewports['Viewport: 1'].setValues(displayedObject=o2)
session.viewports['Viewport: 1'].makeCurrent()
session.viewports['Viewport: 1'].viewportAnnotationOptions.setValues(triad=OFF, 
    legend=OFF, title=OFF, state=OFF, annotations=OFF, compass=OFF)
session.graphicsOptions.setValues(backgroundStyle=SOLID, 
    backgroundColor='#000000')
session.viewports['Viewport: 1'].odbDisplay.commonOptions.setValues(
    visibleEdges=FEATURE)
session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(
    DEFORMED, ))
session.viewports['Viewport: 1'].view.fitView()
session.viewports['Viewport: 1'].view.setValues(nearPlane=2.66507, 
    farPlane=4.00948, width=0.985891, height=0.403033, viewOffsetX=0.0127686, 
    viewOffsetY=0.00864643)
session.printOptions.setValues(vpDecorations=OFF, vpBackground=OFF)
session.printToFile(fileName='ShellGeometry', 
    format=PNG, canvasObjects=(session.viewports['Viewport: 1'], ))
session.viewports['Viewport: 1'].view.setValues(nearPlane=2.69405, 
    farPlane=3.9805, width=0.638046, height=0.260834, viewOffsetX=0.224399, 
    viewOffsetY=0.0029814)
session.printOptions.setValues(vpDecorations=OFF, vpBackground=OFF)
session.printToFile(fileName='ShellGeometry_Closeup', 
    format=PNG, canvasObjects=(session.viewports['Viewport: 1'], ))


