'''
Page-curl widget
================

Reference: http://wdnuon.blogspot.fr/2010/05/implementing-ibooks-page-curling-using.html
'''

from kivy.app import App
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.core.image import Image as CoreImage
from kivy.graphics import Mesh, RenderContext, Callback, BindTexture, Color, Rectangle
from math import sin, cos, pi
from kivy.lang import Builder
from kivy.resources import resource_find
from kivy.graphics.opengl import glDisable, glEnable, GL_DEPTH_TEST, GL_CULL_FACE
from kivy.clock import Clock
from kivy.graphics.transformation import Matrix
from kivy.animation import AnimationTransition

DEBUG = False
RAD = 180. / pi

Builder.load_string('''
#:import Animation kivy.animation.Animation
<Controls>:
    GridLayout:
        size_hint_y: None
        pos_hint: {'top': 1.}
        height: 40
        cols: 1

        canvas.before:
            Color:
                rgba: 0, 0, 0, .8
            Rectangle:
                pos: self.pos
                size: self.size

        Slider:
            max: 1.0
            on_value: app.page.time = self.value

        GridLayout:
            rows: 1
            Slider:
                on_value: app.page.cy_x = self.value
                min: -1000.
                max: 1000.
            Slider:
                on_value: app.page.cy_y = self.value
                min: -1000.
                max: 1000.
            Slider:
                on_value: app.page.cy_dir = self.value
                max: 2 * 3.1416
            Slider:
                on_value: app.page.cy_radius = self.value
                max: 200.
''')

def funcLinear(ft, f0, f1):
    return f0 + (f1 - f0) * ft

class PageCurl(Widget):
    source = StringProperty()
    time = NumericProperty(1.)

    cy_x = NumericProperty(520.)
    cy_y = NumericProperty(-50)
    cy_dir = NumericProperty(0)
    cy_radius = NumericProperty(150.)

    def __init__(self, **kwargs):
        super(PageCurl, self).__init__(**kwargs)
        self.c_front = RenderContext()
        self.c_front.shader.source = resource_find('front.glsl')
        self.c_back = RenderContext()
        self.c_back.shader.source = resource_find('back.glsl')
        self.c_backshadow = RenderContext()
        self.c_backshadow.shader.source = resource_find('backshadow.glsl')

        self.canvas.add(self.c_front)
        self.canvas.add(self.c_back)
        self.canvas.add(self.c_backshadow)

        self.texture = CoreImage(self.source).texture
        Clock.schedule_interval(self.update_glsl, 1 / 60.)

    def on_size(self, instance, size):
        with self.canvas.before:
            Callback(self._enter_3d)
        self.build_mesh()
        with self.canvas.after:
            Callback(self._leave_3d)

    def update_glsl(self, *largs):
        proj = Matrix().view_clip(0, self.width, 0, self.height, -1000, 1000, 0)
        self.c_front['projection_mat'] = proj
        self.c_front['cylinder_position'] = map(float, (self.cy_x, self.cy_y))
        self.c_front['cylinder_direction'] = (cos(self.cy_dir), sin(self.cy_dir))
        self.c_front['cylinder_radius'] = float(self.cy_radius)

        for key in ('projection_mat', 'cylinder_position', 'cylinder_radius',
                'cylinder_direction'):
            self.c_back[key] = self.c_front[key]
            self.c_backshadow[key] = self.c_front[key]

        self.c_front['texture1'] = 1
        self.c_backshadow['texture1'] = 1
        self.c_back['texture1'] = 1

    def _enter_3d(self, *args):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)

    def _leave_3d(self, *args):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)

    def build_mesh(self):
        m = 20
        width = self.width
        height = self.height
        step_width = width / (width / m)
        step_height = height / (height / m)
        vertices = []
        indices = []
        indices_back = []
        fw = float(width)
        fh = float(height)

        # create all the vertices
        for y in xrange(0, self.height + step_height, step_height):
            for x in xrange(0, self.width + step_width, step_width):
                vertices += [x, y, 0, x / fw, 1. - y / fh]

        # trace a triangles mesh
        mx = 1 + self.width / step_width
        my = 1 + self.height / step_height

        texture = self.texture
        mode = 'triangles'
        if DEBUG:
            texture = None
            mode = 'points'
        self.vertex_format = [
            ('vPosition', 3, 'float'),
            ('vTexCoords0', 2, 'float')]

        for x in xrange(mx - 1):
            for y in xrange(my - 1):
                i = y * mx + x
                indices += [i, i + 1, i + 1 + mx,
                            i, i + 1 + mx, i + mx]
                indices_back += [i, i + 1 + mx, i + 1,
                            i, i + mx, i + 1 + mx]

        self.g_mesh = Mesh(vertices=vertices, indices=indices,
                mode=mode, texture=texture, fmt=self.vertex_format)
        self.g_mesh_back = Mesh(vertices=vertices, indices=indices_back,
                mode=mode, texture=texture, fmt=self.vertex_format)
        self.o_vertices = vertices

        self.c_front.add(BindTexture(source='frontshadow.png', index=1))
        self.c_front.add(self.g_mesh)
        self.c_backshadow.add(Rectangle(size=self.size))
        self.c_back.add(BindTexture(source='backshadow.png', index=1))
        self.c_back.add(self.g_mesh_back)

    def on_time(self, instance, t):
        t = self.time
        d = 0.8
        if t < d:
            dt = t / d
            self.cy_dir = funcLinear(AnimationTransition.out_circ(dt), 0, 1.55)
        else:
            self.cy_dir = 1.55

        self.cy_x = funcLinear(t, self.width, -self.width / 2.0)

class Controls(FloatLayout):
    pass

class PageCurlApp(App):
    def build(self):
        from kivy.uix.image import Image
        root = FloatLayout()
        root.add_widget(Image(source='pic2.jpg'))
        self.page = PageCurl(source='pic1.jpg')
        root.add_widget(self.page)
        root.add_widget(Controls())
        return root

PageCurlApp().run()
