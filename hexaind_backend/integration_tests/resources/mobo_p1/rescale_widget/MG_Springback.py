## STANDARD IMPORTS 
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
modelName = 'Springback_MG'
mdb.Model(modelType=STANDARD_EXPLICIT, name=modelName)


## READ PART FROM FORMING ODB
mdb.models[modelName].PartFromOdb(instance='BLANK-1', name='BLANK-1', 
    odb=session.openOdb('FormingJob.odb'))

## CREATE INSTANCE
mdb.models[modelName].rootAssembly.DatumCsysByThreePoints(coordSysType=
    CYLINDRICAL, origin=(0.0, 0.0, 0.0), point1=(1.0, 0.0, 0.0), point2=(0.0, 
    0.0, -1.0))
mdb.models[modelName].rootAssembly.Instance(dependent=ON, name=
    'BLANK-1', part=mdb.models[modelName].parts['BLANK-1'])

## CREATION OF NODE SETS 
# Edge to apply symmetry boundary condition 
mdb.models[modelName].rootAssembly.Set(name='SYM', nodes=mdb.models[modelName].
                        rootAssembly.instances['BLANK-1'].sets['SYMMSEG'].nodes)
# Top edge 
mdb.models[modelName].rootAssembly.Set(name='TOP', nodes=mdb.models[modelName].
                        rootAssembly.instances['BLANK-1'].sets['TOPEDGE'].nodes)
# Bottom edge 
mdb.models[modelName].rootAssembly.Set(name='BOT', nodes=mdb.models[modelName].
                        rootAssembly.instances['BLANK-1'].sets['BOTEDGE'].nodes)

## STEP DEFINITION
# Initial Step
print(mdb.models[modelName].rootAssembly.instances)
mdb.models[modelName].InitialState(createStepName='Initial', 
    endIncrement=STEP_END, endStep=LAST_STEP, fileName='FormingJob', instances=
    (mdb.models[modelName].rootAssembly.instances['BLANK-1'], ), name=
    'ResidualState', updateReferenceConfiguration=OFF)    
    
# Symmetry boundary condition on symmetric edge 
mdb.models[modelName].XsymmBC(createStepName='Initial', localCsys=None, 
    name='SymmEdge', region=
    mdb.models[modelName].rootAssembly.sets['SYM'])
    
# Springback Step
initial_increment = 1.0e-02
maximum_increment = 1.00
minimum_increment = 1.0e-05
mdb.models[modelName].StaticStep(description='Performing springback',  
    initialInc=initial_increment, maxInc=maximum_increment, 
    minInc=minimum_increment,name='Springback_Step', previous='Initial')
mdb.models[modelName].steps['Springback_Step'].Restart(frequency=5, 
    numberIntervals=0, overlay=ON, timeMarks=OFF)
    
# Variables to output    
mdb.models[modelName].fieldOutputRequests['F-Output-1'].setValues(
    variables=('S', 'PE', 'PEEQ', 'PEMAG', 'LE', 'U', 'RF', 'CF', 'CSTRESS', 
    'CDISP', 'COORD'))
    
## JOB DEFINITION   
springback_job = 'SpringbackJob'  
mdb.Job(atTime=None, contactPrint=OFF, description='', echoPrint=OFF, 
    explicitPrecision=SINGLE, getMemoryFromAnalysis=True, historyPrint=OFF, 
    memory=90, memoryUnits=PERCENTAGE, model=modelName, modelPrint=OFF, 
    multiprocessingMode=DEFAULT, name=springback_job, nodalOutputPrecision=
    FULL, numCpus=1, numGPUs=0, queue=None, resultsFormat=ODB, scratch='', 
    type=ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)    
    
    
# Write input
    
mdb.jobs[springback_job].writeInput(consistencyChecking=OFF)

