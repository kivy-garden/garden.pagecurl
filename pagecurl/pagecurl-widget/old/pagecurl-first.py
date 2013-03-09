from kivy.app import App
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.core.image import Image as CoreImage
from kivy.graphics import Mesh, Color
from math import sqrt, sin, cos, asin
from kivy.lang import Builder

DEBUG = False

Builder.load_string('''
#:import Animation kivy.animation.Animation
<Controls>:
    GridLayout:
        size_hint_y: None
        height: 90
        cols: 1

        canvas.before:
            Color:
                rgba: 0, 0, 0, .8
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: 'rho: {:.02f} - theta = {:.02f} - alpha = {:.02f}'.format(app.page.rho, app.page.theta, app.page.alpha)
        GridLayout:
            rows: 1
            Slider:
                on_value: app.page.theta = self.value
                max: 3.14
            Slider:
                on_value: app.page.alpha = -self.value
                max: 1000.0
                min: 1.0
            Slider:
                on_value: app.page.rho = -self.value
                max: 3.14
            Button:
                text: 'start'
                on_press: app.page.theta = 1.57; Animation(theta=0.01, t='out_circ').start(app.page)

        Slider:
            max: 1.0
            on_value: app.page.theta = 0.01 + 1.57 * (1 - self.value)
''')

class PageCurl(Widget):
    source = StringProperty()
    theta = NumericProperty(90.)
    alpha = NumericProperty(-700)
    rho = NumericProperty(0.)

    def __init__(self, **kwargs):
        super(PageCurl, self).__init__(**kwargs)
        self.texture = CoreImage(self.source).texture
        self.bind(theta=self.deform, alpha=self.deform, rho=self.deform)

    def on_size(self, instance, size):
        self.canvas.clear()
        with self.canvas:
            Color(1, 1, 1)
            self.build_mesh()

        self.deform()

    def build_mesh(self):
        m = 100
        width = self.width
        height = self.height
        step_width = width / (width / m)
        step_height = height / (height / m)
        vertices = []
        indices = []
        indices_debug = []
        fw = float(width)
        fh = float(height)

        # create all the vertices
        for y in xrange(0, self.height + step_height, step_height):
            for x in xrange(0, self.width + step_width, step_width):
                vertices += [x, y, x / fw, 1. - y / fh]

        # trace a strip mesh
        mx = 1 + self.width / step_width
        my = 1 + self.height / step_height

        '''
        # strip mesh
        mode = 'triangle_strip'
        for y in xrange(my):
            for x in xrange(mx):
                i = y * mx + x
                indices += [i, i + mx]
            # fake indices to be able to strip the next row
            indices += [i + mx]
        '''

        if True:
            texture = self.texture
            mode = 'triangles'
            for x in xrange(mx - 1):
                for y in xrange(my - 1):
                    i = y * mx + x
                    indices += [i, i + 1, i + 1 + mx,
                                i, i + mx, i + 1 + mx]
                    if DEBUG:
                        indices_debug += [
                                i, i + 1,
                                i, i + mx,
                                i + 1, i + mx]

        else:
            texture = None
            mode = 'points'
            indices = range(mx * my)


        self.g_mesh = Mesh(vertices=vertices, indices=indices,
                mode=mode, texture=texture)
        if DEBUG:
            self.g_mesh2 = Mesh(vertices=vertices, indices=indices_debug,
                    mode='lines')
        self.o_vertices = vertices

    def deform(self, *args):
        theta = self.theta
        alpha = self.alpha
        rho = self.rho
        v = self.o_vertices
        vout = v[:]
        for i in xrange(0, len(v), 4):
            x = v[i]
            y = v[i + 1]
            R = sqrt(x * x + (y - alpha) ** 2)
            r = R * sin(theta)
            beta = asin(x / R) / sin(theta)

            x = r * sin(beta)
            y = R + alpha - r * (1 - cos(beta)) * sin(theta)
            z = r * (1 - cos(beta)) * cos(theta)
            vout[i] = x * cos(rho) - z * sin(rho)
            vout[i + 1] = y

        self.g_mesh.vertices = vout
        if DEBUG:
            self.g_mesh2.vertices = vout


class Controls(FloatLayout):
    pass

class PageCurlApp(App):
    def build(self):
        root = FloatLayout()
        self.page = PageCurl(source='Watermelon.512.jpg')
        root.add_widget(self.page)
        root.add_widget(Controls())
        return root

PageCurlApp().run()
