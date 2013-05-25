import pygtk
pygtk.require('2.0')
import gtk

from mpl_toolkits.mplot3d.axes3d import Axes3D
import matplotlib.pyplot as plt

import gtk
from matplotlib.backends.backend_gtk import FigureCanvasGTK as FigureCanvas
from matplotlib.figure import Figure
import time
import gobject

import dicom

class ContourDisplay:

    def __init__(self):
        # create a new window
        window = gtk.Window()
        window.set_default_size(400,300)
        window.set_title("DICOM contour display")

        # create a figure and plot
        self.figure = Figure(figsize=(5,4), dpi=72)
        self.subplot = self.figure.add_subplot(111, projection='3d')

        # Create the widget, a FigureCanvas containing our Figure
        canvas = FigureCanvas(self.figure)
        Axes3D.mouse_init(self.subplot)

        vbox = gtk.VBox(homogeneous=False, spacing=0)
        vbox.pack_start(canvas, expand=True, fill=True, padding=0)
        
        self.contourselect = gtk.SpinButton(gtk.Adjustment(value=0, lower=0, upper=13, step_incr=1, page_incr=1), digits=0)
        
        hbox = gtk.HBox(homogeneous=True, spacing=0)
        
        hbox.pack_start(gtk.Label("Contour to display:"))
        hbox.pack_start(self.contourselect)
        
        self.contourselect.connect("value-changed", lambda x: self.update_contour())
        
        vbox.pack_start(hbox, expand=False, fill=True, padding=0)
        
        window.add(vbox)

        self.subplot.plot([0], [0], '-')
        self.subplot.grid(True)
        self.subplot.set_xlabel('x')
        self.subplot.set_ylabel('y')

        self.figure.canvas.draw()

        # show everything
        window.show_all()
        
        window.connect("destroy", lambda x: gtk.main_quit())

    def load_file(self, fname):
        self.data = dicom.read_file(fname)
        
    def update_contour(self):
        self.subplot.clear()

        contour_num = int(self.contourselect.get_value())

        for d in self.data.ROIContours[contour_num].Contours:
            
            x = d.ContourData[0::3]
            y = d.ContourData[1::3]
            z = d.ContourData[2::3]

            self.subplot.plot_wireframe(x, y, z, rstride=10, cstride=10)


        self.figure.canvas.draw()

    def main(self):
        self.update_contour()
        gtk.main()

if __name__ == "__main__":
    viewer = ContourDisplay()
    viewer.load_file("scalp.dcm")
    viewer.main()
    
