# Import the required modules
from odbAccess import *
from abaqusConstants import *
from odbMaterial import *
from odbSection import *
# Write out csv file 
import csv

# odb file
odbFilename = 'SpringbackJob.odb'
# ABAQUS set names 
topSetName = 'TOP'
botSetName = 'BOT'
stepName = 'Springback_Step'
# Thinning data file name 
thinningFileName = 'ThinningData.csv'


# Create ODB object 
odb = openOdb(path=odbFilename)


# Initialize empty lists to store nodal coordinates and node labels 
# of nodes on the top and bottom edges of the undeformed configuration
topCoords_undef = [] 
botCoords_undef = []    

# Loop over nodes to extract nodal coordinates and node labels of 
# nodes on top edge
for ndMeshObjs in odb.rootAssembly.nodeSets[topSetName].nodes[0] :
    topCoords_undef.append((ndMeshObjs.coordinates[0],ndMeshObjs.coordinates[1],ndMeshObjs.label))
    
# Loop over nodes to extract nodal coordinates and node labels of 
# nodes on bottom edge 
for ndMeshObjs in odb.rootAssembly.nodeSets[botSetName].nodes[0] :
    botCoords_undef.append((ndMeshObjs.coordinates[0],ndMeshObjs.coordinates[1],ndMeshObjs.label))

# Sort the tuples of the list in increasing order of the 1st coordinate 
topCoords_undef.sort(key = lambda triple: triple[0])
botCoords_undef.sort(key = lambda triple: triple[0])    

topX_undef = []
topY_undef = []
botX_undef = []
botY_undef = []

for nodes in topCoords_undef :
    topX_undef = topX_undef + [nodes[0]]
    topY_undef = topY_undef + [nodes[1]]    

for nodes in botCoords_undef :
    botX_undef = botX_undef + [nodes[0]]
    botY_undef = botY_undef + [nodes[1]]   
   
# Initialize empty list to store nodal coordinates and node labels of the model post springback
allCoords_def = []

# Frame number : Specify '-1' for the last frame of the Springback step
frameNum = -1

# Loop over nodes to extract nodal coordinates and node labels
for fdoutObjs in odb.steps[stepName].frames[frameNum].fieldOutputs['COORD'].values :
    if  (str(fdoutObjs.precision) == 'DOUBLE_PRECISION') and  fdoutObjs.nodeLabel is not None :
        allCoords_def.append((fdoutObjs.dataDouble[0],fdoutObjs.dataDouble[1],fdoutObjs.nodeLabel)) 
    elif (str(fdoutObjs.precision) == 'SINGLE_PRECISION') and  fdoutObjs.nodeLabel is not None :    
        allCoords_def.append((fdoutObjs.data[0],fdoutObjs.data[1],fdoutObjs.nodeLabel)) 
    
# Initialize empty lists to store nodal coordinates and node labels 
# of nodes on the top and bottom edges of the deformed configuration   
topCoords_def = [] 
botCoords_def = [] 

# Loop over nodes of top edge to extract corresponding nodal coordinates 
# of the deformed configuration
for nodes in topCoords_undef :
    topCoords_def.append(allCoords_def[nodes[2]-1])

# Loop over nodes of bottom edge to extract corresponding nodal coordinates 
# of the deformed configuration
for nodes in botCoords_undef :
    botCoords_def.append(allCoords_def[nodes[2]-1])
    
 
# Lists to store x and y coordinates of the top and bottom edges separately 
topX_def = []
topY_def = []
botX_def = []
botY_def = []

for nodes in topCoords_def :
    topX_def = topX_def + [nodes[0]]
    topY_def = topY_def + [nodes[1]]

for nodes in botCoords_def :
    botX_def = botX_def + [nodes[0]]
    botY_def = botY_def + [nodes[1]]
    
## Thickness Computation    
def perpDistCompute(botX1,botY1,botX2,botY2,topX1,topY1,topX2,topY2) :
    botC_X = 0.5*(botX1 + botX2)
    botC_Y = 0.5*(botY1 + botY2)
    
    perpDist = botC_Y*(topX2 - topX1) - botC_X*(topY2 - topY1) + topX1*topY2 - topX2*topY1
    perpDist = abs(perpDist)/pow((topX1 - topX2)*(topX1 - topX2)+(topY1 - topY2)*(topY1 - topY2),0.5)
    return perpDist 


# Initialize list to store deformed thickness
perpDist_List = []         
# Top edge except for ends
for i in range(1,len(botX_def)) :
    botX2 = botX_def[i]
    botY2 = botY_def[i]
    botX1 = botX_def[i-1]
    botY1 = botY_def[i-1]
    topX2 = topX_def[i]
    topY2 = topY_def[i]
    topX1 = topX_def[i-1]
    topY1 = topY_def[i-1]
    perpDist_List = perpDist_List + [perpDistCompute(botX1,botY1,botX2,botY2,topX1,topY1,topX2,topY2)]

# Initialize list to store original thickness
origThickness = [] 
for i in range(1,len(botX_def)) :
    origThickness = origThickness + [topY_undef[i-1] - botY_undef[i-1]]

# Initialize list to store thinning percentage 
thinningPercent = []
for i in range(1,len(botX_def)) :
    thinningPercent = thinningPercent + [(perpDist_List[i-1]-origThickness[i-1])/(origThickness[i-1])*100] 

# Initialize list to store distance along deformed bottom edge
defDist_list = []
defprev = 0.0
defDist = 0.0
 
# Write out .csv file which can be opened in MS-Excel
with open(thinningFileName,'wb') as file: # wb is required to prevent error from using 'newline' option
    writer = csv.writer(file)
    writer.writerow(["Distance","Gauge","NodeID","X","Y","Thinning Percent"])
    for i in range(1,len(topX_def)) :
        defDist = defDist + 0.5*(pow((botX_def[i] - botX_def[i-1])*(botX_def[i] - botX_def[i-1]) \
                            + (botY_def[i] - botY_def[i-1])*(botY_def[i] - botY_def[i-1]),0.5))
        defDist = defDist + defprev 
        defprev = 0.5*(pow((botX_def[i] - botX_def[i-1])*(botX_def[i] - botX_def[i-1]) \
                    + (botY_def[i] - botY_def[i-1])*(botY_def[i] - botY_def[i-1]),0.5))
        
        
        writer.writerow([defDist,perpDist_List[i-1],botCoords_undef[i][2],botX_def[i]-botX_def[0],botY_def[i]-botY_def[0],thinningPercent[i-1]])
        defDist_list = defDist_list + [defDist] 

   
## KEY DIMENSIONS 
lip_height = max(topY_def) - botY_def[-1]
countersink_depth = max(botY_def) - min(botY_def)

# Based on partition offset         
for i in range(0,len(botX_undef)) :
    if (botX_undef[i] > 0.8) :
        indx_req = i 
        break 
        
panel_height = botY_def[indx_req] - min(botY_def)


# Print key dimensions 
print('Lip height = ' + str(lip_height) + ' in')
print('Countersink depth = ' + str(countersink_depth) + ' in')
print('Panel height = ' + str(panel_height) + ' in')

# odb file
odbFilename = 'BucklingJob.odb'

# Create ODB object 
odb = openOdb(path=odbFilename)
stepName = 'Buckling'

# Time period based on last converged step
t_period = odb.steps[stepName].timePeriod 

# Maximum pressure
p_max = 130.0

# Compute buckling pressure
p_buckle = p_max * t_period

# Print buckling pressure 
print('Buckling pressure = ' + str(p_buckle) + ' psi')

perfmetrics_file = 'PerfMetricsFile.csv'
with open(perfmetrics_file,'wb') as file: # wb is required to prevent error from using 'newline' option
    writer = csv.writer(file)
    writer.writerow(["Lip Height","Countersink Depth","Panel Height","Buckling Pressure","Max Thinning Percent"])
    writer.writerow([lip_height,countersink_depth,panel_height,p_buckle,min(thinningPercent)])
    