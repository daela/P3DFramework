
from __future__ import print_function

import math
from os.path import isfile
import sys


# Change the path to your render pipeline installation here
sys.path.insert(0, "../RenderPipeline")


from panda3d.core import loadPrcFile, Vec3, Shader, RenderModeAttrib, SamplerState
from panda3d.core import Texture, ShaderAttrib, NodePath, load_prc_file_data

from direct.showbase.ShowBase import ShowBase
from Core.RSCoreModules import TerrainMeshRenderer

from __init__ import RenderPipeline
from Code.Util.MovementController import MovementController

class App(ShowBase):

    def __init__(self):
        """ Inits the showbase """

        # Load options
        load_prc_file_data("", """
        model-cache-dir
        fullscreen #f
        win-size 1600 900
        window-title Render Pipeline by tobspr 
        icon-filename Data/GUI/icon.ico
        """)

        # Load render pipeline
        self.render_pipeline = RenderPipeline(self)
        self.render_pipeline.create()
        self.render_pipeline.create_default_skybox()

        # Init movement controller
        self.controller = MovementController(self)
        self.controller.set_initial_position_hpr(
            Vec3(-987.129, -2763.58, 211.47), Vec3(5.21728, 7.84863, 0))
        self.controller.setup()

        # Hotkeys
        self.accept("r", self._reload_shader)

        self.addTask(self.update, "update")
        self.scene_wireframe = False

        self._init_terrain()
        self._reload_shader()

    def update(self, task):
        """ Main update task """
        self.terrain.update()
        self.terrain_shadow.update()
        return task.cont

    def _reload_shader(self):
        """ Reloads all terrain shaders """
        self.render_pipeline.reload_shaders()

        self.render_pipeline.set_effect(self.terrain.get_node(), "Effects/terrain.yaml", {
            "render_gbuffer": True,
            "render_shadows": False,

        })

        self.render_pipeline.set_effect(self.terrain_shadow.get_node(), "Effects/terrain_shadow.yaml", {
            "render_gbuffer": False,
            "render_shadows": True,
        }, 5000)


    def _init_terrain(self):
        """ Inits the terrain """

        layout = "Layout0"
        hmap = "Data/Terrain/" + layout + "/heightmap.png"

        bounds_file = "Data/Terrain/" + layout + "bounds.bin"

        if not isfile(bounds_file):
            print("Generating terrain bounds ..")
            TerrainMeshRenderer.generateBounds(hmap, "Data/Terrain/" + layout + "bounds.bin")

        terrainOffset = Vec3(-4096, -4096, 70.0)
        terrainScale = Vec3(1.0, 1.0, 700.0)

        self.terrain = TerrainMeshRenderer()
        self.terrain.set_heightfield_size(8192)
        self.terrain.set_culling_enabled(False)
        self.terrain.load_chunk_mesh("Core/Resources/Chunk32.bam")
        self.terrain.set_focus(base.cam, base.camLens)
        self.terrain.load_bounds(bounds_file)
        self.terrain.set_target_triangle_width(7.0)

        self.terrain.set_pos(terrainOffset)
        self.terrain.set_scale(terrainScale)

        self.terrain.create()

        node = self.terrain.get_node()
        node.reparentTo(render)

        self.terrain_shadow = TerrainMeshRenderer()
        self.terrain_shadow.set_heightfield_size(8192)
        self.terrain_shadow.load_chunk_mesh("Core/Resources/Chunk32.bam")
        self.terrain_shadow.set_focus(base.cam, base.camLens)
        self.terrain_shadow.set_target_triangle_width(7.0)
        self.terrain_shadow.load_bounds(bounds_file)
        self.terrain_shadow.set_pos(terrainOffset)
        self.terrain_shadow.set_scale(terrainScale)
        self.terrain_shadow.set_culling_enabled(False)
        self.terrain_shadow.create()

        nodeShadow = self.terrain_shadow.get_node()
        nodeShadow.reparentTo(render)

        hmap = loader.loadTexture("Data/Terrain/" + layout + "/heightmap.png")
        hmap.set_wrap_u(Texture.WM_clamp)
        hmap.set_wrap_v(Texture.WM_clamp)
        hmap.set_format(Texture.F_r16)
        node.set_shader_input("heightmap", hmap)
        nodeShadow.set_shader_input("heightmap", hmap)

        fmap = loader.loadTexture("Data/Terrain/" + layout + "/flowmap.png")
        fmap.set_wrap_u(Texture.WMClamp)
        fmap.set_wrap_v(Texture.WMClamp)
        node.set_shader_input("flowmap", fmap)

        for material in ['rock', 'grass', 'gravel', 'snow', 'moss']:
            for i in xrange(2):
                tex = loader.loadTexture("Data/Terrain/Materials/" + material + "_" + str(i+1) + ".png")
                tex.set_wrap_u(Texture.WM_repeat)
                tex.set_wrap_v(Texture.WM_repeat)
                tex.set_format(Texture.F_srgb_alpha)
                tex.set_minfilter(Texture.FT_linear_mipmap_linear)
                tex.set_magfilter(Texture.FT_linear)
                tex.set_anisotropic_degree(16)
                node.set_shader_input(material + ("Diffuse" if i == 0 else "Normal"), tex)

App().run()
