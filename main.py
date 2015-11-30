
from panda3d.core import loadPrcFile, Vec3, Shader, RenderModeAttrib, SamplerState
from panda3d.core import Texture, ShaderAttrib, NodePath, loadPrcFileData

from direct.showbase.ShowBase import ShowBase
from Core.RSCoreModules import TerrainMeshRenderer

import math

import sys
sys.path.insert(0, "../RenderPipeline")

from __init__ import RenderPipeline
from Code.Util.MovementController import MovementController

class App(ShowBase):
    def __init__(self):

        loadPrcFileData("", "model-cache-dir")

        self.render_pipeline = RenderPipeline(self)
        self.render_pipeline.get_mount_manager().mount()
        self.render_pipeline.load_settings("Config/pipeline.yaml")
        self.render_pipeline.create()

        self.controller = MovementController(self)
        self.controller.set_initial_position_hpr(
            Vec3(-987.129, -2763.58, 211.47), Vec3(5.21728, 7.84863, 0))

        self.controller.setup()

        self.render_pipeline.create_default_skybox()

        self.accept("r", self._reload_shader)
        self.accept("f3", self._toggle_scene_wireframe)

        self.addTask(self.update, "update")

        self.scene_wireframe = False

        # Create some ocean
        # self.water = ProjectedWaterGrid(self.render_pipeline)
        # self.water.setWaterLevel(0)

        self._init_terrain()
        self._reload_shader()

    def update(self, task):
        self.terrain.update()
        self.terrainShadow.update()
        return task.cont

    def _reload_shader(self):
        self.render_pipeline.reload_shaders()

        self.render_pipeline.set_effect(self.terrain.getNode(), "Data/Effects/terrain.yaml", {
            "render_gbuffer": True,
            "render_shadows": False,

        })

        self.render_pipeline.set_effect(self.terrainShadow.getNode(), "Data/Effects/terrain_shadow.yaml", {
            "render_gbuffer": False,
            "render_shadows": True,
        }, 5000)


    def _toggle_scene_wireframe(self):
        self.scene_wireframe = not self.scene_wireframe

        if self.scene_wireframe:
            render.setAttrib(RenderModeAttrib.make(RenderModeAttrib.MWireframe), 10)
        else:
            render.setAttrib(RenderModeAttrib.make(RenderModeAttrib.MFilled), 10)


    def _init_terrain(self):
        layout = "Layout0"
        hmap = "Data/Terrain/" + layout + "/heightmap.png"

        # TerrainMeshRenderer.generateBounds(hmap, "Data/Terrain/" + layout + "bounds.bin")
        # sys.exit(0)

        terrainOffset = Vec3(-4096, -4096, 70.0)
        terrainScale = Vec3(1.0, 1.0, 700.0)

        self.terrain = TerrainMeshRenderer()
        self.terrain.setHeightfieldSize(8192)
        self.terrain.setCullingEnabled(False)
        self.terrain.loadChunkMesh("Core/Resources/Chunk32.bam")
        self.terrain.setFocus(base.cam, base.camLens)
        self.terrain.loadBounds("Data/Terrain/" + layout + "bounds.bin")
        self.terrain.setTargetTriangleWidth(7.0)

        self.terrain.setPos(terrainOffset)
        self.terrain.setScale(terrainScale)

        self.terrain.create()

        node = self.terrain.getNode()
        node.reparentTo(render)

        self.terrainShadow = TerrainMeshRenderer()
        self.terrainShadow.setHeightfieldSize(8192)
        self.terrainShadow.loadChunkMesh("Core/Resources/Chunk32.bam")
        self.terrainShadow.setFocus(base.cam, base.camLens)
        self.terrainShadow.setTargetTriangleWidth(7.0)
        self.terrainShadow.loadBounds("Data/Terrain/" + layout + "bounds.bin")
        self.terrainShadow.setPos(terrainOffset)
        self.terrainShadow.setScale(terrainScale)
        self.terrainShadow.setCullingEnabled(False)
        self.terrainShadow.create()

        nodeShadow = self.terrainShadow.getNode()
        nodeShadow.reparentTo(render)



        hmap = loader.loadTexture("Data/Terrain/" + layout + "/heightmap.png")
        hmap.setWrapU(Texture.WMClamp)
        hmap.setWrapV(Texture.WMClamp)
        node.setShaderInput("heightmap", hmap)
        nodeShadow.setShaderInput("heightmap", hmap)

        fmap = loader.loadTexture("Data/Terrain/" + layout + "/flowmap.png")
        fmap.setWrapU(Texture.WMClamp)
        fmap.setWrapV(Texture.WMClamp)
        node.setShaderInput("flowmap", fmap)

        for material in ['rock', 'grass', 'gravel', 'snow', 'moss']:
            for i in xrange(2):
                tex = loader.loadTexture("Data/Terrain/Materials/" + material + "_" + str(i+1) + ".png")
                tex.setWrapU(Texture.WMRepeat)
                tex.setWrapV(Texture.WMRepeat)
                tex.setFormat(Texture.FSrgbAlpha)
                tex.setMinfilter(Texture.FTLinearMipmapLinear)
                tex.setMagfilter(Texture.FTLinear)
                tex.setAnisotropicDegree(16)
                node.setShaderInput(material + ("Diffuse" if i == 0 else "Normal"), tex)
    

        # self.water.model.setShaderInput("terrainHeightmap", hmap)
        # self.water.model.setShaderInput("terrainOffset", terrainOffset)
        # self.water.model.setShaderInput("terrainScale", terrainScale)

App().run()