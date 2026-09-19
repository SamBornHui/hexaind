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
import math
import csv


## Import csv file with spacers and pressures
all_dat = []
with open('param_values.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        all_dat = all_dat + [row]
     
num_data = all_dat[1]
#new block
cols = all_dat[0]
param_dict = {}
for i, col in enumerate(cols):
    param_dict[col] = num_data[i]

dcp_spacer_thickness = float(param_dict['dcp_spacer'])        
pp_spacer_thickness = float(param_dict['pp_spacer'])        
ips_force = float(param_dict['ips_pressure'])*2.445         
up_force = float(param_dict['up_pressure'])*3.801
friction_coeff = float(param_dict['friction_coeff'])
upper_radius = float(param_dict['upper_radius']) 
lower_radius = float(param_dict['lower_radius'])        
t_value = float(param_dict['t_value'])        
lr_opening = float(param_dict['lr_opening'])        
catcher_depth = float(param_dict['catcher_depth'])         
ips_radius = float(param_dict['ips_radius'])        
dcr_radius = float(param_dict['dcr_radius'])        
dcp_radius_1 = float(param_dict['dcp_radius_1'])        
dcp_radius_2 = float(param_dict['dcp_radius_2']) 

# dcp_spacer_thickness = float(num_data[0])        
# pp_spacer_thickness = float(num_data[1])        
# ips_force = float(num_data[2])*2.445        
# up_force = float(num_data[3])*3.801
# friction_coeff = float(num_data[4])
# upper_radius = float(num_data[5])        
# lower_radius = float(num_data[6])        
# t_value = float(num_data[7])        
# lr_opening = float(num_data[8])        
# catcher_depth = float(num_data[9])         
# ips_radius = float(num_data[10])        
# dcr_radius = float(num_data[11])        
# dcp_radius_1 = float(num_data[12])        
# dcp_radius_2 = float(num_data[13])        
        


# The following line is useful when one would like to write coordinates associated
# with edges of a part in place of the ids used by getSequenceFromMask
#session.journalOptions.setValues(replayGeometry=COORDINATE,recoverGeometry=COORDINATE)

# Model definition
mdlName = 'CDL200_MG'
mdb.Model(modelType=STANDARD_EXPLICIT, name=mdlName)

## IPS PART DEFINITION
# Sketching tool
mdb.models[mdlName].ConstrainedSketch(name='__profile__', sheetSize=
    200.0)
mdb.models[mdlName].sketches['__profile__'].sketchOptions.setValues(
    viewStyle=AXISYM)
mdb.models[mdlName].sketches['__profile__'].ConstructionLine(point1=(
    0.0, -100.0), point2=(0.0, 100.0))

# Geometric sequence for IPS to construct boundary segments
IPS_geoSeq = 'AAAAALCACCALCALLLLL'

# Number of segments constituting the IPS
IPS_segSize = len(IPS_geoSeq)

# The IPS is created a closed piecewise-smooth curve with anti-clockwise 
# orientation of the edges 
## Geometry inputs 
xp2 = 0.965197939225732
yp2 = 0.155741865281044
xp1 = 0.974131683917449
yp1 = 0.193426894701229
r0 = 0.05
r1 = ips_radius # Modify this 
x0 = 0.951881880342853
theta_p = atan2(yp1 - yp2,xp1 - xp2)
theta_1 = pi/2 - theta_p 
x1 = xp2 - r1*cos(theta_1)
y1 = yp2 + r1*sin(theta_1)
theta_ang = atan2(sqrt((r0 + r1)*(r0 + r1) - (x1 - x0)*(x1 - x0)),x1 - x0)*180.0/pi 
y0 = y1 - (r0 + r1)*sin(theta_ang*pi/180.0)

# Point set definition - x coordinates
IPS_PointSet_x = [(0.873499999285286,0.870799999285282,0.871563042764762),
                  (0.875149999284815,0.871563042764762,0.875149999286009),
                  (0.875149999280154,0.875149999286009,0.893007142142608),
                  (0.875649999280313,0.893007142142608,0.898372077205295),
                  (0.868449999279676,0.898372077205295,0.900449999280625),
                  (0.900449999280625,0.900449999279431),
                  (0.910449999279422,0.900449999279431,0.900874976597947),
                  (0.89129995391653,0.900874976597947,0.901296242939964),
                  (0.971270266104227,0.901296242939964,0.903410915939389),
                  (x0,0.903410915939389,x0 + r0*cos(theta_ang*pi/180)),
                  (x1,x1 - r1*cos(theta_ang*pi/180),0.965197939225732),
                  (0.965197939225732,0.974131683917449),
                  (1.05153543068513,0.974131683917449,1.01105949162002),
                  (1.00599999923691,1.01105949162002,1.0159999992369),
                  (1.0159999992369,1.0159999992369),
                  (1.0159999992369,0.546050049514974),
                  (0.546050049514974,0.546050049514974),
                  (0.546050049514974,0.870799999285282),
                  (0.870799999285282,0.870799999285282)]
# Point set definition - y coordinates
IPS_PointSet_y = [(0.0427780743454527+(y0 - 0.0761411666047067),0.0427780743448274+(y0 - 0.0761411666047067),0.0408970641280995+(y0 - 0.0761411666047067)),
                  (0.0443804163830954+(y0 - 0.0761411666047067),0.0408970641280995+(y0 - 0.0761411666047067),0.039380416382194+(y0 - 0.0761411666047067)),
                  (0.0643804163831057+(y0 - 0.0761411666047067),0.039380416382194+(y0 - 0.0761411666047067),0.0468840610815704+(y0 - 0.0761411666047067)),
                  (0.0638905184346825+(y0 - 0.0761411666047067),0.0468840610815704+(y0 - 0.0761411666047067),0.0552767402382131+(y0 - 0.0761411666047067)),
                  (0.0666199872457973+(y0 - 0.0761411666047067),0.0552767402382131+(y0 - 0.0761411666047067),0.0666199872532296+(y0 - 0.0761411666047067)),
                  (0.0666199872532296+(y0 - 0.0761411666047067),0.0676437033983603+(y0 - 0.0761411666047067)),
                  (0.0676437034006803+(y0 - 0.0761411666047067),0.0676437033983603+(y0 - 0.0761411666047067),0.0705279607832878+(y0 - 0.0761411666047067)),
                  (0.0734122181658954+(y0 - 0.0761411666047067),0.0705279607832878+(y0 - 0.0761411666047067),0.0731398108252073+(y0 - 0.0761411666047067)),
                  (0.0712329594403975+(y0 - 0.0761411666047067),0.0731398108252073+(y0 - 0.0761411666047067),0.0884116845154601+(y0 - 0.0761411666047067)),
                  (y0,0.0884116845154601 + (y0 - 0.0761411666047067),y0 + r0*sin(theta_ang*pi/180)),
                  (y1,y1 - r1*sin(theta_ang*pi/180),0.155741865281044),
                  (0.155741865281044,0.193426894701229),
                  (0.173211554329811,0.193426894701229,0.242216614700766),
                  (0.250842247247146,0.242216614700766,0.250842247249469),
                  (0.250842247249469,1.40728041641583),
                  (1.40728041641583,1.40728041641583),
                  (1.40728041641583,1.30028041637331),
                  (1.30028041637331,1.30028041637331),
                  (1.30028041637331,0.0427780743448274+(y0 - 0.0761411666047067))]


# Run loop over number of curved segments to construct each segment
# Currently only line segments and circular arcs
for i in range(0,IPS_segSize) :
    if IPS_geoSeq[i] == 'L' :
        # Sketch line segment
        mdb.models[mdlName].sketches['__profile__'].Line(point1=(IPS_PointSet_x[i][0],IPS_PointSet_y[i][0]),
        point2=(IPS_PointSet_x[i][1],IPS_PointSet_y[i][1]))       
    elif IPS_geoSeq[i] == 'A' :
        # Sketch arc of circle with anti-clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(IPS_PointSet_x[i][0],IPS_PointSet_y[i][0]),
        direction=COUNTERCLOCKWISE,
        point1=(IPS_PointSet_x[i][1],IPS_PointSet_y[i][1]),
        point2=(IPS_PointSet_x[i][2],IPS_PointSet_y[i][2]))
    elif IPS_geoSeq[i] == 'C' :
        # Sketch arc of circle with clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(IPS_PointSet_x[i][0],IPS_PointSet_y[i][0]),
        direction=CLOCKWISE,
        point1=(IPS_PointSet_x[i][1],IPS_PointSet_y[i][1]),
        point2=(IPS_PointSet_x[i][2],IPS_PointSet_y[i][2]))
        
# Set part type after sketch completion        
mdb.models[mdlName].Part(dimensionality=AXISYMMETRIC, name='IPS', 
    type=ANALYTIC_RIGID_SURFACE)
mdb.models[mdlName].parts['IPS'].AnalyticRigidSurf2DPlanar(sketch=
    mdb.models[mdlName].sketches['__profile__'])
# Exit part definition    
del mdb.models[mdlName].sketches['__profile__']

## To identify the IPS reference point
# Initialize list containing y-coordinates of points near each edge
ips_edgelist_ycoords = [] 
# Loop over edges to extract and store the y-coordinates
for ipsEdges in mdb.models[mdlName].parts['IPS'].edges :
    ips_edgelist_ycoords = ips_edgelist_ycoords + [ipsEdges.pointOn[0][1]]
# Identify an index of the DCP edge list with the maximum y-coordinate
ips_ycoord_maxindx = ips_edgelist_ycoords.index(max(ips_edgelist_ycoords))

# Set reference point as midpoint of the corresponding edge 
mdb.models[mdlName].parts['IPS'].ReferencePoint(point=
    mdb.models[mdlName].parts['IPS'].InterestingPoint(
    mdb.models[mdlName].parts['IPS'].edges[ips_ycoord_maxindx], MIDDLE))
mdb.models[mdlName].parts['IPS'].Set(name='RefPt', referencePoints=(
    mdb.models[mdlName].parts['IPS'].referencePoints[2], ))    

# Extract coordinates corresponding to the point identified. This will be needed later to set
# datum point for the other end point of the spring
ips_edge_endnodes = mdb.models[mdlName].parts['IPS'].edges[ips_ycoord_maxindx].getVertices()
ips_edge_end1 = mdb.models[mdlName].parts['IPS'].vertices[ips_edge_endnodes[0]].pointOn[0]
ips_edge_end2 = mdb.models[mdlName].parts['IPS'].vertices[ips_edge_endnodes[1]].pointOn[0]
ipsRefPoint_coords =  (0.5*(ips_edge_end1[0] + ips_edge_end2[0]),0.5*(ips_edge_end1[1] + ips_edge_end2[1]), \
                        0.5*(ips_edge_end1[2] + ips_edge_end2[2]) )

   
# Alternative definition of surface
mdb.models[mdlName].parts['IPS'].Surface(name='Srfc', side1Edges=
    mdb.models[mdlName].parts['IPS'].edges)
    
# IPS Mass
mdb.models[mdlName].parts['IPS'].engineeringFeatures.PointMassInertia(
    alpha=0.0, composite=0.0, mass=0.00122, name='Mass', region=
    mdb.models[mdlName].parts['IPS'].sets['RefPt'])



## SPACER PART DEFINITION
# Sketching tool
mdb.models[mdlName].ConstrainedSketch(name='__profile__', sheetSize=
    200.0)
mdb.models[mdlName].sketches['__profile__'].sketchOptions.setValues(
    viewStyle=AXISYM)
mdb.models[mdlName].sketches['__profile__'].ConstructionLine(point1=(
    0.0, -100.0), point2=(0.0, 100.0))    

# Geometric sequence for DCP to construct boundary segments
# L : Line segment 
# A : Anticlockwise arc of a circle 
# C : Clockwise arc of a circle
Spacer_geoSeq = 'LLLL'

# Number of segments constituting the DCP
Spacer_segSize = len(Spacer_geoSeq)


# The Spacer is created a closed piecewise-smooth curve with anti-clockwise 
# orientation of the edges 
# List of x-coordinates 
Spacer_PointSet_x = [(0.394999999980996,0.81249999903315),
                     (0.81249999903315,0.81249999903315),
                     (0.81249999903315,0.394999999980996),
                     (0.394999999980996,0.394999999980996)]
# List of y-coordinates 
Spacer_PointSet_y = [(1.12828041636628,1.12828041636628),
                     (1.12828041636628,1.30028041637331),
                     (1.30028041637331,1.30028041637331),
                     (1.30028041637331,1.12828041636628)]

# Run loop over number of curved segments to construct each segment
# Currently only line segments and circular arcs are used as the basic geometries 
# for the segments to construct curves 
for i in range(0,Spacer_segSize) :
    if Spacer_geoSeq[i] == 'L' :
        # Sketch line segment
        mdb.models[mdlName].sketches['__profile__'].Line(point1=(Spacer_PointSet_x[i][0],Spacer_PointSet_y[i][0]),
        point2=(Spacer_PointSet_x[i][1],Spacer_PointSet_y[i][1]))       
    elif Spacer_geoSeq[i] == 'A' :
        # Sketch arc of a circle with anti-clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(Spacer_PointSet_x[i][0],Spacer_PointSet_y[i][0]),
        direction=COUNTERCLOCKWISE,
        point1=(Spacer_PointSet_x[i][1],Spacer_PointSet_y[i][1]),
        point2=(Spacer_PointSet_x[i][2],Spacer_PointSet_y[i][2]))
    elif Spacer_geoSeq[i] == 'C' :
        # Sketch arc of a circle with clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(Spacer_PointSet_x[i][0],Spacer_PointSet_y[i][0]),
        direction=CLOCKWISE,
        point1=(Spacer_PointSet_x[i][1],Spacer_PointSet_y[i][1]),
        point2=(Spacer_PointSet_x[i][2],Spacer_PointSet_y[i][2]))

# Set part type after sketch completion        
mdb.models[mdlName].Part(dimensionality=AXISYMMETRIC, 
    name='Spacer', type=DISCRETE_RIGID_SURFACE)
mdb.models[mdlName].parts['Spacer'].BaseWire(sketch=
    mdb.models[mdlName].sketches['__profile__'])
# Exit part definition    
del mdb.models[mdlName].sketches['__profile__'] 


## To identify the Spacer reference point
# Initialize list containing y-coordinates of points near each edge
Spacer_edgelist_ycoords = [] 
# Loop over edges to extract and store the y-coordinates
for SpacerEdges in mdb.models[mdlName].parts['Spacer'].edges :
    Spacer_edgelist_ycoords = Spacer_edgelist_ycoords + [SpacerEdges.pointOn[0][1]]

# Identify an index of the DCP edge list with the minimum y-coordinate
Spacer_ycoord_minindx = Spacer_edgelist_ycoords.index(min(Spacer_edgelist_ycoords))

# Set reference point as midpoint of the corresponding edge 
mdb.models[mdlName].parts['Spacer'].ReferencePoint(point=
    mdb.models[mdlName].parts['Spacer'].InterestingPoint(
    mdb.models[mdlName].parts['Spacer'].edges[Spacer_ycoord_minindx], MIDDLE))
mdb.models[mdlName].parts['Spacer'].Set(name='RefPt', referencePoints=(
    mdb.models[mdlName].parts['Spacer'].referencePoints[2], ))


# Extract coordinates corresponding to the point identified. This will be needed later to define 
# the other end point of the spring as a datum point
Spacer_edge_endnodes = mdb.models[mdlName].parts['Spacer'].edges[Spacer_ycoord_minindx].getVertices()
Spacer_edge_end1 = mdb.models[mdlName].parts['Spacer'].vertices[Spacer_edge_endnodes[0]].pointOn[0]
Spacer_edge_end2 = mdb.models[mdlName].parts['Spacer'].vertices[Spacer_edge_endnodes[1]].pointOn[0]
SpacerRefPoint_coords =  (0.5*(Spacer_edge_end1[0] + Spacer_edge_end2[0]),0.5*(Spacer_edge_end1[1] + Spacer_edge_end2[1]), \
                        0.5*(Spacer_edge_end1[2] + Spacer_edge_end2[2]) )



mdb.models[mdlName].parts['Spacer'].seedEdgeByNumber(constraint=FINER,
    edges=mdb.models[mdlName].parts['Spacer'].edges, number=1)
    
mdb.models[mdlName].parts['Spacer'].generateMesh()

# Alternative definition of surface
mdb.models[mdlName].parts['Spacer'].Surface(name='Srfc', side2Edges=
    mdb.models[mdlName].parts['Spacer'].edges)



## DCP PART DEFINITION
# Sketching tool setup
mdb.models[mdlName].ConstrainedSketch(name='__profile__', sheetSize=
    200.0)
mdb.models[mdlName].sketches['__profile__'].sketchOptions.setValues(
    viewStyle=AXISYM)
mdb.models[mdlName].sketches['__profile__'].ConstructionLine(point1=(
    0.0, -100.0), point2=(0.0, 100.0))    

# Geometric sequence for DCP to construct boundary segments
# L : Line segment 
# A : Anticlockwise arc of a circle 
# C : Clockwise arc of a circle
DCP_geoSeq = 'LAALL'

# Number of segments constituting the DCP
DCP_segSize = len(DCP_geoSeq)

# The DCP is created an open piecewise-smooth curve with anti-clockwise 
# orientation of the edges 

r0 = dcp_radius_1
r1 = dcp_radius_2
theta_ang = 75.4633050847973
theta_rad = theta_ang*pi/180.0 
y0 = 0.128280416373329 + 0.172 - dcp_spacer_thickness + r0
x1 = 0.86274999998102 - r1
y1 = y0 + (r1 - r0)*sin(theta_rad)
x0 = x1 + (r1 - r0)*cos(theta_rad)

# Point set definition - x coordinates
DCP_PointSet_x = [(0.0,x0),
                  (x0,x0,x0 + r0*cos(theta_rad)),
                  (x1,x1 + r1*cos(theta_rad),0.86274999998102),
                  (0.86274999998102,0.86274999998102),
                  (0.86274999998102,0.0)]
# Point set definition - y coordinates
DCP_PointSet_y = [(0.128280416373329 + 0.172 - dcp_spacer_thickness,0.128280416373308+ 0.172 - dcp_spacer_thickness),
                  (y0,0.128280416373308+ 0.172 - dcp_spacer_thickness,y0 - r0*sin(theta_rad)),
                  (y1,y1 - r1*sin(theta_rad),y1),
                  (y1,1.12828041636628+ 0.172 - dcp_spacer_thickness),
                  (1.12828041636628+ 0.172 - dcp_spacer_thickness,1.12828041636628+ 0.172 - dcp_spacer_thickness)]      

                  
# Run loop over number of curved segments to construct each segment
# Currently only line segments and circular arcs are used as the basic geometries 
# for the segments to construct curves 
for i in range(0,DCP_segSize) :
    if DCP_geoSeq[i] == 'L' :
        # Sketch line segment
        mdb.models[mdlName].sketches['__profile__'].Line(point1=(DCP_PointSet_x[i][0],DCP_PointSet_y[i][0]),
        point2=(DCP_PointSet_x[i][1],DCP_PointSet_y[i][1]))       
    elif DCP_geoSeq[i] == 'A' :
        # Sketch arc of a circle with anti-clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(DCP_PointSet_x[i][0],DCP_PointSet_y[i][0]),
        direction=COUNTERCLOCKWISE,
        point1=(DCP_PointSet_x[i][1],DCP_PointSet_y[i][1]),
        point2=(DCP_PointSet_x[i][2],DCP_PointSet_y[i][2]))
    elif DCP_geoSeq[i] == 'C' :
        # Sketch arc of a circle with clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(DCP_PointSet_x[i][0],DCP_PointSet_y[i][0]),
        direction=CLOCKWISE,
        point1=(DCP_PointSet_x[i][1],DCP_PointSet_y[i][1]),
        point2=(DCP_PointSet_x[i][2],DCP_PointSet_y[i][2]))

# Set part type after sketch completion        
mdb.models[mdlName].Part(dimensionality=AXISYMMETRIC, name='DCP', 
    type=ANALYTIC_RIGID_SURFACE)
mdb.models[mdlName].parts['DCP'].AnalyticRigidSurf2DPlanar(sketch=
    mdb.models[mdlName].sketches['__profile__'])
# Exit part definition    
del mdb.models[mdlName].sketches['__profile__']    


## To identify the DCP reference point
# Initialize list containing x and y-coordinates of points near each edge
dcp_edgelist_ycoords = [] 
dcp_edgelist_xcoords = [] 
# Loop over edges to extract and store the y-coordinates
for dcpEdges in mdb.models[mdlName].parts['DCP'].edges :
    dcp_edgelist_ycoords = dcp_edgelist_ycoords + [dcpEdges.pointOn[0][1]]
    
    
# Identify an index of the DCP edge list with the maximum y-coordinate
dcp_ycoord_maxindx = dcp_edgelist_ycoords.index(max(dcp_edgelist_ycoords))


# Set reference point as midpoint of the corresponding edge 
mdb.models[mdlName].parts['DCP'].ReferencePoint(point=
    mdb.models[mdlName].parts['DCP'].InterestingPoint(
    mdb.models[mdlName].parts['DCP'].edges[dcp_ycoord_maxindx], MIDDLE))
mdb.models[mdlName].parts['DCP'].Set(name='RefPt', referencePoints=(
    mdb.models[mdlName].parts['DCP'].referencePoints[2], ))


# Extract coordinates corresponding to the point identified. This will be needed later to define 
# the other end point of the spring as a datum point
dcp_edge_endnodes = mdb.models[mdlName].parts['DCP'].edges[dcp_ycoord_maxindx].getVertices()
dcp_edge_end1 = mdb.models[mdlName].parts['DCP'].vertices[dcp_edge_endnodes[0]].pointOn[0]
dcp_edge_end2 = mdb.models[mdlName].parts['DCP'].vertices[dcp_edge_endnodes[1]].pointOn[0]
dcpRefPoint_coords =  (0.5*(dcp_edge_end1[0] + dcp_edge_end2[0]),0.5*(dcp_edge_end1[1] + dcp_edge_end2[1]), \
                        0.5*(dcp_edge_end1[2] + dcp_edge_end2[2]) )

## Identify xmax on DCP base
# List of x and y coordinates of all edge vertices(double counting vertices) 
dcp_vertex_y = []
dcp_vertex_x = []
for alledges in mdb.models[mdlName].parts['DCP'].edges :
    pnt_coords = alledges.pointOn[0]
    end_nodes = alledges.getVertices()
    end1_coords = mdb.models[mdlName].parts['DCP'].vertices[end_nodes[0]].pointOn[0]
    end2_coords = mdb.models[mdlName].parts['DCP'].vertices[end_nodes[1]].pointOn[0]
    dcp_vertex_y = dcp_vertex_y + [end1_coords[1]] + [end2_coords[1]]
    dcp_vertex_x = dcp_vertex_x + [end1_coords[0]] + [end2_coords[0]]
    
# Identify an index with minimum y-coordinate
dcp_vertex_y_minindx = dcp_vertex_y.index(min(dcp_vertex_y))
# Minimum y-coordinate 
dcp_vertex_y_min = min(dcp_vertex_y)
# Set a possible x value as the x-coordinate of the index identified earlier
dcp_base_xmax = dcp_vertex_x[dcp_vertex_y_minindx]

# Loop over vertices to check for minimum y-coordinate and maximum x-coordinate 
cntr = 0  
for ycoord in dcp_vertex_y :
    if(abs(ycoord - dcp_vertex_y_min)<1.0e-6) :
        dcp_base_xmax = max(dcp_base_xmax,dcp_vertex_x[cntr])    
    cntr = cntr + 1 
        

# Uncomment the following lines to print out the vertex coordinates corresponding to the edges

#for alledges in mdb.models[mdlName].parts['DCP'].edges :
#    pnt_coords = alledges.pointOn[0]
#    end_nodes = alledges.getVertices()
#    end1_coords = mdb.models[mdlName].parts['DCP'].vertices[end_nodes[0]].pointOn[0]
#    end2_coords = mdb.models[mdlName].parts['DCP'].vertices[end_nodes[1]].pointOn[0]
#    #print((end1_coords,end2_coords)) 
#    print(alledges)

# Alternative definition of surface
mdb.models[mdlName].parts['DCP'].Surface(name='Srfc', side2Edges=
    mdb.models[mdlName].parts['DCP'].edges)


    
## UP PART DEFINITION
mdb.models[mdlName].ConstrainedSketch(name='__profile__', sheetSize=
    200.0)
mdb.models[mdlName].sketches['__profile__'].sketchOptions.setValues(
    viewStyle=AXISYM)
mdb.models[mdlName].sketches['__profile__'].ConstructionLine(point1=(
    0.0, -100.0), point2=(0.0, 100.0))

# Geometric sequence for UP to construct boundary segments     
UP_geoSeq = 'ACALLL'

# Number of segments constituting the UP
UP_segSize = len(UP_geoSeq)

# The UP is created a closed piecewise-smooth curve with anti-clockwise 
# orientation of the edges 
# List of x-coordinates 
UP_PointSet_x = [(1.03299999998103,1.02299999998098,1.03456197299954),
                 (1.07004999998105,1.03456197299954,1.11963511324961),
                 (1.12399999998098,1.11963511324961,1.14399999998096),
                 (1.14399999998096,1.14399999998096),
                 (1.14399999998096,1.02299999998098),
                 (1.02299999998098,1.02299999998098)]                 

# List of y-coordinates 
UP_PointSet_y = [(0.0317835403035396,0.0317835403035396,0.0219062815598612),
                 (-0.20250503709622,0.0219062815598612,0.019218115826849),
                 (0.0387359990066898,0.019218115826849,0.0387359990066898),
                 (0.0387359990066898,1.9656804163734),
                 (1.9656804163734,1.9656804163734),
                 (1.9656804163734,0.0317835403035396)]

# Run loop over number of curved segments to construct each segment
# Currently only line segments and circular arcs
for i in range(0,UP_segSize) :
    if UP_geoSeq[i] == 'L' :
        # Sketch line segment
        mdb.models[mdlName].sketches['__profile__'].Line(point1=(UP_PointSet_x[i][0],UP_PointSet_y[i][0]),
        point2=(UP_PointSet_x[i][1],UP_PointSet_y[i][1]))       
    elif UP_geoSeq[i] == 'A' :
        # Sketch arc of circle with anti-clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(UP_PointSet_x[i][0],UP_PointSet_y[i][0]),
        direction=COUNTERCLOCKWISE,
        point1=(UP_PointSet_x[i][1],UP_PointSet_y[i][1]),
        point2=(UP_PointSet_x[i][2],UP_PointSet_y[i][2]))
    elif UP_geoSeq[i] == 'C' :
        # Sketch arc of circle with clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(UP_PointSet_x[i][0],UP_PointSet_y[i][0]),
        direction=CLOCKWISE,
        point1=(UP_PointSet_x[i][1],UP_PointSet_y[i][1]),
        point2=(UP_PointSet_x[i][2],UP_PointSet_y[i][2]))

# Set part type after sketch completion                
mdb.models[mdlName].Part(dimensionality=AXISYMMETRIC, name='UP', type=
    ANALYTIC_RIGID_SURFACE)
mdb.models[mdlName].parts['UP'].AnalyticRigidSurf2DPlanar(sketch=
    mdb.models[mdlName].sketches['__profile__'])
# Exit part definition        
del mdb.models[mdlName].sketches['__profile__']

## To identify the UP reference point
# Initialize list containing y-coordinates of points near each edge
up_edgelist_ycoords = [] 
# Loop over edges to extract and store the y-coordinates
for upEdges in mdb.models[mdlName].parts['UP'].edges :
    up_edgelist_ycoords = up_edgelist_ycoords + [upEdges.pointOn[0][1]]
# Identify an index of the UP edge list with the maximum y-coordinate    
up_ycoord_maxindx = up_edgelist_ycoords.index(max(up_edgelist_ycoords))

# Set reference point as midpoint of the corresponding edge 
mdb.models[mdlName].parts['UP'].ReferencePoint(point=
    mdb.models[mdlName].parts['UP'].InterestingPoint(
    mdb.models[mdlName].parts['UP'].edges[up_ycoord_maxindx], MIDDLE))
mdb.models[mdlName].parts['UP'].Set(name='RefPt', referencePoints=(
    mdb.models[mdlName].parts['UP'].referencePoints[2], ))
    
# Extract coordinates corresponding to the point identified. This will be needed later to set
# datum point for the other end point of the spring
up_edge_endnodes = mdb.models[mdlName].parts['UP'].edges[up_ycoord_maxindx].getVertices()
up_edge_end1 = mdb.models[mdlName].parts['UP'].vertices[up_edge_endnodes[0]].pointOn[0]
up_edge_end2 = mdb.models[mdlName].parts['UP'].vertices[up_edge_endnodes[1]].pointOn[0]
upRefPoint_coords =  (0.5*(up_edge_end1[0] + up_edge_end2[0]),0.5*(up_edge_end1[1] + up_edge_end2[1]), \
                        0.5*(up_edge_end1[2] + up_edge_end2[2]) )
                        

# Alternative definition of surface
mdb.models[mdlName].parts['UP'].Surface(name='Srfc', side1Edges=mdb.models[mdlName].parts['UP'].edges)
    
# Mass
mdb.models[mdlName].parts['UP'].engineeringFeatures.PointMassInertia(
    alpha=0.0, composite=0.0, mass=0.00324, name='Mass', region=
    mdb.models[mdlName].parts['UP'].sets['RefPt'])    
    
## BDD PART DEFINITION
mdb.models[mdlName].ConstrainedSketch(name='__profile__', sheetSize=
    200.0)
mdb.models[mdlName].sketches['__profile__'].sketchOptions.setValues(
    viewStyle=AXISYM)
mdb.models[mdlName].sketches['__profile__'].ConstructionLine(point1=(
    0.0, -100.0), point2=(0.0, 100.0))  
    
# Geometric sequence for DCP to construct boundary segments
BDD_geoSeq = 'ALLLL'

# Number of segments constituting the BDD
BDD_segSize = len(BDD_geoSeq)


# The BDD is created an open piecewise-smooth curve with anti-clockwise 
# orientation of the edges
# List of x-coordinates 

BDD_PointSet_x = [(1.19899999998096,1.14899999998096,1.19899999998096),
                  (1.19899999998096,1.32964999998096),
                  (1.32964999998096,1.32964999998096),
                  (1.32964999998096,1.14899999998096),
                  (1.14899999998096,1.14899999998096)]                  
# List of y-coordinates
BDD_PointSet_y = [(0.0593804163734966,0.0593804163734966,0.00938041637349896),
                  (0.00938041637349896,0.00938041637349896),
                  (0.00938041637349896,1.17378),
                  (1.17378,1.17378),
                  (1.17378,0.0593804163734966)]                  

# Run loop over all segments to construct each segment
for i in range(0,BDD_segSize) :
    if BDD_geoSeq[i] == 'L' :
        # Sketch line segment
        mdb.models[mdlName].sketches['__profile__'].Line(point1=(BDD_PointSet_x[i][0],BDD_PointSet_y[i][0]),
        point2=(BDD_PointSet_x[i][1],BDD_PointSet_y[i][1]))       
    elif BDD_geoSeq[i] == 'A' :
        # Sketch arc of a circle with anti-clockwise orientation        
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(BDD_PointSet_x[i][0],BDD_PointSet_y[i][0]),
        direction=COUNTERCLOCKWISE,
        point1=(BDD_PointSet_x[i][1],BDD_PointSet_y[i][1]),
        point2=(BDD_PointSet_x[i][2],BDD_PointSet_y[i][2]))
    elif BDD_geoSeq[i] == 'C' :
        # Sketch arc of a circle with clockwise orientation    
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(BDD_PointSet_x[i][0],BDD_PointSet_y[i][0]),
        direction=CLOCKWISE,
        point1=(BDD_PointSet_x[i][1],BDD_PointSet_y[i][1]),
        point2=(BDD_PointSet_x[i][2],BDD_PointSet_y[i][2]))

# Set part type after sketch completion        
mdb.models[mdlName].Part(dimensionality=AXISYMMETRIC, name='BDD', 
    type=ANALYTIC_RIGID_SURFACE)
mdb.models[mdlName].parts['BDD'].AnalyticRigidSurf2DPlanar(sketch=
    mdb.models[mdlName].sketches['__profile__'])
# Exit part definition    
del mdb.models[mdlName].sketches['__profile__']    

## To identify the BDD reference point
# Initialize list containing y-coordinates of points near each edge
bdd_edgelist_ycoords = [] 
# Loop over edges to extract and store the y-coordinates
for bddEdges in mdb.models[mdlName].parts['BDD'].edges :
    bdd_edgelist_ycoords = bdd_edgelist_ycoords + [bddEdges.pointOn[0][1]]

# Identify an index of the BDD edge list with the maximum y-coordinate    
bdd_ycoord_maxindx = bdd_edgelist_ycoords.index(max(bdd_edgelist_ycoords))


# Set reference point as midpoint of the corresponding edge 
mdb.models[mdlName].parts['BDD'].ReferencePoint(point=
    mdb.models[mdlName].parts['BDD'].InterestingPoint(
    mdb.models[mdlName].parts['BDD'].edges[bdd_ycoord_maxindx], MIDDLE))
mdb.models[mdlName].parts['BDD'].Set(name='RefPt', referencePoints=(
    mdb.models[mdlName].parts['BDD'].referencePoints[2], ))
    
    
# Extract coordinates corresponding to the point identified. This will be needed later to set
# datum point for the other end point of the spring
bdd_edge_endnodes = mdb.models[mdlName].parts['BDD'].edges[bdd_ycoord_maxindx].getVertices()
bdd_edge_end1 = mdb.models[mdlName].parts['BDD'].vertices[bdd_edge_endnodes[0]].pointOn[0]
bdd_edge_end2 = mdb.models[mdlName].parts['BDD'].vertices[bdd_edge_endnodes[1]].pointOn[0]
bddRefPoint_coords =  (0.5*(bdd_edge_end1[0] + bdd_edge_end2[0]),0.5*(bdd_edge_end1[1] + bdd_edge_end2[1]), \
                        0.5*(bdd_edge_end1[2] + bdd_edge_end2[2]) )    


# Alternative definition of surface
mdb.models[mdlName].parts['BDD'].Surface(name='Srfc', side1Edges=
    mdb.models[mdlName].parts['BDD'].edges)    

## LP PART DEFINITION
mdb.models[mdlName].ConstrainedSketch(name='__profile__', sheetSize=
    200.0)
mdb.models[mdlName].sketches['__profile__'].sketchOptions.setValues(
    viewStyle=AXISYM)
mdb.models[mdlName].sketches['__profile__'].ConstructionLine(point1=(
    0.0, -100.0), point2=(0.0, 100.0)) 

# Geometric sequence for LP to construct boundary segments
LP_geoSeq = 'LALALL'

# Number of segments constituting the LP
LP_segSize = len(LP_geoSeq)

# The LP is created a closed piecewise-smooth curve with anti-clockwise 
# orientation of the edges 
# List of x-coordinates
LP_PointSet_x = [(1.32,1.32),
                 (1.30499999998102,1.32,1.30499999998102),
                 (1.30499999998102,1.17399999998099),
                 (1.17399999998099,1.17399999998099,1.15899999998099),
                 (1.15899999998099,1.15899999998099),
                 (1.15899999998099,1.32)]

# List of y-coordinates
LP_PointSet_y = [(-0.912546,-0.015),
                 (-0.015,-0.015,0.0),
                 (0.0,0.0),
                 (-0.015,0.0,-0.015),
                 (-0.015,-0.912546),
                 (-0.912546,-0.912546)]
# Run loop over number of curved segments to construct each segment
# Currently only line segments and circular arcs
for i in range(0,LP_segSize) :
    if LP_geoSeq[i] == 'L' :
        # Sketch line segment
        mdb.models[mdlName].sketches['__profile__'].Line(point1=(LP_PointSet_x[i][0],LP_PointSet_y[i][0]),
        point2=(LP_PointSet_x[i][1],LP_PointSet_y[i][1]))       
    elif LP_geoSeq[i] == 'A' :
        # Sketch arc of circle with anti-clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(LP_PointSet_x[i][0],LP_PointSet_y[i][0]),
        direction=COUNTERCLOCKWISE,
        point1=(LP_PointSet_x[i][1],LP_PointSet_y[i][1]),
        point2=(LP_PointSet_x[i][2],LP_PointSet_y[i][2]))
    elif LP_geoSeq[i] == 'C' :
        # Sketch arc of circle with clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(LP_PointSet_x[i][0],LP_PointSet_y[i][0]),
        direction=CLOCKWISE,
        point1=(LP_PointSet_x[i][1],LP_PointSet_y[i][1]),
        point2=(LP_PointSet_x[i][2],LP_PointSet_y[i][2]))

# Set part type after sketch completion        
mdb.models[mdlName].Part(dimensionality=AXISYMMETRIC, name='LP', 
    type=ANALYTIC_RIGID_SURFACE)
mdb.models[mdlName].parts['LP'].AnalyticRigidSurf2DPlanar(sketch=
    mdb.models[mdlName].sketches['__profile__'])
# Exit part definition      
del mdb.models[mdlName].sketches['__profile__'] 

## To identify the LP reference point
# Initialize list containing y-coordinates of points near each edge
lp_edgelist_ycoords = []
# Loop over edges to extract and store the y-coordinates 
for lpEdges in mdb.models[mdlName].parts['LP'].edges :
    lp_edgelist_ycoords = lp_edgelist_ycoords + [lpEdges.pointOn[0][1]]
# Identify an index of the LP edge list with the maximum y-coordinate    
lp_ycoord_minindx = lp_edgelist_ycoords.index(min(lp_edgelist_ycoords))

# Set reference point as midpoint of the corresponding edge 
mdb.models[mdlName].parts['LP'].ReferencePoint(point=
    mdb.models[mdlName].parts['LP'].InterestingPoint(
    mdb.models[mdlName].parts['LP'].edges[lp_ycoord_minindx], MIDDLE))
mdb.models[mdlName].parts['LP'].Set(name='RefPt', referencePoints=(
    mdb.models[mdlName].parts['LP'].referencePoints[2], )) 

# Extract coordinates corresponding to the point identified. This will be needed later to set
# datum point for the other end point of the spring
lp_edge_endnodes = mdb.models[mdlName].parts['LP'].edges[lp_ycoord_minindx].getVertices()
lp_edge_end1 = mdb.models[mdlName].parts['LP'].vertices[lp_edge_endnodes[0]].pointOn[0]
lp_edge_end2 = mdb.models[mdlName].parts['LP'].vertices[lp_edge_endnodes[1]].pointOn[0]
lpRefPoint_coords =  (0.5*(lp_edge_end1[0] + lp_edge_end2[0]),0.5*(lp_edge_end1[1] + lp_edge_end2[1]), \
                        0.5*(lp_edge_end1[2] + lp_edge_end2[2]) )

pointOn_list_x = [] 
pointOn_list_y = [] 
for alledges in  mdb.models[mdlName].parts['LP'].edges :
    pointOn_list_x = pointOn_list_x  + [alledges.pointOn[0][0]]
    pointOn_list_y = pointOn_list_y  + [alledges.pointOn[0][1]]
    
indx_ymax = pointOn_list_y.index(max(pointOn_list_y))
lp_top_endnodes = mdb.models[mdlName].parts['LP'].edges[indx_ymax].getVertices()
lp_top_end1 = mdb.models[mdlName].parts['LP'].vertices[lp_top_endnodes[0]].pointOn[0]
lp_top_end2 = mdb.models[mdlName].parts['LP'].vertices[lp_top_endnodes[1]].pointOn[0]     
lp_top_xmax = max(lp_top_end1[0],lp_top_end2[0])
lp_top_xmin = min(lp_top_end1[0],lp_top_end2[0])

# Alternative definition of surface
mdb.models[mdlName].parts['LP'].Surface(name='Srfc', side1Edges=
    mdb.models[mdlName].parts['LP'].edges)
    
# Point mass 
mdb.models[mdlName].parts['LP'].engineeringFeatures.PointMassInertia(
    alpha=0.0, composite=0.0, mass=0.00429, name='Mass', region=
    mdb.models[mdlName].parts['LP'].sets['RefPt'])

# Die Core Ring Part
mdb.models[mdlName].ConstrainedSketch(name='__profile__', sheetSize=
    200.0)
mdb.models[mdlName].sketches['__profile__'].sketchOptions.setValues(
    viewStyle=AXISYM)
mdb.models[mdlName].sketches['__profile__'].ConstructionLine(point1=(
    0.0, -100.0), point2=(0.0, 100.0))

# Geometric sequence for DCR to construct boundary segments
DCR_geoSeq = 'LAAALCALCALL'

# Number of segments constituting the DCR
DCR_segSize = len(DCR_geoSeq)

# The DCR is created a closed piecewise-smooth curve with anti-clockwise 
# orientation of the edges 
xp2 = 0.970631091510256
yp2 = -0.136807441842745
xp1 = 0.982206988479959
yp1 = -0.0888852326987504
r0 = dcr_radius # Modify this
r1 = 0.035
x0 = 0.910679732761366 + r0
theta_p = atan2(yp1 - yp2,xp1 - xp2)
theta_1 = pi/2 - theta_p 
x1 = xp2 - r1*cos(theta_1)
y1 = yp2 + r1*sin(theta_1)
theta_ang = atan2(sqrt((r0 + r1)*(r0 + r1) - (x1 - x0)*(x1 - x0)),x1 - x0)*180.0/pi 
y0 = y1 - (r0 + r1)*sin(theta_ang*pi/180.0)
tol_mod =  -0.22129170531813 - y0 + 0.0005
tol_add = max(0.0,tol_mod)

# Point set definition - x coordinates
DCR_PointSet_x = [(1.13944999998103,1.13944999998097),
                  (1.109449999981,1.13944999998097,1.11570396823498),
                  (1.07004999998099,1.11570396823498,1.04094798655819),
                  (1.05024999998102,1.04094798655819,0.982206988479959),
                  (0.982206988479959,0.970631091510256),
                  (x1,0.970631091510256,x1 - r1*cos(theta_ang*pi/180.0)),
                  (x0,x0 + r0*cos(theta_ang*pi/180.0),0.910679732761366),
                  (0.910679732761366,0.910679732761366),
                  (0.893979732761352,0.910679732761366,0.906359999625806),
                  (0.928599999981031,0.906359999625806,0.898599999981059),
                  (0.898599999981059,0.898599999981059),
                  (0.898599999981059,1.13944999998103)]
# Point set definition - y coordinates
DCR_PointSet_y = [(-0.694781976143879-tol_add,-0.068152387086009),
                  (-0.068152387086009,-0.068152387086009,-0.0388114961473107),
                  (-0.253,-0.0388114961473107,-0.0359422362256332),
                  (-0.1053214301261,-0.0359422362256332,-0.0888852326987504),
                  (-0.0888852326987504,-0.136807441842745),
                  (y1,-0.136807441842745,y1 - r1*sin(theta_ang*pi/180.0)),
                  (y0,y0 + r0*sin(theta_ang*pi/180.0),y0),
                  (y0,-0.22129170531813-tol_add),
                  (-0.22129170531813-tol_add,-0.22129170531813-tol_add,-0.232499693200268-tol_add),
                  (-0.25263380316817-tol_add,-0.232499693200268-tol_add,-0.25263380316817-tol_add),
                  (-0.25263380316817-tol_add,-0.694781976143879-tol_add),
                  (-0.694781976143879-tol_add,-0.694781976143879-tol_add)] 

# Run loop over number of curved segments to construct each segment
# Currently only line segments and circular arcs
for i in range(0,DCR_segSize) :
    if DCR_geoSeq[i] == 'L' :
        # Sketch line segment    
        mdb.models[mdlName].sketches['__profile__'].Line(point1=(DCR_PointSet_x[i][0],DCR_PointSet_y[i][0]),
        point2=(DCR_PointSet_x[i][1],DCR_PointSet_y[i][1]))       
    elif DCR_geoSeq[i] == 'A' :
        # Sketch arc of circle with anti-clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(DCR_PointSet_x[i][0],DCR_PointSet_y[i][0]),
        direction=COUNTERCLOCKWISE,
        point1=(DCR_PointSet_x[i][1],DCR_PointSet_y[i][1]),
        point2=(DCR_PointSet_x[i][2],DCR_PointSet_y[i][2]))
    elif DCR_geoSeq[i] == 'C' :
        # Sketch arc of circle with clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(DCR_PointSet_x[i][0],DCR_PointSet_y[i][0]),
        direction=CLOCKWISE,
        point1=(DCR_PointSet_x[i][1],DCR_PointSet_y[i][1]),
        point2=(DCR_PointSet_x[i][2],DCR_PointSet_y[i][2]))

# Set part type after sketch completion        
mdb.models[mdlName].Part(dimensionality=AXISYMMETRIC, name='DCR', 
    type=ANALYTIC_RIGID_SURFACE)
mdb.models[mdlName].parts['DCR'].AnalyticRigidSurf2DPlanar(sketch=
    mdb.models[mdlName].sketches['__profile__'])
# Exit part definition      
del mdb.models[mdlName].sketches['__profile__']    

## To identify the DCR reference point
# Initialize list containing y-coordinates of points near each edge
dcr_edgelist_ycoords = [] 
# Loop over edges to extract and store the y-coordinates
for dcrEdges in mdb.models[mdlName].parts['DCR'].edges :
    dcr_edgelist_ycoords = dcr_edgelist_ycoords + [dcrEdges.pointOn[0][1]]
# Identify an index of the DCR edge list with the maximum y-coordinate    
dcr_ycoord_minindx = dcr_edgelist_ycoords.index(min(dcr_edgelist_ycoords))

# Set reference point as midpoint of the corresponding edge 
mdb.models[mdlName].parts['DCR'].ReferencePoint(point=
    mdb.models[mdlName].parts['DCR'].InterestingPoint(
    mdb.models[mdlName].parts['DCR'].edges[dcr_ycoord_minindx], MIDDLE))
mdb.models[mdlName].parts['DCR'].Set(name='RefPt', referencePoints=(
    mdb.models[mdlName].parts['DCR'].referencePoints[2], ))
    
# Extract coordinates corresponding to the point identified. This will be needed later to set
# datum point for the other end point of the spring
dcr_edge_endnodes = mdb.models[mdlName].parts['DCR'].edges[dcr_ycoord_minindx].getVertices()
dcr_edge_end1 = mdb.models[mdlName].parts['DCR'].vertices[dcr_edge_endnodes[0]].pointOn[0]
dcr_edge_end2 = mdb.models[mdlName].parts['DCR'].vertices[dcr_edge_endnodes[1]].pointOn[0]
dcrRefPoint_coords =  (0.5*(dcr_edge_end1[0] + dcr_edge_end2[0]),0.5*(dcr_edge_end1[1] + dcr_edge_end2[1]), \
                        0.5*(dcr_edge_end1[2] + dcr_edge_end2[2]) )  

# Alternative definition of surface
mdb.models[mdlName].parts['DCR'].Surface(name='Srfc', side1Edges=
    mdb.models[mdlName].parts['DCR'].edges)    
    

## PP PART DEFINITION
mdb.models[mdlName].ConstrainedSketch(name='__profile__', sheetSize=
    200.0)
mdb.models[mdlName].sketches['__profile__'].sketchOptions.setValues(
    viewStyle=AXISYM)
mdb.models[mdlName].sketches['__profile__'].ConstructionLine(point1=(
    0.0, -100.0), point2=(0.0, 100.0))
    
cx_u = 0.811939962095721
cy_u = -0.173700000193601+pp_spacer_thickness-0.1625-upper_radius

cx_l = lr_opening/2.0 - lower_radius
cy_l = -0.173700000193601+pp_spacer_thickness-0.1625-upper_radius-t_value

delta_x = cx_u - cx_l

delta_y = t_value

reldis = sqrt(delta_x*delta_x + delta_y*delta_y)

delta_r = upper_radius - lower_radius
phi = atan2(-1.0*delta_x,delta_y)

theta = phi - atan2(delta_r,sqrt(reldis*reldis - delta_r*delta_r))

# Geometric sequence for PP to construct boundary segments
PP_geoSeq = 'LCLCLALALLL'

# Number of segments constituting the PP
PP_segSize = len(PP_geoSeq)

# The PP is created an open piecewise-smooth curve with clockwise 
# orientation of the edges 
PP_PointSet_x = [(0.0,cx_u),
                 (cx_u,cx_u,cx_u + upper_radius*cos(theta)),
                 (cx_u + upper_radius*cos(theta),cx_l + lower_radius*cos(theta)),
                 (cx_l,cx_l + lower_radius*cos(theta),lr_opening/2.0),
                 (lr_opening/2.0,lr_opening/2.0),
                 (0.877399999917372+(lr_opening/2.0-0.8504),lr_opening/2.0,0.854843504095641+(lr_opening/2.0-0.8504)),
                 (0.854843504095641+(lr_opening/2.0-0.8504),0.859087134403694+(lr_opening/2.0-0.8504)),
                 (0.876949999919361+(lr_opening/2.0-0.8504),0.859087134403694+(lr_opening/2.0-0.8504),0.876949999924477+(lr_opening/2.0-0.8504)),
                 (0.876949999924477+(lr_opening/2.0-0.8504),0.895499999928063),
                 (0.895499999928063,0.895499999980984),
                 (0.895499999980984,0.0)]
PP_PointSet_y = [(-0.173700000193601+pp_spacer_thickness-0.1625,-0.173700000004998+pp_spacer_thickness-0.1625),
                 (-0.173700000193601+pp_spacer_thickness-0.1625-upper_radius,-0.173700000099299+pp_spacer_thickness-0.1625,cy_u + upper_radius*sin(theta)),
                 (cy_u + upper_radius*sin(theta),cy_l + lower_radius*sin(theta)),
                 (cy_l,cy_l + lower_radius*sin(theta),cy_l),
                 (cy_l,-0.226699999996061+pp_spacer_thickness-0.1625-(catcher_depth-0.0829)),
                 (-0.226699999989787+pp_spacer_thickness-0.1625-(catcher_depth-0.0829),-0.226699999996061+pp_spacer_thickness-0.1625-(catcher_depth-0.0829),-0.241539288929622+pp_spacer_thickness-0.1625-(catcher_depth-0.0829)),
                 (-0.241539288929622+pp_spacer_thickness-0.1625-(catcher_depth-0.0829),-0.247442041711131+pp_spacer_thickness-0.1625-(catcher_depth-0.0829)),
                 (-0.234599999989743+pp_spacer_thickness-0.1625-(catcher_depth-0.0829),-0.247442041711131+pp_spacer_thickness-0.1625-(catcher_depth-0.0829),-0.256599999989873+pp_spacer_thickness-0.1625-(catcher_depth-0.0829)),
                 (-0.256599999989873+pp_spacer_thickness-0.1625-(catcher_depth-0.0829),-0.256599999987955+pp_spacer_thickness-0.1625-(catcher_depth-0.0829)),
                 (-0.256599999987955+pp_spacer_thickness-0.1625-(catcher_depth-0.0829),-0.485000000018093+pp_spacer_thickness-0.1625),
                 (-0.485000000018093+pp_spacer_thickness-0.1625,-0.485000000018093+pp_spacer_thickness-0.1625)]

# Run loop over number of curved segments to construct each segment
# Currently only line segments and circular arcs
for i in range(0,PP_segSize) :
    if PP_geoSeq[i] == 'L' :
        # Sketch line segment
        mdb.models[mdlName].sketches['__profile__'].Line(point1=(PP_PointSet_x[i][0],PP_PointSet_y[i][0]),
        point2=(PP_PointSet_x[i][1],PP_PointSet_y[i][1]))       
    elif PP_geoSeq[i] == 'A' :
        # Sketch arc of circle with anti-clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(PP_PointSet_x[i][0],PP_PointSet_y[i][0]),
        direction=COUNTERCLOCKWISE,
        point1=(PP_PointSet_x[i][1],PP_PointSet_y[i][1]),
        point2=(PP_PointSet_x[i][2],PP_PointSet_y[i][2]))
    elif PP_geoSeq[i] == 'C' :
        # Sketch arc of circle with clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(PP_PointSet_x[i][0],PP_PointSet_y[i][0]),
        direction=CLOCKWISE,
        point1=(PP_PointSet_x[i][1],PP_PointSet_y[i][1]),
        point2=(PP_PointSet_x[i][2],PP_PointSet_y[i][2]))

# Set part type after sketch completion 
mdb.models[mdlName].Part(dimensionality=AXISYMMETRIC, name='PP', type=
    ANALYTIC_RIGID_SURFACE)
mdb.models[mdlName].parts['PP'].AnalyticRigidSurf2DPlanar(sketch=
    mdb.models[mdlName].sketches['__profile__'])
# Exit part definition    
del mdb.models[mdlName].sketches['__profile__']    

## To identify the PP reference point
# Initialize list containing y-coordinates of points near each edge
pp_edgelist_ycoords = [] 
# Loop over edges to extract and store the y-coordinates
for ppEdges in mdb.models[mdlName].parts['PP'].edges :
    pp_edgelist_ycoords = pp_edgelist_ycoords + [ppEdges.pointOn[0][1]]
# Identify an index of the DCP edge list with the maximum y-coordinate    
pp_ycoord_minindx = pp_edgelist_ycoords.index(min(pp_edgelist_ycoords))

# Set reference point as midpoint of the corresponding edge 
mdb.models[mdlName].parts['PP'].ReferencePoint(point=
    mdb.models[mdlName].parts['PP'].InterestingPoint(
    mdb.models[mdlName].parts['PP'].edges[pp_ycoord_minindx], MIDDLE))
mdb.models[mdlName].parts['PP'].Set(name='RefPt', referencePoints=(
    mdb.models[mdlName].parts['PP'].referencePoints[2], ))
    
# Extract coordinates corresponding to the point identified. This will be needed later to set
# datum point for the other end point of the spring
pp_edge_endnodes = mdb.models[mdlName].parts['PP'].edges[pp_ycoord_minindx].getVertices()
pp_edge_end1 = mdb.models[mdlName].parts['PP'].vertices[pp_edge_endnodes[0]].pointOn[0]
pp_edge_end2 = mdb.models[mdlName].parts['PP'].vertices[pp_edge_endnodes[1]].pointOn[0]
ppRefPoint_coords =  (0.5*(pp_edge_end1[0] + pp_edge_end2[0]),0.5*(pp_edge_end1[1] + pp_edge_end2[1]), \
                        0.5*(pp_edge_end1[2] + pp_edge_end2[2]) )  
    

## Identify xmax on PP top
# List of x and y coordinates of all edge vertices(double counting vertices)
pp_vertex_y = []
pp_vertex_x = []
for alledges in mdb.models[mdlName].parts['PP'].edges :
    pnt_coords = alledges.pointOn[0]
    end_nodes = alledges.getVertices()
    end1_coords = mdb.models[mdlName].parts['PP'].vertices[end_nodes[0]].pointOn[0]
    end2_coords = mdb.models[mdlName].parts['PP'].vertices[end_nodes[1]].pointOn[0]
    pp_vertex_y = pp_vertex_y + [end1_coords[1]] + [end2_coords[1]]
    pp_vertex_x = pp_vertex_x + [end1_coords[0]] + [end2_coords[0]]

# Identify an index with maximum y-coordinate
pp_vertex_y_maxindx = pp_vertex_y.index(max(pp_vertex_y))
# Maximum y-coordinate 
pp_vertex_y_max = max(pp_vertex_y)
# Set a possible x value as the x-coordinate of the index identified earlier
pp_base_xmax = pp_vertex_x[pp_vertex_y_maxindx]

# Loop over vertices to check for minimum y-coordinate and maximum x-coordinate 
cntr = 0  
for ycoord in pp_vertex_y :
    if(abs(ycoord - pp_vertex_y_max)<1.0e-6) :
        pp_base_xmax = max(pp_base_xmax,pp_vertex_x[cntr])    
    cntr = cntr + 1 
    

# Alternative definition of surface
mdb.models[mdlName].parts['PP'].Surface(name='Srfc', side1Edges=
    mdb.models[mdlName].parts['PP'].edges)    
    
# Mass
mdb.models[mdlName].parts['PP'].engineeringFeatures.PointMassInertia(
    alpha=0.0, composite=0.0, mass=0.00503, name='Mass', region=
    mdb.models[mdlName].parts['PP'].sets['RefPt'])    
   

## MATERIAL PROPERTIES OF AA 3104
elasticModulus = 10000000.0
poissonRatio = 0.32
density = 0.00026
## Import csv file with parameter values 
material_dat = []
with open('sedata.csv', 'r') as file:
    reader = csv.reader(file)
    for row in reader:
        material_dat = material_dat + [row]
        
material_dat = material_dat[1:]

plasticityData = []
for row in material_dat : 
    plasticityData = plasticityData + [(float(row[1]),float(row[0]))]    

mdb.models[mdlName].Material(name='AA3104')
mdb.models[mdlName].materials['AA3104'].Elastic(table=((elasticModulus,poissonRatio), ))
mdb.models[mdlName].materials['AA3104'].Density(table=((density, ), ))
mdb.models[mdlName].materials['AA3104'].Plastic(table=plasticityData)

## DEFINE SECTION  
mdb.models[mdlName].HomogeneousSolidSection(material='AA3104', name=
    'CanEnd', thickness=None)

# BLANK PART DEFINITION   
mdb.models[mdlName].ConstrainedSketch(name='__profile__', sheetSize=
    200.0)
mdb.models[mdlName].sketches['__profile__'].sketchOptions.setValues(
    viewStyle=AXISYM)
mdb.models[mdlName].sketches['__profile__'].ConstructionLine(point1=(
    0.0, -100.0), point2=(0.0, 100.0))

# Geometric sequence for blank to construct boundary segments   
BLANK_geoSeq = 'LLLL'
# Number of segments constituting the blank
BLANK_segSize = len(BLANK_geoSeq)

# Gauge 
blankGauge = 0.0082
# Length of blank
blankLength = 1.32965

# List of x-coordinates 
BLANK_PointSet_x = [(0.0,blankLength),
                    (blankLength,blankLength),
                    (blankLength,0.0),
                    (0.0,0.0)]
# List of y-coordinates 
BLANK_PointSet_y = [(0.0, 0.0),
                    (0.0,blankGauge),
                    (blankGauge,blankGauge),
                    (blankGauge,0.0)]    
# Run loop over number of curved segments to construct each segment
# Currently only line segments and circular arcs are used as the basic geometries 
# for the segments to construct curves 
for i in range(0,BLANK_segSize) :
    if BLANK_geoSeq[i] == 'L' :
        # Sketch line segment
        mdb.models[mdlName].sketches['__profile__'].Line(point1=(BLANK_PointSet_x[i][0],BLANK_PointSet_y[i][0]),
        point2=(BLANK_PointSet_x[i][1],BLANK_PointSet_y[i][1]))       
    elif BLANK_geoSeq[i] == 'A' :
        # Sketch arc of a circle with anti-clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(BLANK_PointSet_x[i][0],BLANK_PointSet_y[i][0]),
        direction=COUNTERCLOCKWISE,
        point1=(BLANK_PointSet_x[i][1],BLANK_PointSet_y[i][1]),
        point2=(BLANK_PointSet_x[i][2],BLANK_PointSet_y[i][2]))
    elif BLANK_geoSeq[i] == 'C' :
        # Sketch arc of a circle with clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(BLANK_PointSet_x[i][0],BLANK_PointSet_y[i][0]),
        direction=CLOCKWISE,
        point1=(BLANK_PointSet_x[i][1],BLANK_PointSet_y[i][1]),
        point2=(BLANK_PointSet_x[i][2],BLANK_PointSet_y[i][2]))
        
# Set part type after sketch completion 
mdb.models[mdlName].Part(dimensionality=AXISYMMETRIC, name='Blank', 
    type=DEFORMABLE_BODY)
mdb.models[mdlName].parts['Blank'].BaseShell(sketch=
    mdb.models[mdlName].sketches['__profile__'])
# Exit part definition 
del mdb.models[mdlName].sketches['__profile__']

## CREATE NODE SETS 
mdb.models[mdlName].parts['Blank'].Set(faces=
    mdb.models[mdlName].parts['Blank'].faces, name='Blank')
distToler = 1.0e-6

# Loop over blank edges   
for alledges in mdb.models[mdlName].parts['Blank'].edges :   
    # Obtain coordinates of point on edge and edge vertices 
    pnt_coords = alledges.pointOn[0]
    end_nodes = alledges.getVertices()
    end1_coords = mdb.models[mdlName].parts['Blank'].vertices[end_nodes[0]].pointOn[0]
    end2_coords = mdb.models[mdlName].parts['Blank'].vertices[end_nodes[1]].pointOn[0]
    
    
    if (abs(pnt_coords[0])<distToler) :
        # Create node set corresponding to the symmetric edge 
        mdb.models[mdlName].parts['Blank'].Set(edges=EdgeArray([alledges]),name='SymmSeg')    
    elif (abs(pnt_coords[1] - blankGauge)<distToler) :
        # Create node set corresponding to the top edge 
        mdb.models[mdlName].parts['Blank'].Set(edges=EdgeArray([alledges]),name='TopEdge') 
        # Create surface corresponding to top edge 
        if(end2_coords[0] > end1_coords[0]) :
            mdb.models[mdlName].parts['Blank'].Surface(name='UpperSurf',
                side1Edges=EdgeArray([alledges]))
        else :
            mdb.models[mdlName].parts['Blank'].Surface(name='UpperSurf',
                side2Edges=EdgeArray([alledges]))   
    elif (abs(pnt_coords[1])<distToler) :
        # Create node set corresponding to the bottom edge
        mdb.models[mdlName].parts['Blank'].Set(edges=EdgeArray([alledges]),name='BotEdge')    
        # Create surface corresponding to bottom edge 
        if(end2_coords[0] > end1_coords[0]) :
            mdb.models[mdlName].parts['Blank'].Surface(name='LowerSurf',
                side2Edges=EdgeArray([alledges]))
        else :
            mdb.models[mdlName].parts['Blank'].Surface(name='LowerSurf',
                side1Edges=EdgeArray([alledges]))

mdb.models[mdlName].parts['Blank'].DatumCsysByThreePoints(coordSysType=
    CARTESIAN, name='DatumCsysForLocalCsys', origin=
    mdb.models[mdlName].parts['Blank'].vertices[1], point1=
    mdb.models[mdlName].parts['Blank'].vertices[2], point2=
    mdb.models[mdlName].parts['Blank'].vertices[0])

mdb.models[mdlName].parts['Blank'].MaterialOrientation(
    additionalRotationField='', additionalRotationType=ROTATION_NONE, angle=0.0
    , axis=AXIS_3, fieldName='', localCsys=
    mdb.models[mdlName].parts['Blank'].datums[mdb.models[mdlName].parts['Blank'].datums.keys()[1]], orientationType=SYSTEM, 
    region=mdb.models[mdlName].parts['Blank'].sets['Blank'], stackDirection=
    STACK_3)
## PARTITION FACE BY DATUM PLANE
# Here the partition offset is computed based as follows 
# 1. Identify the maximum x-coordinate among the bottom edge vertices of DCP
# 2. Identify the maximum x-coordinate among the top edge vertices of PP
# 3. Find the minimum among those coordinates
# 4. Multiply it by some fraction to be conservative 
partition_offset_max = min(pp_base_xmax,dcp_base_xmax)
offset_fraction = 0.98   
partition_offset = offset_fraction * partition_offset_max

# Hardcode partition offset 
# Offset distance for the symmetric edge
#partition_offset = 0.7


# Offset computed from positions of tools 
mdb.models[mdlName].parts['Blank'].DatumPlaneByPrincipalPlane(
    offset=partition_offset, principalPlane=YZPLANE)
  
# Blank face is partitioned by extracting id of the datum plane(dictionary key)
mdb.models[mdlName].parts['Blank'].PartitionFaceByDatumPlane(
    datumPlane=mdb.models[mdlName].parts['Blank'].datums[mdb.models[mdlName].parts['Blank'].datums.keys()[2]], 
    faces=mdb.models[mdlName].parts['Blank'].faces.findAt((mdb.models[mdlName].parts['Blank'].faces[0].pointOn[0], )))

## SECTION ASSIGNMENT
mdb.models[mdlName].parts['Blank'].SectionAssignment(offset=0.0, 
    offsetField='', offsetType=MIDDLE_SURFACE, region=
    mdb.models[mdlName].parts['Blank'].sets['Blank'], sectionName=
    'CanEnd', thicknessAssignment=FROM_SECTION) 

# Create edge arrays corresponding to partition with coarse and fine meshes 
coarse_edge = []
fine_edge = []
vertical_edge = []

for alledges in mdb.models[mdlName].parts['Blank'].edges :
    pnt_coords = alledges.pointOn
    
    if ((pnt_coords[0][0] - partition_offset) <= -1.0e-6) and (pnt_coords[0][0] >= 1.0e-6) :
        coarse_edge = coarse_edge + [alledges]
    elif ((pnt_coords[0][0] - partition_offset) >= 1.0e-6) and ((pnt_coords[0][0] - blankLength) <= -1.0e-6) :
        fine_edge = fine_edge + [alledges]
    else :
        vertical_edge = vertical_edge + [alledges]      


# Create seeds on fine edge set 
aspect_ratio = 1.5 
fine_seed_size = blankGauge/6.0*aspect_ratio 
mdb.models[mdlName].parts['Blank'].seedEdgeBySize(constraint=FINER, 
    deviationFactor=0.1, edges=EdgeArray(fine_edge)
    , size=fine_seed_size)
# Create seeds on fine edge set 
vertical_seed_size = blankGauge/6.0 
mdb.models[mdlName].parts['Blank'].seedEdgeBySize(constraint=FINER, 
    deviationFactor=0.1, edges=EdgeArray(vertical_edge)
    , size=vertical_seed_size)
# Create seeds on coarse edge set
coarse_seed_size = fine_seed_size*3.8 
mdb.models[mdlName].parts['Blank'].seedEdgeBySize(constraint=FINER, 
    deviationFactor=0.1, edges=EdgeArray(coarse_edge)
    , size=coarse_seed_size)    
# Mesh blank
mdb.models[mdlName].parts['Blank'].generateMesh() 



## LP_BDD_RECTANGLE PART DEFINITION
# Sketching tool
mdb.models[mdlName].ConstrainedSketch(name='__profile__', sheetSize=
    200.0)
mdb.models[mdlName].sketches['__profile__'].sketchOptions.setValues(
    viewStyle=AXISYM)
mdb.models[mdlName].sketches['__profile__'].ConstructionLine(point1=(
    0.0, -100.0), point2=(0.0, 100.0))    

# Geometric sequence for DCP to construct boundary segments
# L : Line segment 
# A : Anticlockwise arc of a circle 
# C : Clockwise arc of a circle
lp_bdd_rect_geoSeq = 'LLLL'

# Number of segments constituting the DCP
lp_bdd_rect_segSize = len(lp_bdd_rect_geoSeq)


# The Spacer is created a closed piecewise-smooth curve with anti-clockwise 
# orientation of the edges 
# List of x-coordinates 
lp_bdd_rect_PointSet_x = [(lp_top_xmax,lp_top_xmax),
                  (lp_top_xmax,lp_top_xmin),
                  (lp_top_xmin,lp_top_xmin),
                  (lp_top_xmin,lp_top_xmax)]
# List of y-coordinates 
lp_bdd_rect_PointSet_y = [(0.0,blankGauge/10.0),
                  (blankGauge/10.0,blankGauge/10.0),
                  (blankGauge/10.0,0.0),
                  (0.0,0.0)]

# Run loop over number of curved segments to construct each segment
# Currently only line segments and circular arcs are used as the basic geometries 
# for the segments to construct curves 
for i in range(0,lp_bdd_rect_segSize) :
    if lp_bdd_rect_geoSeq[i] == 'L' :
        # Sketch line segment
        mdb.models[mdlName].sketches['__profile__'].Line(point1=(lp_bdd_rect_PointSet_x[i][0],lp_bdd_rect_PointSet_y[i][0]),
        point2=(lp_bdd_rect_PointSet_x[i][1],lp_bdd_rect_PointSet_y[i][1]))       
    elif lp_bdd_rect_geoSeq[i] == 'A' :
        # Sketch arc of a circle with anti-clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(lp_bdd_rect_PointSet_x[i][0],lp_bdd_rect_PointSet_y[i][0]),
        direction=COUNTERCLOCKWISE,
        point1=(lp_bdd_rect_PointSet_x[i][1],lp_bdd_rect_PointSet_y[i][1]),
        point2=(lp_bdd_rect_PointSet_x[i][2],lp_bdd_rect_PointSet_y[i][2]))
    elif lp_bdd_rect_geoSeq[i] == 'C' :
        # Sketch arc of a circle with clockwise orientation
        mdb.models[mdlName].sketches['__profile__'].ArcByCenterEnds(center=(lp_bdd_rect_PointSet_x[i][0],lp_bdd_rect_PointSet_y[i][0]),
        direction=CLOCKWISE,
        point1=(lp_bdd_rect_PointSet_x[i][1],lp_bdd_rect_PointSet_y[i][1]),
        point2=(lp_bdd_rect_PointSet_x[i][2],lp_bdd_rect_PointSet_y[i][2]))

# Set part type after sketch completion        
mdb.models[mdlName].Part(dimensionality=AXISYMMETRIC, 
    name='LP_BDD_RECTANGLE', type=DISCRETE_RIGID_SURFACE)
mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].BaseWire(sketch=
    mdb.models[mdlName].sketches['__profile__'])
# Exit part definition    
del mdb.models[mdlName].sketches['__profile__'] 


## To identify the Spacer reference point
# Initialize list containing y-coordinates of points near each edge
lp_bdd_rect_edgelist_ycoords = [] 
# Loop over edges to extract and store the y-coordinates
for lp_bdd_rect_Edges in mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].edges :
    lp_bdd_rect_edgelist_ycoords = lp_bdd_rect_edgelist_ycoords + [lp_bdd_rect_Edges.pointOn[0][1]]

# Identify an index of the LP_BDD_Rectangle edge list with the minimum y-coordinate
lp_bdd_rect_ycoord_minindx = lp_bdd_rect_edgelist_ycoords.index(min(lp_bdd_rect_edgelist_ycoords))

# Set reference point as midpoint of the corresponding edge 
mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].ReferencePoint(point=
    mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].InterestingPoint(
    mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].edges[lp_bdd_rect_ycoord_minindx], MIDDLE))
mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].Set(name='RefPt', referencePoints=(
    mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].referencePoints[2], ))


# Extract coordinates corresponding to the point identified. This will be needed later to define 
# the other end point of the spring as a datum point
lp_bdd_rect_edge_endnodes = mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].edges[lp_bdd_rect_ycoord_minindx].getVertices()
lp_bdd_rect_edge_end1 = mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].vertices[lp_bdd_rect_edge_endnodes[0]].pointOn[0]
lp_bdd_rect_edge_end2 = mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].vertices[lp_bdd_rect_edge_endnodes[1]].pointOn[0]
lp_bdd_rect_RefPoint_coords =  (0.5*(lp_bdd_rect_edge_end1[0] + lp_bdd_rect_edge_end2[0]),0.5*(lp_bdd_rect_edge_end1[1] + lp_bdd_rect_edge_end2[1]), \
                        0.5*(lp_bdd_rect_edge_end1[2] + lp_bdd_rect_edge_end2[2]) )



mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].seedEdgeByNumber(constraint=FINER,
    edges=mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].edges, number=1)
    
mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].generateMesh()

# Alternative definition of surface
mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].Surface(name='Srfc', side2Edges=
    mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].edges) 
    
# Point mass 
mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].engineeringFeatures.PointMassInertia(
    alpha=0.0, composite=0.0, mass=1.0e-6, name='Mass', region=
    mdb.models[mdlName].parts['LP_BDD_RECTANGLE'].sets['RefPt'])    

## ASSEMBLY
mdb.models[mdlName].rootAssembly.DatumCsysByThreePoints(coordSysType=
    CYLINDRICAL, origin=(0.0, 0.0, 0.0), point1=(1.0, 0.0, 0.0), point2=(0.0, 
    0.0, -1.0))
mdb.models[mdlName].rootAssembly.Instance(dependent=ON, name='BDD-1', 
    part=mdb.models[mdlName].parts['BDD'])
mdb.models[mdlName].rootAssembly.Instance(dependent=ON, name='Blank-1'
    , part=mdb.models[mdlName].parts['Blank'])
mdb.models[mdlName].rootAssembly.Instance(dependent=ON, name='DCP-1', 
    part=mdb.models[mdlName].parts['DCP'])

mdb.models[mdlName].rootAssembly.Instance(dependent=ON, name='DCR-1', 
    part=mdb.models[mdlName].parts['DCR'])
mdb.models[mdlName].rootAssembly.Instance(dependent=ON, name='IPS-1', 
    part=mdb.models[mdlName].parts['IPS'])
    
mdb.models[mdlName].rootAssembly.Instance(dependent=ON, name='LP-1', 
    part=mdb.models[mdlName].parts['LP'])
mdb.models[mdlName].rootAssembly.Instance(dependent=ON, name='PP-1', 
    part=mdb.models[mdlName].parts['PP'])
mdb.models[mdlName].rootAssembly.Instance(dependent=ON, name='UP-1', 
    part=mdb.models[mdlName].parts['UP'])
mdb.models[mdlName].rootAssembly.Instance(dependent=ON, name='Spacer-1', 
    part=mdb.models[mdlName].parts['Spacer'])   
mdb.models[mdlName].rootAssembly.Instance(dependent=ON, name='LP_BDD_RECTANGLE-1', 
    part=mdb.models[mdlName].parts['LP_BDD_RECTANGLE'])  
   
# Spring end point coordinates
ips_springend_coords = [ipsRefPoint_coords[0],ipsRefPoint_coords[1]+2.00,ipsRefPoint_coords[2]]
up_springend_coords = [upRefPoint_coords[0],upRefPoint_coords[1]+2.00,upRefPoint_coords[2]]
lp_springend_coords = [lpRefPoint_coords[0],lpRefPoint_coords[1]-2.00,lpRefPoint_coords[2]]
pp_springend_coords = [ppRefPoint_coords[0],ppRefPoint_coords[1]-2.00,ppRefPoint_coords[2]]
# Datum points for spring end point coordinates     
mdb.models[mdlName].rootAssembly.DatumPointByCoordinate(coords=ips_springend_coords)
mdb.models[mdlName].rootAssembly.DatumPointByCoordinate(coords=up_springend_coords)
mdb.models[mdlName].rootAssembly.DatumPointByCoordinate(coords=lp_springend_coords)
mdb.models[mdlName].rootAssembly.DatumPointByCoordinate(coords=pp_springend_coords)  
# Change name of datum points    
mdb.models[mdlName].rootAssembly.features.changeKey(fromName=
    'Datum pt-1', toName='IPS_Datum')
mdb.models[mdlName].rootAssembly.features.changeKey(fromName=
    'Datum pt-2', toName='UP_Datum')
mdb.models[mdlName].rootAssembly.features.changeKey(fromName=
    'Datum pt-3', toName='LP_Datum')
mdb.models[mdlName].rootAssembly.features.changeKey(fromName=
    'Datum pt-4', toName='PP_Datum')

   
# Create reference points from datum points 
spring_end_refpt_id = mdb.models[mdlName].rootAssembly.datums.keys()[1]
# Needed to change numbering manually. Earlier it was 88, 89, 90, 91
mdb.models[mdlName].rootAssembly.ReferencePoint(point=
    mdb.models[mdlName].rootAssembly.datums[spring_end_refpt_id])
mdb.models[mdlName].rootAssembly.ReferencePoint(point=
    mdb.models[mdlName].rootAssembly.datums[spring_end_refpt_id+1])
mdb.models[mdlName].rootAssembly.ReferencePoint(point=
    mdb.models[mdlName].rootAssembly.datums[spring_end_refpt_id+2])
mdb.models[mdlName].rootAssembly.ReferencePoint(point=
    mdb.models[mdlName].rootAssembly.datums[spring_end_refpt_id+3])
# Change name of reference points     
mdb.models[mdlName].rootAssembly.features.changeKey(fromName='RP-1', 
    toName='IPS_SPRP')
mdb.models[mdlName].rootAssembly.features.changeKey(fromName='RP-2', 
    toName='UP_SPRP')
mdb.models[mdlName].rootAssembly.features.changeKey(fromName='RP-3', 
    toName='LP_SPRP')
mdb.models[mdlName].rootAssembly.features.changeKey(fromName='RP-4', 
    toName='PP_SPRP')
    
# Needed to change numbering manually. Earlier it was 106, 107, 108, 109
mdb.models[mdlName].rootAssembly.Set(name='Spring_IPS_Pt', 
    referencePoints=(
    mdb.models[mdlName].rootAssembly.referencePoints[spring_end_refpt_id+4], ))
mdb.models[mdlName].rootAssembly.Set(name='Spring_UP_Pt', 
    referencePoints=(
    mdb.models[mdlName].rootAssembly.referencePoints[spring_end_refpt_id+5], ))
mdb.models[mdlName].rootAssembly.Set(name='Spring_LP_Pt', 
    referencePoints=(
    mdb.models[mdlName].rootAssembly.referencePoints[spring_end_refpt_id+6], ))
mdb.models[mdlName].rootAssembly.Set(name='Spring_PP_Pt', 
    referencePoints=(
    mdb.models[mdlName].rootAssembly.referencePoints[spring_end_refpt_id+7], ))    
# Spring masses
spring_mass = 1.0e-6
mdb.models[mdlName].rootAssembly.engineeringFeatures.PointMassInertia(
    alpha=0.0, composite=0.0, mass=spring_mass, name='IPS_Spring_Mass', region=
    mdb.models[mdlName].rootAssembly.sets['Spring_IPS_Pt'])
mdb.models[mdlName].rootAssembly.engineeringFeatures.PointMassInertia(
    alpha=0.0, composite=0.0, mass=spring_mass, name='UP_Spring_Mass', region=
    mdb.models[mdlName].rootAssembly.sets['Spring_UP_Pt'])
    
## INITIAL STEP
mdb.models[mdlName].VelocityBC(amplitude=UNSET, createStepName=
    'Initial', distributionType=UNIFORM, fieldName='', localCsys=None, name=
    'Blank_Symm', region=
    mdb.models[mdlName].rootAssembly.instances['Blank-1'].sets['SymmSeg']
    , v1=0.0, v2=UNSET, vr3=0.0)
mdb.models[mdlName].EncastreBC(createStepName='Initial', localCsys=
    None, name='DCR_EndFixed', region=
    mdb.models[mdlName].rootAssembly.instances['DCR-1'].sets['RefPt'])
mdb.models[mdlName].EncastreBC(createStepName='Initial', localCsys=
    None, name='PP_Spring_FixedEnd', region=
    mdb.models[mdlName].rootAssembly.sets['Spring_PP_Pt'])
mdb.models[mdlName].EncastreBC(createStepName='Initial', localCsys=
    None, name='LP_Spring_FixedEnd', region=
    mdb.models[mdlName].rootAssembly.sets['Spring_LP_Pt'])    
    
## FORMING STEP
#stroke_length = 1.70206
##bdc_to_lp_top = 371.16e-03
#cyc_per_second = 5 

# Coordinates of the bottom of DCP
##dcp_bottom = min(dcp_edgelist_ycoords)
# Coordinates of the top of DCP
##lp_top = max(lp_edgelist_ycoords)

# Distance of the DCP bottom from the BDC
##bdc_to_dcp_bottom = bdc_to_lp_top + (dcp_bottom - lp_top)
# Time taken for the DCP bottom to travel to BDC
# time_travel = math.acos(1.0 - 2.0*bdc_to_dcp_bottom/stroke_length)/2.0/math.pi/cyc_per_second 
time_travel = 0.053
# Initial velocity
# velocity_init = bdc_to_dcp_bottom*2.0/time_travel
velocity_init = 18.44

# Create step
mdb.models[mdlName].ExplicitDynamicsStep(description='', 
    improvedDtMethod=ON, name='Forming', previous='Initial', timePeriod=
    2.0*time_travel)
# Set output variables   
n_output_intervals = 100
mdb.models[mdlName].fieldOutputRequests['F-Output-1'].setValues(
    variables=('A', 'COORD', 'CSTRESS', 'EVOL', 'LE', 'MISES', 'PE', 'PEEQ', 
    'RF', 'S', 'STH', 'SVAVG', 'U', 'V'),numIntervals=n_output_intervals)   
    
## INTERACTIONS

# Interaction property 
# Tool and blank - Normal and tangential behavior
mdb.models[mdlName].ContactProperty('ToolBlankInteractProps')
mdb.models[mdlName].interactionProperties['ToolBlankInteractProps'].TangentialBehavior(
    dependencies=0, directionality=ISOTROPIC, elasticSlipStiffness=None, 
    formulation=PENALTY, fraction=0.005, maximumElasticSlip=FRACTION, 
    pressureDependency=OFF, shearStressLimit=None, slipRateDependency=OFF, 
    table=((friction_coeff, ), ), temperatureDependency=OFF)
mdb.models[mdlName].interactionProperties['ToolBlankInteractProps'].NormalBehavior(
    allowSeparation=ON, constraintEnforcementMethod=DEFAULT, 
    pressureOverclosure=HARD)    
# Tool and tool - Normal and tangential behavior
mdb.models[mdlName].ContactProperty('ToolToolInteractProps')
mdb.models[mdlName].interactionProperties['ToolToolInteractProps'].TangentialBehavior(
    formulation=FRICTIONLESS)
mdb.models[mdlName].interactionProperties['ToolToolInteractProps'].NormalBehavior(
    allowSeparation=ON, constraintEnforcementMethod=DEFAULT, 
    pressureOverclosure=HARD)    
# Interactions between surfaces 
# BDD and blank top surface 
mdb.models[mdlName].SurfaceToSurfaceContactExp(clearanceRegion=None, 
    createStepName='Forming', datumAxis=None, initialClearance=OMIT, 
    interactionProperty='ToolBlankInteractProps',mechanicalConstraint=KINEMATIC,name='BDD_Blank_Int',
	main=mdb.models[mdlName].rootAssembly.instances['BDD-1'].surfaces['Srfc'],
	secondary=mdb.models[mdlName].rootAssembly.instances['Blank-1'].surfaces['UpperSurf'],sliding=FINITE)
# DCP and blank top surface     
mdb.models[mdlName].SurfaceToSurfaceContactExp(clearanceRegion=None, 
    createStepName='Forming', datumAxis=None, initialClearance=OMIT, 
    interactionProperty='ToolBlankInteractProps', main=
    mdb.models[mdlName].rootAssembly.instances['DCP-1'].surfaces['Srfc']
    , mechanicalConstraint=KINEMATIC, name='DCP_Blank_Int', secondary=
    mdb.models[mdlName].rootAssembly.instances['Blank-1'].surfaces['UpperSurf']
    , sliding=FINITE)
# IPS and blank top surface         
mdb.models[mdlName].SurfaceToSurfaceContactExp(clearanceRegion=None, 
    createStepName='Forming', datumAxis=None, initialClearance=OMIT, 
    interactionProperty='ToolBlankInteractProps', mechanicalConstraint=KINEMATIC, main=mdb.models[mdlName].rootAssembly.instances['IPS-1'].surfaces['Srfc'],
	name='IPS_Blank_Int', secondary=mdb.models[mdlName].rootAssembly.instances['Blank-1'].surfaces['UpperSurf'],
	sliding=FINITE)    
# DCP and Spacer      
mdb.models[mdlName].SurfaceToSurfaceContactExp(clearanceRegion=None, 
    createStepName='Forming', datumAxis=None, initialClearance=OMIT, 
    interactionProperty='ToolToolInteractProps', main=
    mdb.models[mdlName].rootAssembly.instances['DCP-1'].surfaces['Srfc']
    , mechanicalConstraint=PENALTY, name='DCP_Spacer_Int', secondary=
    mdb.models[mdlName].rootAssembly.instances['Spacer-1'].surfaces['Srfc']
    , sliding=FINITE)
# IPS and Spacer      
mdb.models[mdlName].SurfaceToSurfaceContactExp(clearanceRegion=None, 
    createStepName='Forming', datumAxis=None, initialClearance=OMIT, 
    interactionProperty='ToolToolInteractProps', main=
    mdb.models[mdlName].rootAssembly.instances['IPS-1'].surfaces['Srfc']
    , mechanicalConstraint=PENALTY, name='IPS_Spacer_Int', secondary=
    mdb.models[mdlName].rootAssembly.instances['Spacer-1'].surfaces['Srfc']
    , sliding=FINITE)    
# BDD and LP_BDD_RECTANGLE      
mdb.models[mdlName].SurfaceToSurfaceContactExp(clearanceRegion=None, 
    createStepName='Forming', datumAxis=None, initialClearance=OMIT, 
    interactionProperty='ToolToolInteractProps', main=
    mdb.models[mdlName].rootAssembly.instances['BDD-1'].surfaces['Srfc']
    , mechanicalConstraint=PENALTY, name='BDD_LP_BDD_Rectangle_Int', secondary=
    mdb.models[mdlName].rootAssembly.instances['LP_BDD_RECTANGLE-1'].surfaces['Srfc']
    , sliding=FINITE)    
# LP and LP_BDD_RECTANGLE      
mdb.models[mdlName].SurfaceToSurfaceContactExp(clearanceRegion=None, 
    createStepName='Forming', datumAxis=None, initialClearance=OMIT, 
    interactionProperty='ToolToolInteractProps', main=
    mdb.models[mdlName].rootAssembly.instances['LP-1'].surfaces['Srfc']
    , mechanicalConstraint=PENALTY, name='LP_LP_BDD_Rectangle_Int', secondary=
    mdb.models[mdlName].rootAssembly.instances['LP_BDD_RECTANGLE-1'].surfaces['Srfc']
    , sliding=FINITE)    
    
# DCR and blank bottom surface         
mdb.models[mdlName].SurfaceToSurfaceContactExp(clearanceRegion=None, 
    createStepName='Forming', datumAxis=None, initialClearance=OMIT, 
    interactionProperty='ToolBlankInteractProps', main=
    mdb.models[mdlName].rootAssembly.instances['DCR-1'].surfaces['Srfc']
    , mechanicalConstraint=KINEMATIC, name='DCR_Blank_Int', secondary=
    mdb.models[mdlName].rootAssembly.instances['Blank-1'].surfaces['LowerSurf']
    , sliding=FINITE)

# LP and blank bottom surface         
mdb.models[mdlName].SurfaceToSurfaceContactExp(clearanceRegion=None, 
    createStepName='Forming', datumAxis=None, initialClearance=OMIT, 
    interactionProperty='ToolBlankInteractProps', main=
    mdb.models[mdlName].rootAssembly.instances['LP-1'].surfaces['Srfc']
    , mechanicalConstraint=KINEMATIC, name='LP_Blank_Int', secondary=
    mdb.models[mdlName].rootAssembly.instances['Blank-1'].surfaces['LowerSurf']
    , sliding=FINITE)
# PP and blank bottom surface         
mdb.models[mdlName].SurfaceToSurfaceContactExp(clearanceRegion=None, 
    createStepName='Forming', datumAxis=None, initialClearance=OMIT, 
    interactionProperty='ToolBlankInteractProps', main=
    mdb.models[mdlName].rootAssembly.instances['PP-1'].surfaces['Srfc']
    , mechanicalConstraint=KINEMATIC, name='PP_Blank_Int', secondary=
    mdb.models[mdlName].rootAssembly.instances['Blank-1'].surfaces['LowerSurf']
    , sliding=FINITE)
# UP and blank top surface         
mdb.models[mdlName].SurfaceToSurfaceContactExp(clearanceRegion=None, 
    createStepName='Forming', datumAxis=None, initialClearance=OMIT, 
    interactionProperty='ToolBlankInteractProps', main=
    mdb.models[mdlName].rootAssembly.instances['UP-1'].surfaces['Srfc']
    , mechanicalConstraint=KINEMATIC, name='UP_Blank_Int', secondary=
    mdb.models[mdlName].rootAssembly.instances['Blank-1'].surfaces['UpperSurf']
    , sliding=FINITE)    
## AMPLITUDE
mdb.models[mdlName].TabularAmplitude(data=((0.0, velocity_init), (
    time_travel, 0.0), (2.0*time_travel, 0.0)), name='PistonMotion', smooth=
    SOLVER_DEFAULT, timeSpan=STEP)
mdb.models[mdlName].TabularAmplitude(data=((0.0, velocity_init), (
    time_travel, 0.0), (2.0*time_travel, -1.0*velocity_init)), name='SlideMotion', 
    smooth=SOLVER_DEFAULT, timeSpan=STEP)
# Boundary Conditions for Forming step
mdb.models[mdlName].VelocityBC(amplitude='SlideMotion', 
    createStepName='Forming', distributionType=UNIFORM, fieldName='', 
    localCsys=None, name='BDD_Motion', region=
    mdb.models[mdlName].rootAssembly.instances['BDD-1'].sets['RefPt'], 
    v1=0.0, v2=-1.0, vr3=0.0)
mdb.models[mdlName].VelocityBC(amplitude='SlideMotion', 
    createStepName='Forming', distributionType=UNIFORM, fieldName='', 
    localCsys=None, name='DCP_Motion', region=
    mdb.models[mdlName].rootAssembly.instances['DCP-1'].sets['RefPt'], 
    v1=0.0, v2=-1.0, vr3=0.0)
mdb.models[mdlName].VelocityBC(amplitude='SlideMotion', 
    createStepName='Forming', distributionType=UNIFORM, fieldName='', 
    localCsys=None, name='Spacer_Motion', region=
    mdb.models[mdlName].rootAssembly.instances['Spacer-1'].sets['RefPt'], 
    v1=0.0, v2=-1.0, vr3=0.0)    
mdb.models[mdlName].VelocityBC(amplitude=UNSET, createStepName=
    'Forming', distributionType=UNIFORM, fieldName='', localCsys=None, name=
    'IPS_ConstrainedMotion', region=
    mdb.models[mdlName].rootAssembly.instances['IPS-1'].sets['RefPt'], 
    v1=0.0, v2=UNSET, vr3=0.0)
mdb.models[mdlName].VelocityBC(amplitude='PistonMotion', 
    createStepName='Forming', distributionType=UNIFORM, fieldName='', 
    localCsys=None, name='IPS_PistonMotion', region=
    mdb.models[mdlName].rootAssembly.sets['Spring_IPS_Pt'], v1=0.0, 
    v2=-1.0, vr3=0.0)
mdb.models[mdlName].VelocityBC(amplitude=UNSET, createStepName=
    'Forming', distributionType=UNIFORM, fieldName='', localCsys=None, name=
    'LP_ConstraineMotion', region=
    mdb.models[mdlName].rootAssembly.instances['LP-1'].sets['RefPt'], 
    v1=0.0, v2=UNSET, vr3=0.0)
mdb.models[mdlName].VelocityBC(amplitude=UNSET, createStepName=
    'Forming', distributionType=UNIFORM, fieldName='', localCsys=None, name=
    'LP_BDD_RECTANGLE_ConstraineMotion', region=
    mdb.models[mdlName].rootAssembly.instances['LP_BDD_RECTANGLE-1'].sets['RefPt'], 
    v1=0.0, v2=UNSET, vr3=0.0)    
mdb.models[mdlName].VelocityBC(amplitude=UNSET, createStepName=
    'Forming', distributionType=UNIFORM, fieldName='', localCsys=None, name=
    'PP_ConstrainedMotion', region=
    mdb.models[mdlName].rootAssembly.instances['PP-1'].sets['RefPt'], 
    v1=0.0, v2=UNSET, vr3=0.0)
mdb.models[mdlName].VelocityBC(amplitude=UNSET, createStepName=
    'Forming', distributionType=UNIFORM, fieldName='', localCsys=None, name=
    'UP_ConstrainedMotion', region=
    mdb.models[mdlName].rootAssembly.instances['UP-1'].sets['RefPt'], 
    v1=0.0, v2=UNSET, vr3=0.0)
mdb.models[mdlName].VelocityBC(amplitude='PistonMotion', 
    createStepName='Forming', distributionType=UNIFORM, fieldName='', 
    localCsys=None, name='UP_PistonMotion', region=
    mdb.models[mdlName].rootAssembly.sets['Spring_UP_Pt'], v1=0.0, v2=
    -1.0, vr3=0.0)
# Start - Modify input file for nonlinear spring
##
model = mdb.models[mdlName]
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
## Create nonlinear spring attached to IPS
kwds_IPS = """*Spring, elset=IPS_NonLinearSpring-spring, NONLINEAR
2
%f, -1.0
%f, -0.0001 
0.0, 0.0
*Element, type=SpringA, elset=IPS_NonLinearSpring-spring
3, IPS-1.%d, %d"""
#nset_ips_refpt=196
nset_ips_refpt=1
nset_ips_spring_refpt=1 # Need to keep track of order of reference points created in assembly
modelkwb.insert(position=line_num_endassembly-1, text=kwds_IPS % (-1.0*ips_force,-1.0*ips_force,nset_ips_refpt,nset_ips_spring_refpt))
## Create nonlinear spring attached to UP 
kwds_UP = """*Spring, elset=UP_NonLinearSpring-spring, NONLINEAR
2
%f, -1.0
%f, -0.0001
0.0, 0.0
*Element, type=SpringA, elset=UP_NonLinearSpring-spring
4, UP-1.%d, %d"""
nset_UP_refpt=1 # the only reference point created in part UP (analytical rigid)
nset_UP_spring_refpt=2 # second reference point created in assembly
modelkwb.insert(position=line_num_endassembly-1, text=kwds_UP % (-1.0*up_force,-1.0*up_force,nset_UP_refpt,nset_UP_spring_refpt))
## Create nonlinear spring attached to LP 
kwds_LP = """*Spring, elset=LP_NonLinearSpring-spring, NONLINEAR
2
-286.3, -1.0
-286.3, -0.0001
0.0, 0.0
*Element, type=SpringA, elset=LP_NonLinearSpring-spring
5, LP-1.%d, %d"""
#nset_LP_refpt=266
nset_LP_refpt=1
nset_LP_spring_refpt=3 # third reference point created in assembly
modelkwb.insert(position=line_num_endassembly-1, text=kwds_LP % (nset_LP_refpt,nset_LP_spring_refpt))
## Create nonlinear spring attached to PP
kwds_PP = """*Spring, elset=PP_NonLinearSpring-spring, NONLINEAR
2
-1085.7, -1.0
-1085.7, -0.0001
0.0, 0.0
*Element, type=SpringA, elset=PP_NonLinearSpring-spring
6, PP-1.%d, %d"""
nset_PP_refpt=1 # the only reference point created in part PP (analytical rigid)
nset_PP_spring_refpt=4 # fourth reference point created in assembly
modelkwb.insert(position=line_num_endassembly-1, text=kwds_PP % (nset_PP_refpt,nset_PP_spring_refpt))
##
# End - Modify input file for nonlinear spring    
# Job creation
mdb.Job(activateLoadBalancing=False, atTime=None, contactPrint=OFF, 
    description='', echoPrint=OFF, explicitPrecision=DOUBLE, historyPrint=OFF, 
    memory=90, memoryUnits=PERCENTAGE, model=mdlName, modelPrint=OFF, 
    multiprocessingMode=DEFAULT, name='FormingJob', nodalOutputPrecision=FULL, 
    numCpus=1, numDomains=1, parallelizationMethodExplicit=DOMAIN, queue=None, 
    resultsFormat=ODB, scratch='', type=ANALYSIS, userSubroutine='', waitHours=
    0, waitMinutes=0)
mdb.jobs['FormingJob'].writeInput(consistencyChecking=OFF)
    
