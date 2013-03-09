from kivy.graphics import Fbo, ClearColor, ClearBuffers, \
        Canvas, RenderContext, BindTexture, Callback, \
        Mesh, Rectangle, Color
from kivy.graphics.opengl import glEnable, glDisable, \
        GL_DEPTH_TEST, GL_CULL_FACE
from kivy.uix.screenmanager import TransitionBase
from kivy.graphics.transformation import Matrix
from kivy.properties import NumericProperty
from kivy.animation import AnimationTransition
from math import cos, sin, pi
from os.path import join, dirname

DEBUG = False
TILE = 20

def funcLinear(ft, f0, f1):
    return f0 + (f1 - f0) * ft

curdir = dirname(__file__)

class PageCurlTransition(TransitionBase):

    cy_x = NumericProperty(520.)
    cy_y = NumericProperty(0)
    cy_dir = NumericProperty(pi / 2.)
    cy_radius = NumericProperty(50.)

    def __init__(self, **kwargs):
        super(PageCurlTransition, self).__init__(**kwargs)
        self.fbo_in = None
        self.fbo_out = None

    def make_screen_fbo(self, screen, mode=None):
        assert(mode is not None)
        attr = 'fbo_'  + mode
        fbo = getattr(self, attr)

        w, h = screen.size
        w = (w - w % TILE) + TILE
        h = (h - h % TILE) + TILE
        size = w, h

        if not fbo:
            fbo = Fbo(size=size)
            setattr(self, attr, fbo)

        fbo.clear()
        with fbo:
            ClearColor(0, 0, 0, 1)
            ClearBuffers()

        fbo.add(screen.canvas)
        fbo.draw()
        return fbo

    def add_screen(self, screen):
        self.screen_in.pos = self.screen_out.pos
        self.screen_in.size = self.screen_out.size
        self.manager.real_remove_widget(self.screen_out)

        print '-----------'
        print 'add_screen', screen, screen.canvas
        print 'screen_in', self.screen_in, self.screen_in.parent
        print 'screen_out', self.screen_out, self.screen_out.parent
        print '-----------'
        self.fbo_in = self.make_screen_fbo(self.screen_in, mode='in')
        self.fbo_out = self.make_screen_fbo(self.screen_out, mode='out')
        self.manager.canvas.add(self.fbo_in)
        self.manager.canvas.add(self.fbo_out)

        if not hasattr(self, 'canvas'):
            self.create_canvas()

        self.manager.canvas.add(self.canvas)
        self.on_progress(0)

    def create_canvas(self):
        self.canvas = Canvas()
        self.c_front = RenderContext()
        self.c_front.shader.source = join(curdir, 'front.glsl')
        self.c_back = RenderContext()
        self.c_back.shader.source = join(curdir, 'back.glsl')
        self.c_backshadow = RenderContext()
        self.c_backshadow.shader.source = join(curdir, 'backshadow.glsl')
        self.canvas.add(self.c_front)
        self.canvas.add(self.c_back)
        self.canvas.add(self.c_backshadow)

        with self.canvas.before:
            Color(1, 1, 1)
            Rectangle(
                size=self.fbo_in.size,
                texture=self.fbo_in.texture)
            Callback(self._enter_3d)
        self._build_mesh(self.fbo_in.size)
        with self.canvas.after:
            Callback(self._leave_3d)

    def remove_screen(self, screen):
        self.manager.canvas.remove(self.fbo_in)
        self.manager.canvas.remove(self.fbo_out)
        self.manager.canvas.remove(self.canvas)
        self.manager.real_add_widget(self.screen_in)

    def on_progress(self, t):
        oquad = AnimationTransition.out_quad
        iquad = AnimationTransition.in_quad

        #t = t * 10 if t < .1 else 1
        #t = .7
        #t = AnimationTransition.out_quad(t)

        self.cy_x = funcLinear(AnimationTransition.in_out_cubic(t),
                self.screen_in.width, self.screen_in.width / 2. + 10)
        d = 0.7
        if t < d:
            self.cy_radius = funcLinear(oquad(t / d), 10., 50.)
            self.c_backshadow['opacity'] = 1
        else:
            t2 = (t - d) / (1. - d)
            self.cy_radius = funcLinear(iquad(t2), 50., 0.01)

        d = 0.9
        if t > d:
            t2 = (t - d) / (1. - d)
            self.c_backshadow['opacity'] = funcLinear(t2, 1., 0.)

        d1 = 0.3
        d2 = 0.5
        f1 = AnimationTransition.in_out_sine
        f2 = AnimationTransition.in_sine
        if t < d1:
            d = d1
            di = f1(t / d)
            self.cy_dir = pi / 2. - di / 2.
        elif t < d2:
            pass
        else:
            d = d2
            t2 = (t - d) / (1. - d)
            di = f2(1 - t2)
            self.cy_dir = pi / 2. - di / 2.

        self.update_glsl()
        return
        # old flip
        d = 0.8
        if t < d:
            dt = t / d
            self.cy_dir = funcLinear(AnimationTransition.out_circ(dt), 0, 1.55)
        else:
            self.cy_dir = 1.5
        self.cy_x = funcLinear(t, self.screen_in.width, -self.screen_in.width / 2.0)
        self.update_glsl()

    def update_glsl(self, *largs):
        size = self.manager.size
        proj = Matrix().view_clip(0, size[0], 0, size[1], -1000, 1000, 0)
        self.c_front['projection_mat'] = proj
        self.c_front['cylinder_position'] = map(float, (self.cy_x, self.cy_y))
        self.c_front['cylinder_direction'] = (cos(self.cy_dir), sin(self.cy_dir))
        self.c_front['cylinder_radius'] = float(self.cy_radius)
        self.c_front['texture1'] = 1

        for key in ('projection_mat', 'cylinder_position', 'cylinder_radius',
                'cylinder_direction', 'texture1'):
            self.c_back[key] = self.c_front[key]
            self.c_backshadow[key] = self.c_front[key]

    def _enter_3d(self, *args):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)

    def _leave_3d(self, *args):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)

    def _build_mesh(self, size):
        m = TILE
        width, height = map(int, size)
        step_width = int(width / (width / m))
        step_height = int(height / (height / m))
        vertices = []
        indices = []
        indices_back = []
        fw = float(width)
        fh = float(height)

        # create all the vertices
        for y in xrange(0, height + step_height, step_height):
            for x in xrange(0, width + step_width, step_width):
                vertices += [x, y, 0, x / fw, y / fh]

        # trace a triangles mesh
        mx = 1 + width / step_width
        my = 1 + height / step_height

        self.vertex_format = [
            ('vPosition', 3, 'float'),
            ('vTexCoords0', 2, 'float')]

        mode = 'line_loop' if DEBUG else 'triangles'
        for x in xrange(mx - 1):
            for y in xrange(my - 1):
                i = y * mx + x
                indices += [i, i + 1, i + 1 + mx,
                            i, i + 1 + mx, i + mx]
                indices_back += [i, i + 1 + mx, i + 1,
                            i, i + mx, i + 1 + mx]

        fbo_out_texture = None if DEBUG else self.fbo_out.texture
        fbo_in_texture = None if DEBUG else self.fbo_in.texture
        self.g_mesh = Mesh(vertices=vertices, indices=indices,
                mode=mode, texture=fbo_out_texture, fmt=self.vertex_format)
        self.g_mesh_back = Mesh(vertices=vertices, indices=indices_back,
                mode=mode, texture=fbo_in_texture, fmt=self.vertex_format)
        self.o_vertices = vertices

        self.c_front.add(BindTexture(source=join(curdir, 'frontshadow.png'), index=1))
        self.c_front.add(self.g_mesh)
        self.c_backshadow.add(Rectangle(size=size))
        self.c_back.add(BindTexture(source=join(curdir, 'backshadow.png'), index=1))
        self.c_back.add(self.g_mesh_back)

if __name__ == '__main__':
    from kivy.uix.screenmanager import Screen, ScreenManager
    from kivy.lang import Builder
    from kivy.app import App
    from kivy.properties import StringProperty

    Builder.load_string('''
<ImageScreen>:
    Scatter:
        id: sc
        Image:
            size: sc.size
            mipmap: True
            source: root.source
            Button:
                on_press: app.root.current = app.root.next()
    ''')
    class ImageScreen(Screen):
        source = StringProperty()

    class TestApp(App):
        def build(self):
            root = ScreenManager(transition=PageCurlTransition(
                duration=2.0),
                #);dict(
                size_hint=(0.5, 0.5),
                pos_hint={'center_x': 0.5, 'center_y': 0.5})
            root.add_widget(ImageScreen(name='hello', source='pic1.jpg'))
            root.add_widget(ImageScreen(name='hello2', source='pic2.jpg'))
            return root

    TestApp().run()


