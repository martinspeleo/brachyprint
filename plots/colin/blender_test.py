import bpy
import json
from mathutils import Vector

w = 1
jsonD = []
with open("/Users/colinwren/Documents/Development/resources/scripts/brachyprint/plots/colin/blender.json") as f:
	jsonD = json.load(f)
	
verts = jsonD
cList = []
for d in jsonD:
	cList.append(Vector((d[0], d[1], d[2])))
	
curvedata = bpy.data.curves.new(name='Test', type="CURVE")
curvedata.dimensions = '3D'

obj = bpy.data.objects.new('Test',curvedata)
obj.location = (0,0,0)
bpy.context.scene.objects.link(obj)

polyline = curvedata.splines.new('NURBS')  
polyline.points.add(len(cList)-1)  
for num in range(len(cList)):  
    x, y, z = cList[num]  
    polyline.points[num].co = (x, y, z, w)
polyline.points.add(len(cList))
a,b,c = cList[0]
polyline.points[len(cList)].co = (a,b,c,w)
polyline.order_u = len(polyline.points)-1
polyline.use_endpoint_u = True

bpy.context.scene.update()