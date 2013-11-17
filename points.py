from __future__ import division
from os import listdir
from os.path import isfile, join
from subprocess import call
import dicom
import numpy

sampling = 2

mypath = "redfred"
myseries = "1.2.840.113704.1.111.3736.1370522307.4"
out = r"output/redfredc"
poissionrec = "PoissonRecon/Bin/Linux/PoissonRecon"

def makepoints(t, zpositions, posX, posY, spacingX, spacingY, level, extend):
    t = t.astype(numpy.int16)
    mean = (t[1:, 1:, 1:]  + t[1:, 1:, :-1]  + t[1:, :-1, 1:]  + t[1:,:-1,:-1] 
          + t[:-1, 1:, 1:] + t[:-1, 1:, :-1] + t[:-1, :-1, 1:] + t[:-1,:-1,:-1]) / 8
    gz =   (t[1:, 1:, 1:]  + t[1:, 1:, :-1]  + t[1:, :-1, 1:]  + t[1:,:-1,:-1] \
          - t[:-1, 1:, 1:] - t[:-1, 1:, :-1] - t[:-1, :-1, 1:] - t[:-1,:-1,:-1]) / 4
    #print "gz", gz
    gy =   (t[1:, 1:, 1:]  + t[1:, 1:, :-1]  - t[1:, :-1, 1:]  - t[1:,:-1,:-1] \
          + t[:-1, 1:, 1:] + t[:-1, 1:, :-1] - t[:-1, :-1, 1:] - t[:-1,:-1,:-1]) / 4
    
    gx =   (t[1:, 1:, 1:]  - t[1:, 1:, :-1]  + t[1:, :-1, 1:]  - t[1:,:-1,:-1] \
          + t[:-1, 1:, 1:] - t[:-1, 1:, :-1] + t[:-1, :-1, 1:] - t[:-1,:-1,:-1]) / 4
    #print t[:2, :2, :2]
    #print mean[:1, :1, :1]
    #print "gx", gx[:1, :1, :1]
    #print "gy", gy[:1, :1, :1]
    #print "gz", gz.dtype

    del t
    gn = (gx ** 2 + gy ** 2 + gz ** 2) ** 0.5
    nx = gx / gn
    #print nx.dtype
    #print gx.dtype
    del gx
    ny = gy / gn
    del gy
    nz = gz / gn
    del gz
    dist = (mean - level) / gn
    del gn
    dx = dist * nx
    dy = dist * ny
    dz = dist * nz
    print dz.dtype
    del dist
    hit = numpy.logical_and(numpy.logical_and(abs(dx) < 0.5, abs(dy) < 0.5), abs(dz) < 0.5)
    results = []
    for i, j, k in zip(*hit.nonzero()):
        rx = nx[i, j, k] * spacingX
        ry = ny[i, j, k] * spacingY
        rz = nz[i, j, k] * (zpositions[i+1] - zpositions[i])
        rn = (rx ** 2 + ry ** 2 + rz ** 2) ** 0.5
        rx = -rx / rn
        ry = -ry / rn
        rz = -rz / rn
        results.append((posX + (k + 0.5 - dx[i, j, k]) * spacingX + rx * extend,
                                     posY + (j + 0.5 - dy[i, j, k]) * spacingY + ry * extend,
                                     zpositions[i] * (0.5 + dz[i, j, k]) + zpositions[i+1] * (0.5 - dz[i, j, k]) + rz * extend,
                                     rx,
                                     ry,
                                     rz))
    del dx
    del dy
    del dz
    del nx
    del ny
    del nz
    return results

def points_to_string(points):
    r = ""
    for point in points:
        r = r + "%f %f %f %f %f %f\n" % point
    return r

def load(mypath, myseries, level, extend):
    dicomfiles = [ dicom.read_file(join(mypath,f)) for f in listdir(mypath) if isfile(join(mypath,f)) ]
    mySlices = []
    for d in dicomfiles:
        try:
            if d.SeriesInstanceUID == myseries:
                mySlices.append(d)
        except:
            None
    del dicomfiles
    def cmpZ(x, y):
        return cmp(x.ImagePositionPatient[2], y.ImagePositionPatient[2])
    mySlices.sort(cmpZ)
    mySlices = mySlices[::sampling]
    d=[]
    for s in mySlices:
        a = numpy.fromstring(s.PixelData, dtype=numpy.uint16)
        a.resize(s.Rows, s.Columns)
        d.append(a[::sampling, ::sampling])
    zpositions = [s.ImagePositionPatient[2] for s in mySlices]
    exampleSlice = mySlices[0]
    del mySlices
    t = numpy.array(d)
    del d
    return makepoints(t, 
                      zpositions, 
                      exampleSlice.ImagePositionPatient[0], 
                      exampleSlice.ImagePositionPatient[1],
                      exampleSlice.PixelSpacing[0] * sampling,
                      exampleSlice.PixelSpacing[1] * sampling,
                      level, extend)

def save(points, outfile):
    f = open(outfile, "w")
    f.write(points_to_string(points))
    f.close()

def poission(infile, outfile):
    call([poissionrec, "--in", infile, "--out", outfile])

def load_save_poission(mypath, myseries, out, level, extend):
    points = load(mypath, myseries, level, extend)
    pointsfile = out + str(level) + ".plt"
    save(points, pointsfile)
    meshfile = out + str(level) + ".ply"
    poission(pointsfile, meshfile)

if __name__ == '__main__':
    #load(mypath, myseries, out, 500, 0)
    load_save_poission(mypath, myseries, out, 500, 0)
    #load(mypath, myseries, out, 1200, 0)

