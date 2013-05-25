import bpy
import json

jsonD = []
with open("/Users/colinwren/Documents/brachy/blender.json") as f:
	jsonD = json.load(f)
	
verts = jsonD
faces = []
edges = []
mesh = bpy.data.meshes.new('Test')
mesh.from_pydata(verts,edges,faces)

scene = bpy.context.scene

obj = bpy.data.objects.new('Test',mesh)
scene.objects.link(obj)
scene.update()