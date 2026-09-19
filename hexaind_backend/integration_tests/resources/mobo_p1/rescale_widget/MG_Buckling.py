# Standard imports 
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *

## MODEL DEFINITION
mdb.Model(modelType=STANDARD_EXPLICIT, name='Buckling_MG')

## PART DEFINITION FROM SPRINGBACK ODB
mdb.models['Buckling_MG'].PartFromOdb(instance='BLANK-1', name='BLANK-1', 
    odb=session.openOdb(
    r'SpringbackJob.odb'))

## SPRINGBACK ODB FOR DEFORMED SHAPE
odb = openOdb(path='SpringbackJob.odb')

# Initialize empty lists to store nodal coordinates and node labels 
# of nodes on the top edge of the undeformed configuration
topCoords_undef = [] 
botCoords_undef = [] 

# Loop over nodes to extract nodal coordinates and node labels of 
# nodes on top edge
for ndMeshObjs in odb.rootAssembly.nodeSets['TOP'].nodes[0] :
    topCoords_undef.append((ndMeshObjs.coordinates[0],ndMeshObjs.coordinates[1],ndMeshObjs.label))
for ndMeshObjs in odb.rootAssembly.nodeSets['BOT'].nodes[0] :
    botCoords_undef.append((ndMeshObjs.coordinates[0],ndMeshObjs.coordinates[1],ndMeshObjs.label))    

# Initialize empty list to store nodal coordinates and node labels of the model post springback
allCoords_def = []

# Frame number : Specify '-1' for the last frame of the Springback step
frameNum = -1

# Loop over nodes to extract nodal coordinates and node labels
# The nodeLabels are already in ascending order
for fdoutObjs in odb.steps['Springback_Step'].frames[frameNum].fieldOutputs['COORD'].values :
    if  (str(fdoutObjs.precision) == 'DOUBLE_PRECISION') and  fdoutObjs.nodeLabel is not None :
        allCoords_def.append((fdoutObjs.dataDouble[0],fdoutObjs.dataDouble[1],fdoutObjs.nodeLabel)) 
    elif (str(fdoutObjs.precision) == 'SINGLE_PRECISION') and  fdoutObjs.nodeLabel is not None :    
        allCoords_def.append((fdoutObjs.data[0],fdoutObjs.data[1],fdoutObjs.nodeLabel)) 

# Following line may be uncommented if you notice that the node labels don't
# appear in ascending order 
# allCoords_def.sort(key = lambda triple: triple[2])

# Initialize empty lists to store nodal y-coordinates of nodes on the 
# top and bottom edges of the deformed configuration   
topCoords_def_y = [] 
topCoords_def_x = [] 
botCoords_def_y = [] 
botCoords_def_x = [] 

# Loop over nodes of top edge to extract corresponding nodal coordinates 
# of the deformed configuration
for nodes in topCoords_undef :
    topCoords_def_y.append(allCoords_def[nodes[2]-1][1])
    topCoords_def_x.append(allCoords_def[nodes[2]-1][0])         

for nodes in botCoords_undef :
    botCoords_def_y.append(allCoords_def[nodes[2]-1][1])
    botCoords_def_x.append(allCoords_def[nodes[2]-1][0])
    
# Index corresponding to the maximum among the y-coordinates 
indx_y_max = botCoords_def_y.index(max(botCoords_def_y)) 

# x-coordinate of the node on the top edge corresponding to the maximum y-coordinate 
pressure_surf_x = botCoords_undef[indx_y_max][0]

# Center of upper clamping tool
indx_y_max = topCoords_def_y.index(max(topCoords_def_y)) 
up_clamp_tool_x = topCoords_def_x[indx_y_max]
delta_x = max(topCoords_def_x) - up_clamp_tool_x
delta_y = topCoords_undef[0][1] -  botCoords_undef[0][1]
up_clamp_tool_y = max(topCoords_def_y)      

# Upper clamping tool - Part
mdb.models['Buckling_MG'].ConstrainedSketch(name='__profile__', sheetSize=
    200.0)
mdb.models['Buckling_MG'].sketches['__profile__'].sketchOptions.setValues(
    viewStyle=AXISYM)
mdb.models['Buckling_MG'].sketches['__profile__'].ConstructionLine(point1=(
    0.0, -100.0), point2=(0.0, 100.0))
mdb.models['Buckling_MG'].sketches['__profile__'].Line(point1=(up_clamp_tool_x - delta_x , up_clamp_tool_y + delta_y), 
    point2=(max(topCoords_def_x), up_clamp_tool_y + delta_y))
mdb.models['Buckling_MG'].Part(dimensionality=AXISYMMETRIC, name=
    'UpperClampingTool', type=ANALYTIC_RIGID_SURFACE)
mdb.models['Buckling_MG'].parts['UpperClampingTool'].AnalyticRigidSurf2DPlanar(
    sketch=mdb.models['Buckling_MG'].sketches['__profile__'])
del mdb.models['Buckling_MG'].sketches['__profile__']    

# Reference point
mdb.models['Buckling_MG'].parts['UpperClampingTool'].ReferencePoint(point=
    mdb.models['Buckling_MG'].parts['UpperClampingTool'].InterestingPoint(
    mdb.models['Buckling_MG'].parts['UpperClampingTool'].edges[0], MIDDLE))    
mdb.models['Buckling_MG'].parts['UpperClampingTool'].Set(name='RefPt', 
    referencePoints=(
    mdb.models['Buckling_MG'].parts['UpperClampingTool'].referencePoints[2], 
    ))
    
# Surface    
mdb.models['Buckling_MG'].parts['UpperClampingTool'].Surface(name='Srfc', 
    side2Edges=
    mdb.models['Buckling_MG'].parts['UpperClampingTool'].edges)
    
# Mass    
mdb.models['Buckling_MG'].parts['UpperClampingTool'].engineeringFeatures.PointMassInertia(
    alpha=0.0, composite=0.0, mass=1.0, name='Mass', region=
    mdb.models['Buckling_MG'].parts['UpperClampingTool'].sets['RefPt'])   


# Lower Clamping tool top - Part

curled_region_surface_y = []
curled_region_surface_x = []
for nodes in topCoords_undef :
    top_def_y = allCoords_def[nodes[2]-1][1]
    top_def_x = allCoords_def[nodes[2]-1][0]    
    if top_def_x >= up_clamp_tool_x :
        curled_region_surface_x.append(top_def_x)
        curled_region_surface_y.append(top_def_y)
        
for nodes in botCoords_undef :
    top_def_y = allCoords_def[nodes[2]-1][1]
    top_def_x = allCoords_def[nodes[2]-1][0]    
    if top_def_x >= up_clamp_tool_x :
        curled_region_surface_x.append(top_def_x)
        curled_region_surface_y.append(top_def_y)
        
indx_y_min = curled_region_surface_y.index(min(curled_region_surface_y))

# Index corresponding to the maximum among the x-coordinates 
lower_clamp_tool_top_x = curled_region_surface_x[indx_y_min]
lower_clamp_tool_top_y = curled_region_surface_y[indx_y_min] - delta_y


mdb.models['Buckling_MG'].ConstrainedSketch(name='__profile__', sheetSize=
    200.0)
mdb.models['Buckling_MG'].sketches['__profile__'].sketchOptions.setValues(
    viewStyle=AXISYM)
mdb.models['Buckling_MG'].sketches['__profile__'].ConstructionLine(point1=(
    0.0, -100.0), point2=(0.0, 100.0))

mdb.models['Buckling_MG'].sketches['__profile__'].Line(point1=(lower_clamp_tool_top_x - delta_x, lower_clamp_tool_top_y), 
    point2=(lower_clamp_tool_top_x + delta_x, lower_clamp_tool_top_y))

mdb.models['Buckling_MG'].Part(dimensionality=AXISYMMETRIC, name=
    'LowerClampingTool_Top', type=ANALYTIC_RIGID_SURFACE)
mdb.models['Buckling_MG'].parts['LowerClampingTool_Top'].AnalyticRigidSurf2DPlanar(
    sketch=mdb.models['Buckling_MG'].sketches['__profile__'])
del mdb.models['Buckling_MG'].sketches['__profile__']


# Reference point 
mdb.models['Buckling_MG'].parts['LowerClampingTool_Top'].ReferencePoint(
    point=
    mdb.models['Buckling_MG'].parts['LowerClampingTool_Top'].InterestingPoint(
    mdb.models['Buckling_MG'].parts['LowerClampingTool_Top'].edges[0], 
    MIDDLE))
mdb.models['Buckling_MG'].parts['LowerClampingTool_Top'].Set(name='RefPt', 
    referencePoints=(
    mdb.models['Buckling_MG'].parts['LowerClampingTool_Top'].referencePoints[2], 
    ))
    
# Surface    
mdb.models['Buckling_MG'].parts['LowerClampingTool_Top'].Surface(name='Srfc', 
    side1Edges=
    mdb.models['Buckling_MG'].parts['LowerClampingTool_Top'].edges)
    
# Mass    
mdb.models['Buckling_MG'].parts['LowerClampingTool_Top'].engineeringFeatures.PointMassInertia(
    alpha=0.0, composite=0.0, mass=1.0, name='Mass', region=
    mdb.models['Buckling_MG'].parts['LowerClampingTool_Top'].sets['RefPt'])
 
# Lower clamping tool - Part
mdb.models['Buckling_MG'].ConstrainedSketch(name='__profile__', sheetSize=
    200.0)
mdb.models['Buckling_MG'].sketches['__profile__'].sketchOptions.setValues(
    viewStyle=AXISYM)
mdb.models['Buckling_MG'].sketches['__profile__'].ConstructionLine(point1=(
    0.0, -100.0), point2=(0.0, 100.0))

# Offset to specify spring end point 
spring_offset = up_clamp_tool_y - lower_clamp_tool_top_y + delta_y
# spring_offset = 2.0*delta_y
mdb.models['Buckling_MG'].sketches['__profile__'].Line(point1=(lower_clamp_tool_top_x - delta_x, lower_clamp_tool_top_y - spring_offset), 
        point2=(lower_clamp_tool_top_x + delta_x, lower_clamp_tool_top_y - spring_offset))

mdb.models['Buckling_MG'].Part(dimensionality=AXISYMMETRIC, name=
    'LowerClampingTool_Bot', type=ANALYTIC_RIGID_SURFACE)
mdb.models['Buckling_MG'].parts['LowerClampingTool_Bot'].AnalyticRigidSurf2DPlanar(
    sketch=mdb.models['Buckling_MG'].sketches['__profile__'])
del mdb.models['Buckling_MG'].sketches['__profile__']

# Reference point 
mdb.models['Buckling_MG'].parts['LowerClampingTool_Bot'].ReferencePoint(
    point=
    mdb.models['Buckling_MG'].parts['LowerClampingTool_Bot'].InterestingPoint(
    mdb.models['Buckling_MG'].parts['LowerClampingTool_Bot'].edges[0], 
    MIDDLE))
mdb.models['Buckling_MG'].parts['LowerClampingTool_Bot'].Set(name='RefPt', 
    referencePoints=(
    mdb.models['Buckling_MG'].parts['LowerClampingTool_Bot'].referencePoints[2], 
    ))

# Surface
mdb.models['Buckling_MG'].parts['LowerClampingTool_Bot'].Surface(name='Srfc', 
    side2Edges=
    mdb.models['Buckling_MG'].parts['LowerClampingTool_Bot'].edges)
    
# Mass
mdb.models['Buckling_MG'].parts['LowerClampingTool_Bot'].engineeringFeatures.PointMassInertia(
    alpha=0.0, composite=0.0, mass=1.0, name='Mass', region=
    mdb.models['Buckling_MG'].parts['LowerClampingTool_Bot'].sets['RefPt'])

# Instances 
mdb.models['Buckling_MG'].rootAssembly.DatumCsysByThreePoints(coordSysType=
    CYLINDRICAL, origin=(0.0, 0.0, 0.0), point1=(1.0, 0.0, 0.0), point2=(0.0, 
    0.0, -1.0))
mdb.models['Buckling_MG'].rootAssembly.Instance(dependent=ON, name=
    'BLANK-1', part=mdb.models['Buckling_MG'].parts['BLANK-1'])
mdb.models['Buckling_MG'].rootAssembly.Instance(dependent=ON, name=
    'LowerClampingTool_Bot-1', part=
    mdb.models['Buckling_MG'].parts['LowerClampingTool_Bot'])
mdb.models['Buckling_MG'].rootAssembly.Instance(dependent=ON, name=
    'LowerClampingTool_Top-1', part=
    mdb.models['Buckling_MG'].parts['LowerClampingTool_Top'])
mdb.models['Buckling_MG'].rootAssembly.Instance(dependent=ON, name=
    'UpperClampingTool-1', part=
    mdb.models['Buckling_MG'].parts['UpperClampingTool'])  


# Node sets 
mdb.models['Buckling_MG'].rootAssembly.Set(name='SYM', nodes=
    mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].sets['SYMMSEG'].nodes)    
# Surfaces
mdb.models['Buckling_MG'].rootAssembly.Surface(face2Elements=
    mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].sets['_UPPERSURF_S2'].elements, 
    face4Elements=
    mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].sets['_UPPERSURF_S4'].elements, name='UpperSurf')

mdb.models['Buckling_MG'].rootAssembly.Surface(face2Elements=
    mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].sets['_LOWERSURF_S2'].elements, 
    face4Elements=
    mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].sets['_LOWERSURF_S4'].elements, name='LowerSurf')

# Create the pressure surface 
pressure_surf_s2 = []
for elems in mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].sets['_LOWERSURF_S2'].elements :
    xcd_1 = mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].nodes[elems.connectivity[0]].coordinates[0]
    xcd_2 = mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].nodes[elems.connectivity[1]].coordinates[0]
    xcd_3 = mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].nodes[elems.connectivity[2]].coordinates[0]
    xcd_4 = mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].nodes[elems.connectivity[3]].coordinates[0]
    x_mean = 0.25*(xcd_1 +  xcd_2 + xcd_3 + xcd_4)
    if x_mean < pressure_surf_x :
        pressure_surf_s2 = pressure_surf_s2 + [elems]

pressure_surf_s4 = []    
for elems in mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].sets['_LOWERSURF_S4'].elements :
    xcd_1 = mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].nodes[elems.connectivity[0]].coordinates[0]
    xcd_2 = mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].nodes[elems.connectivity[1]].coordinates[0]
    xcd_3 = mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].nodes[elems.connectivity[2]].coordinates[0]
    xcd_4 = mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'].nodes[elems.connectivity[3]].coordinates[0]
    x_mean = 0.25*(xcd_1 +  xcd_2 + xcd_3 + xcd_4)
    if x_mean < pressure_surf_x :
        pressure_surf_s4 = pressure_surf_s4 + [elems]

   
mdb.models['Buckling_MG'].rootAssembly.Surface(face2Elements=MeshElementArray(pressure_surf_s2),
        face4Elements=MeshElementArray(pressure_surf_s4), 
        name='PressureSurf')    
   
# Spring connecting lower clamping tools 
#mdb.models['Buckling_MG'].rootAssembly.engineeringFeatures.TwoPointSpringDashpot(
#    axis=NODAL_LINE, dashpotBehavior=OFF, dashpotCoefficient=0.0, name='Spring'
#    , regionPairs=((
#    mdb.models['Buckling_MG'].rootAssembly.instances['LowerClampingTool_Bot-1'].sets['RefPt'], 
#    mdb.models['Buckling_MG'].rootAssembly.instances['LowerClampingTool_Top-1'].sets['RefPt']), 
#    ), springBehavior=ON, springStiffness=0.001)

# Initial state 
mdb.models['Buckling_MG'].InitialState(createStepName='Initial', 
    endIncrement=STEP_END, endStep=LAST_STEP, fileName='SpringbackJob', 
    instances=(mdb.models['Buckling_MG'].rootAssembly.instances['BLANK-1'], )
    , name='ResidualState', updateReferenceConfiguration=OFF)  
mdb.models['Buckling_MG'].XsymmBC(createStepName='Initial', localCsys=None, 
    name='BlankSym', region=
    mdb.models['Buckling_MG'].rootAssembly.sets['SYM'])  

# Buckle setup
mdb.models['Buckling_MG'].StaticStep(description='Setting up buckling test', initialInc=0.01, maxInc=0.1, maxNumInc=
    10000, minInc=1e-05,name='Buckle_Setup', previous='Initial')
mdb.models['Buckling_MG'].fieldOutputRequests['F-Output-1'].setValues(
    variables=('S', 'PE', 'PEEQ', 'PEMAG', 'LE', 'U', 'RF', 'CF', 'CSTRESS', 
    'CDISP', 'COORD'))  
    
# Interactions    
mdb.models['Buckling_MG'].ContactProperty('ClampingTool_Blank')
mdb.models['Buckling_MG'].interactionProperties['ClampingTool_Blank'].NormalBehavior(
    allowSeparation=ON, constraintEnforcementMethod=DEFAULT, 
    pressureOverclosure=HARD)
mdb.models['Buckling_MG'].interactionProperties['ClampingTool_Blank'].TangentialBehavior(
    formulation=FRICTIONLESS)
mdb.models['Buckling_MG'].SurfaceToSurfaceContactStd(adjustMethod=NONE, 
    clearanceRegion=None, createStepName='Buckle_Setup', datumAxis=None, 
    enforcement=NODE_TO_SURFACE, initialClearance=OMIT, interactionProperty=
    'ClampingTool_Blank', main=
    mdb.models['Buckling_MG'].rootAssembly.instances['LowerClampingTool_Top-1'].surfaces['Srfc']
    , name='LowerClampingTool_Blank', secondary=
    mdb.models['Buckling_MG'].rootAssembly.surfaces['LowerSurf'], sliding=
    FINITE, smooth=0.2, surfaceSmoothing=NONE, thickness=OFF)
mdb.models['Buckling_MG'].SurfaceToSurfaceContactStd(adjustMethod=NONE, 
    clearanceRegion=None, createStepName='Buckle_Setup', datumAxis=None, 
    enforcement=NODE_TO_SURFACE, initialClearance=OMIT, interactionProperty=
    'ClampingTool_Blank', main=
    mdb.models['Buckling_MG'].rootAssembly.instances['UpperClampingTool-1'].surfaces['Srfc']
    , name='UpperClampingTool_Blank', secondary=
    mdb.models['Buckling_MG'].rootAssembly.surfaces['UpperSurf'], sliding=
    FINITE, smooth=0.2, surfaceSmoothing=NONE, thickness=OFF)    
# Newly created boundary conditions 
mdb.models['Buckling_MG'].EncastreBC(createStepName='Buckle_Setup', 
    localCsys=None, name='UpperClampingTool_Fix', region=
    mdb.models['Buckling_MG'].rootAssembly.instances['UpperClampingTool-1'].sets['RefPt'])
mdb.models['Buckling_MG'].DisplacementBC(amplitude=UNSET, createStepName=
    'Buckle_Setup', distributionType=UNIFORM, fieldName='', fixed=OFF, 
    localCsys=None, name='LowerClampingTool_ConstrainedMotion', region=
    mdb.models['Buckling_MG'].rootAssembly.instances['LowerClampingTool_Top-1'].sets['RefPt']
    , u1=0.0, u2=UNSET, ur3=0.0)
    
#lower_clamp_tool_bot_travel = up_clamp_tool_y - lower_clamp_tool_top_y
lower_clamp_tool_bot_travel = 3.0*delta_y

mdb.models['Buckling_MG'].DisplacementBC(amplitude=UNSET, createStepName=
    'Buckle_Setup', distributionType=UNIFORM, fieldName='', fixed=OFF, 
    localCsys=None, name='SpringMotion', region=
    mdb.models['Buckling_MG'].rootAssembly.instances['LowerClampingTool_Bot-1'].sets['RefPt']
    , u1=0.0, u2=lower_clamp_tool_bot_travel, ur3=0.0)
# Buckling test     
mdb.models['Buckling_MG'].StaticStep(description='Buckling test', initialInc=1e-06, maxInc=0.1, maxNumInc=
    1000000, minInc=1e-09, name=
    'Buckling', previous='Buckle_Setup')
# Modify boundary conditions
mdb.models['Buckling_MG'].boundaryConditions['LowerClampingTool_ConstrainedMotion'].deactivate(
    'Buckling')
mdb.models['Buckling_MG'].DisplacementBC(amplitude=UNSET, createStepName=
    'Buckling', distributionType=UNIFORM, fieldName='', fixed=ON, localCsys=
    None, name='LowerClampingTool_Fixed', region=
    mdb.models['Buckling_MG'].rootAssembly.instances['LowerClampingTool_Top-1'].sets['RefPt']
    , u1=SET, u2=SET, ur3=SET)
# Loading    
pressure_max = 130.0
mdb.models['Buckling_MG'].Pressure(amplitude=UNSET, createStepName='Buckling'
    , distributionType=UNIFORM, field='', magnitude=pressure_max, name='PressureLoad', 
    region=mdb.models['Buckling_MG'].rootAssembly.surfaces['PressureSurf'])

# Start - Modify input file for linear spring connecting lower clamping tools
##
model = mdb.models['Buckling_MG']
modelkwb = model.keywordBlock
# Synch edits to modelkwb with those made in the model. We don't need
# access to *nodes and *elements as they would appear in the inp file,
# so set the storeNodesAndElements arg to False.
modelkwb.synchVersions(storeNodesAndElements=False)

#
# Search the modelkwb for the desired insertion point. In this example, 
# we are looking for a line that indicates we are beginning the Part-Level 
# block for the specific Part we are interested in. If it is found, we 
# break the loop, storing the line number, and then write our keywords
# using the insert method (which actually inserts just below the specified
# line number, fyi).
line_num_endassembly=0
n=len(modelkwb.sieBlocks)
print("length of sieBlocks is %d" % n)
for n, line in enumerate(modelkwb.sieBlocks):
    if line.find("*End Assembly") != -1:
       line_num_endassembly = n
## Create linear spring 
kwds_IPS = """*Spring, elset=Spring-spring

0.001
*Element, type=SpringA, elset=Spring-spring
1, LowerClampingTool_Top-1.1, LowerClampingTool_Bot-1.1"""

modelkwb.insert(position=line_num_endassembly-1, text=kwds_IPS)
##
# End - Modify input file for nonlinear spring  

# Create Job
buckling_job = 'BucklingJob'
mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
    explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
    memory=90, memoryUnits=PERCENTAGE, model='Buckling_MG', modelPrint=OFF, 
    multiprocessingMode=DEFAULT, name=buckling_job, nodalOutputPrecision=FULL
    , numCpus=1, numGPUs=0, queue=None, resultsFormat=ODB, scratch='', type=
    ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)   

# Write input file     
mdb.jobs[buckling_job].writeInput(consistencyChecking=OFF)   