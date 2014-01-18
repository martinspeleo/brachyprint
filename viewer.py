#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import wx
import sys
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import parseply, model

BLOCKSIZE = 100

def null():
    pass

class pickPixel:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __call__(self):
        gluPickMatrix(self.x, self.y, 1, 1, glGetIntegerv(GL_VIEWPORT))

def zerocmp(x, y):
    return cmp(x[0], y[0])

class MeshCanvas(glcanvas.GLCanvas):
    def __init__(self, parent, mesh, modePanel):
        self.mesh = mesh
        self.modePanel = modePanel
        self.mean_x = (self.mesh.maxX + self.mesh.minX) / 2
        self.mean_y = (self.mesh.maxY + self.mesh.minY) / 2
        self.mean_z = (self.mesh.maxZ + self.mesh.minZ) / 2
        range_x = self.mesh.maxX - self.mesh.minX
        range_y = self.mesh.maxY - self.mesh.minY
        range_z = self.mesh.maxZ - self.mesh.minZ
        self.range_max = (range_x ** 2 + range_y ** 2 + range_z ** 2) ** 0.5

        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.init = False
        # initial mouse position
        self.lastx = self.x = 0
        self.lasty = self.y = 0
        self.size = None
        self.scale = 0.5
        self.theta = 0
        self.phi = 0
        self.selection = None
        self.sphere_selection = None
        self.spheres = []
        self.extra_lists = []
        self.mainList = None
        self.mainNumNames = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)

    def OnEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def OnSize(self, event):
        self.setSize()
        event.Skip()

    def setSize(self, selector = null):
        size = self.size = self.GetClientSize()
        if self.GetContext():
            self.SetCurrent()
            if size.width > size.height:
                yscale = self.scale
                xscale = self.scale * size.width / size.height
            else:
                xscale = self.scale
                yscale = self.scale * size.height / size.width
            glViewport(0, 0, size.width, size.height)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            selector()
            glFrustum(-xscale * self.range_max, xscale * self.range_max, -yscale * self.range_max, 
                      yscale * self.range_max, 1.0 * self.range_max, 3.0 * self.range_max)
            glTranslatef(0, 0, - 2 * self.range_max)


    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.SetCurrent()
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnDraw()

    def OnMouseDown(self, evt):
        self.CaptureMouse()
        self.x, self.y = self.lastx, self.lasty = evt.GetPosition()
        mode = self.modePanel.GetMode()
        if mode == "Select":
            hits = self.hit(self.x, self.y, opengl_list(self.mainList), self.mainNumNames)
            if hits:
                self.mainListSelected(hits[0][2][0])
            self.Refresh(False)
        elif mode == "Rubber Band":
            hits = self.hit(self.x, self.y, opengl_lists(self.extra_lists), len(self.spheres))
            if hits:
                self.sphere_selection =  hits[0][2][0]
                
            else:
                self.sphere_selection = None           
                self.placeSphere()
            self.compile_band()
            self.Refresh(False)

    def compile_band(self):
        glNewList(self.extra_lists[0], GL_COMPILE)
        if len(self.spheres) > 0:
            for i, (sphere, nextsphere) in enumerate(zip(self.spheres, self.spheres[1:] + [self.spheres[0]])):
                glPushMatrix()
                glPushName(i)
                glTranslatef(sphere[0], sphere[1], sphere[2])
                glColor3f(0.2,1,0.2)
                glutSolidSphere(3, 10, 10)
                glutSolidCylinder(1.5, ((sphere[0] -nextsphere[0]) ** 2 + 
                                        (sphere[1] -nextsphere[1]) ** 2 + 
                                        (sphere[2] -nextsphere[2]) ** 2) ** 0.5, 10 ,1)
                glPopName()
                glPopMatrix()
        glEndList()
            
    def placeSphere(self, i = None):
        hits = self.hit(self.x, self.y, opengl_list(self.mainList), self.mainNumNames)
        if hits:
            x, y, z = gluUnProject(self.x, self.GetClientSize().height - self.y, hits[0][0])
            hits = self.hit(self.x, self.y, renderOneBlock(hits[0][2][0], self.vol), BLOCKSIZE)
            if i is None:
                self.spheres.append((x, y, z, hits[0][2][0]))
            else:
                self.spheres[i] = (x, y, z, hits[0][2][0])

    def hit(self, x, y, opengl, maxhits):
        glSelectBuffer(4 * maxhits)
        glRenderMode(GL_SELECT)
        self.setSize(pickPixel(x, self.GetClientSize().height - y)) #Set projection to single pixel
        self.setupScene()
        opengl()
        hits = glRenderMode(GL_RENDER)
        self.setSize() #Return projection to normal
        hits.sort(zerocmp)
        return hits
 
    def OnMouseUp(self, evt):
        mode = self.modePanel.GetMode()
        if mode == "Rubber Band" and self.sphere_selection is not None:
            self.placeSphere(int(self.sphere_selection))
            self.compile_band()
            self.Refresh(False)
            self.sphere_selection = None
        self.ReleaseMouse()
        self.Refresh(False)

    def OnMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            self.lastx, self.lasty = self.x, self.y
            self.x, self.y = evt.GetPosition()
            mode = self.modePanel.GetMode()
            if mode == "Rotate":
                self.theta += 0.1 * (self.y - self.lasty)
                self.phi += - 0.1 * (self.x - self.lastx)
            elif mode == "Zoom":
                self.scale = self.scale * 1.01 ** (self.y - self.lasty)
                self.setSize()
            if mode == "Rubber Band" and self.sphere_selection is not None:
                self.placeSphere(int(self.sphere_selection))
                self.compile_band()
            self.Refresh(False)


    def InitGL(self):
        # set viewing projection
        self.setSize()

        glutInit()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)

        glInitNames()
        self.mainList = glGenLists (1)
        self.mainListInitial()
        self.extra_lists = [glGenLists (1)]

    def mainListInitial(self):
        glNewList(self.mainList, GL_COMPILE)
        named_volumes = self.mesh.volumes.items()
        glColor3f(1.0,0.8, 0.8)
        for name, vol in named_volumes:
            glPushName(name)
            glBegin(GL_TRIANGLES)
            for f in vol:
                assert len(f.vertices) == 3
                for v in f.vertices:
                    n = v.normal()
                    glNormal3f(n.x, n.y, n.z)
                    glVertex(v.x, v.y, v.z)
            glEnd()
            glPopName()
        glEndList()     
        self.mainNumNames = len(named_volumes)  

    def mainListSelected(self, volume_name):
        self.vol = self.mesh.volumes[volume_name]
        glNewList(self.mainList, GL_COMPILE)
        glColor3f(1.0,0.8, 0.8)
        blocks = range(1 + len(self.vol) / BLOCKSIZE)
        for name, subvol in [(n, self.vol[n * BLOCKSIZE: (n+1) * BLOCKSIZE]) for n in blocks]:
            glPushName(name)
            glBegin(GL_TRIANGLES)
            for f in subvol:
                assert len(f.vertices) == 3
                for v in f.vertices:
                    n = v.normal()
                    glNormal3f(n.x, n.y, n.z)
                    glVertex(v.x, v.y, v.z)
            glEnd()
            glPopName()
        glEndList()   
        self.mainNumNames = len(blocks)

    def OnDraw(self):
        # clear color and depth buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.setupScene()
        glCallList(self.mainList)
        glMatrixMode(GL_MODELVIEW)
        for list_ in self.extra_lists:
            glCallList(list_)
        self.SwapBuffers()

    def setupScene(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glRotatef(self.theta, 1.0, 0.0, 0.0)
        glRotatef(self.phi, 0.0, 1.0, 0.0)
        glTranslatef(-self.mean_x, -self.mean_y, -self.mean_z)

class opengl_lists:
    def __init__(self, lists):
        self.lists = lists
    def __call__(self):
        for l in self.lists:
            glCallList(l)

class opengl_list:
    def __init__(self, list_):
        self.list = list_
    def __call__(self):
        glCallList(self.list)

class renderOneBlock:
    def __init__(self, block_name, vol):
        self.block_name = block_name
        self.vol = vol
    def __call__(self):
        for f in self.vol[self.block_name * BLOCKSIZE: (self.block_name+1) * BLOCKSIZE]:
            glPushName(f.name)
            glBegin(GL_TRIANGLES)
            assert len(f.vertices) == 3
            for v in f.vertices:
                n = v.normal()
                glNormal3f(n.x, n.y, n.z)
                glVertex(v.x, v.y, v.z)
            glEnd()
            glPopName()

class ModePanel(wx.Panel):
           
    def __init__(self, *args, **kw):
        super(ModePanel, self).__init__(*args, **kw) 
        
        self.InitUI()
        
    def InitUI(self):   
        self.rb_rotate = wx.RadioButton(self, label='Rotate',  style=wx.RB_GROUP)
        self.rb_zoom = wx.RadioButton(self, label='Zoom')
        self.rb_select = wx.RadioButton(self, label='Select')
        self.rb_band = wx.RadioButton(self, label='Rubber Band')

        #self.rb_rotate.Bind(wx.EVT_RADIOBUTTON, self.SetMode)
        #self.rb_zoom.Bind(wx.EVT_RADIOBUTTON, self.SetMode)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.rb_rotate, 0.5, wx.EXPAND)
        box.Add(self.rb_zoom, 0.5, wx.EXPAND)
        box.Add(self.rb_select, 0.5, wx.EXPAND)
        box.Add(self.rb_band, 0.5, wx.EXPAND)
        self.SetAutoLayout(True)
        self.SetSizer(box)
        self.Layout()

    def GetMode(self):
        if self.rb_rotate.GetValue():  return "Rotate"
        if self.rb_zoom.GetValue(): return "Zoom"  
        if self.rb_select.GetValue(): return "Select"  
        if self.rb_band.GetValue(): return "Rubber Band"

class MainWindow(wx.Frame):
    def __init__(self, parent = None, id = -1, title = "PyOpenGL Example 1"):
        # Init
        wx.Frame.__init__(
                self, parent, id, title, size = (400,200),
                style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
        )

        # TextCtrl
        # self.control = wx.TextCtrl(self, -1, style = wx.TE_MULTILINE)
        
        #self.control = ConeCanvas(self)
        self.modePanel = ModePanel(self)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.modePanel, 0.5, wx.EXPAND)
        #box.Add(CubeCanvas(self), 1, wx.EXPAND)
        f = open("output/redfredc501.ply")
        d = parseply.parseply(f)
        f.close()
        tc = MeshCanvas(self, model.makeMesh(d), self.modePanel)
        box.Add(tc, 1, wx.EXPAND)

        self.SetAutoLayout(True)
        self.SetSizer(box)
        self.Layout()


        # StatusBar
        #self.CreateStatusBar()

        # Filemenu
        filemenu = wx.Menu()

        # Filemenu - About
        menuitem = filemenu.Append(-1, "&About", "Information about this program")
        self.Bind(wx.EVT_MENU, self.OnAbout, menuitem) # here comes the event-handler
        # Filemenu - Separator
        filemenu.AppendSeparator()

        # Filemenu - Exit
        menuitem = filemenu.Append(-1, "E&xit", "Terminate the program")
        self.Bind(wx.EVT_MENU, self.OnExit, menuitem) # here comes the event-handler

        # Menubar
        menubar = wx.MenuBar()
        menubar.Append(filemenu,"&File")
        self.SetMenuBar(menubar)

        # Show
        self.Show(True)

    def OnAbout(self,event):
        message = "Using PyOpenGL in wxPython"
        caption = "About PyOpenGL Example"
        wx.MessageBox(message, caption, wx.OK)

    def OnExit(self,event):
        self.Close(True)  # Close the frame.

app = wx.PySimpleApp()
frame = MainWindow()
app.MainLoop()

# destroying the objects, so that this script works more than once in IDLEdieses Beispiel
del frame
del app

