import dicom
from dicom.valuerep  import DSfloat
from pylab import plot
import json
from mpl_toolkits.mplot3d.axes3d import Axes3D
import matplotlib.pyplot as plt
import pprint

import numpy as np
from matplotlib import cm
from mpl_toolkits.mplot3d.axes3d import get_test_data

fig = plt.figure(figsize=plt.figaspect(0.5))
ax = fig.add_subplot(1,2,2, projection='3d')

Objects = {}

#dfile = dicom.read_file("data.dcm")
#dfileObjects = dfile.ROIContourSequence


#for dobject in dfileObjects:
#	Slices = []
#	for objectSlice in dobject.ContourSequence:
#		XPoints = []
#		YPoints = []
#		ZPoints = []
#		slicePoints = objectSlice.ContourData
#		for XPoint in slicePoints[0::3]:
#			XPoints.append(float(XPoint))#
#		for YPoint in slicePoints[1::3]:
#			YPoints.append(float(YPoint))
#		for ZPoint in slicePoints[2::3]:
#			ZPoints.append(float(ZPoint))
#		Points = []
#		for i in range(0, len(XPoints)):
#			Points.append({"x":XPoints[i], "y": YPoints[i], "z": ZPoints[i]})
#		ContourPoints = []
#		ContourPoints.append(Points)#
#		Slices.append(ContourPoints)
#	Objects.update({dobject.ReferencedROINumber: Slices})
pp = pprint.PrettyPrinter(indent=4)
#pp.pprint(Objects)
#json.dump(Objects, open("xyz.json", "wb"))

jsonD = []
with open ("xyz.json") as f:
	jsonD = json.load(f)

#pp.pprint(jsonD["13"])

verts = []
for cSlice in jsonD["11"]:
	vert = []
	for slicer in cSlice[0]:
		verts.append([int(slicer["x"]), int(slicer["y"]), int(slicer["z"])])
print verts

json.dump(verts, open('blender.json', 'wb'))
#	ax.plot_wireframe(cSlice["x"], cSlice["y"], cSlice["z"], rstride=10, cstride=10)
#plt.show()

