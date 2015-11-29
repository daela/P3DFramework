
from panda3d.core import loadPrcFile, Vec3, Shader, RenderModeAttrib, SamplerState
from panda3d.core import Texture, ShaderAttrib, NodePath, loadPrcFileData

from direct.showbase.ShowBase import ShowBase
# from TerrainNode import TerrainNode

from Core.RSCoreModules import TerrainMeshRenderer

import math

import sys
# sys.path.insert(0, "RenderPipeline")
from RenderPipeline.Code.RenderingPipeline import RenderingPipeline
from RenderPipeline.Code.DirectionalLight import DirectionalLight
from RenderPipeline.Code.MovementController import MovementController
from RenderPipeline.Code.Water.ProjectedWaterGrid import ProjectedWaterGrid
# from Code.MovementController import MovementController
# from Code.DirectionalLight import DirectionalLight
# from Code.Water.ProjectedWaterGrid import ProjectedWaterGrid

class App(ShowBase):
    def __init__(self):


        loadPrcFile("RenderPipeline/Config/configuration.prc")
        loadPrcFileData("", "model-cache-dir")

        self.renderPipeline = RenderingPipeline(self)
        self.renderPipeline.getMountManager().setBasePath("RenderPipeline/")
        # self.renderPipeline.get_mount_manager().mount()
        self.renderPipeline.loadSettings("RenderPipeline/Config/pipeline.ini")
        ShowBase.__init__(self)
        self.renderPipeline.create()


        self._create_lights()
        self.controller = MovementController(self)
        self.controller.setInitialPositionHpr(
            Vec3(-987.129, -2763.58, 211.47), Vec3(5.21728, 7.84863, 0))


        self.controller.setup()

        self.skybox = self.renderPipeline.getDefaultSkybox()
        self.skybox.reparentTo(render)


        self.accept("r", self._reload_shader)
        self.accept("f3", self._toggle_scene_wireframe)

        self.addTask(self.update, "update")

        self.scene_wireframe = False

        self.renderPipeline.onSceneInitialized()

        # Create some ocean
        self.water = ProjectedWaterGrid(self.renderPipeline)
        self.water.setWaterLevel(0)

        self._init_terrain()
        self._reload_shader()


        # Slider to move the sun
        if self.renderPipeline.settings.displayOnscreenDebugger:
            self.renderPipeline.guiManager.demoSlider.node[
                "command"] = self._set_sun_pos
            self.renderPipeline.guiManager.demoSlider.node[
                "value"] = 80

            self.lastSliderValue = 0.0

    def _set_sun_pos(self):
        """ Sets the sun position based on the debug slider """

        radial = True
        rawValue = self.renderPipeline.guiManager.demoSlider.node["value"]
        diff = self.lastSliderValue - rawValue
        self.lastSliderValue = rawValue

        if radial:
            rawValue = rawValue / 100.0 * 2.0 * math.pi
            dPos = Vec3(
                math.sin(rawValue) * 30.0, math.cos(rawValue) * 30.0,  6.0)
            dPos = Vec3(100, 100, self.lastSliderValue - 20)
        else:
            dPos = Vec3(30, (rawValue - 50) * 1.5, 0)

        # dPos = Vec3(-2, 0, 40)

        if abs(diff) > 0.0001:
            if hasattr(self, "dirLight"):
                self.dirLight.setPos(dPos * 100000000.0)



    def _create_lights(self):

        dirLight = DirectionalLight()
        dirLight.setShadowMapResolution(1024)
        dirLight.setColor(Vec3(1, 1, 0.8) * 1.5)
        dirLight.setPssmDistance(2048)
        # dirLight.setSunDistance(12000 * 5)
        dirLight.setPssmTarget(self.cam, self.camLens)
        dirLight.setCastsShadows(True)
        self.renderPipeline.addLight(dirLight)
        self.dirLight = dirLight
        sunPos = Vec3(56.7587, -31.3601, 189.196)
        self.dirLight.setPos(sunPos * 1000000.0)

        # Tell the GI which light casts the GI
        # self.renderPipeline.setGILightSource(dirLight)
        self.renderPipeline.setScatteringSource(dirLight)

    def update(self, task):
        self.terrain.update()
        self.terrainShadow.update()

        return task.cont

    def _reload_shader(self):
        # self._compute_snowmap()
        self.renderPipeline.reloadShaders()

        # terrain_shader = Shader.load(Shader.SLGLSL, "Data/Shader/Terrain/vertex.glsl", "Data/Shader/Terrain/fragment.glsl", "", "Data/Shader/Terrain/tesscontrol.glsl", "Data/Shader/Terrain/tesseval.glsl")
        # self.terrain.getLODNode(0).setShader(terrain_shader, 100)
        # self.terrain.getLODNode(1).setShader(terrain_shader, 100)
        # self.terrain.getLODNode(2).setShader(terrain_shader, 100)

    def _toggle_scene_wireframe(self):
        self.scene_wireframe = not self.scene_wireframe

        if self.scene_wireframe:
            render.setAttrib(RenderModeAttrib.make(RenderModeAttrib.MWireframe), 10)
        else:
            render.setAttrib(RenderModeAttrib.make(RenderModeAttrib.MFilled), 10)

        self.skybox.setAttrib(RenderModeAttrib.make(RenderModeAttrib.MFilled), 20)


    def _init_terrain(self):
        layout = "Layout1"
        hmap = "Data/Terrain/" + layout + "/heightmap.png"

        # TerrainMeshRenderer.generateBounds(hmap, "Data/Terrain/" + layout + "bounds.bin")
        # sys.exit(0)

        terrainOffset = Vec3(-2048, -2048, 220.0)
        terrainScale = Vec3(1.0, 1.0, 700.0)

        self.terrain = TerrainMeshRenderer()
        self.terrain.setHeightfieldSize(4096)
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
        self.terrainShadow.setHeightfieldSize(4096)
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


        self.renderPipeline.setEffect(node, "Data/Effects/Terrain.effect", {
            "mainPass": True,
            "castShadows": False,
        })

        self.renderPipeline.setEffect(nodeShadow, "Data/Effects/TerrainShadow.effect", {
            "mainPass": False,
            "castShadows": True,
        }, 5000)



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
    

        self.water.model.setShaderInput("terrainHeightmap", hmap)
        self.water.model.setShaderInput("terrainOffset", terrainOffset)
        self.water.model.setShaderInput("terrainScale", terrainScale)




        # self.terrain_node = render.attach_new_node("Terrain")
        # self.terrain_bounds = self._load_terrain_bounds("Data/Terrain/" + layout + "/Bounds.bin")

        # hfield_size = 2048
        # self.terrain_height = 200.0 / 1024.0 * hfield_size

        # print "TERRAIN HEIGHT = ", self.terrain_height

        # self.snowmap = Texture("snowmap")
        # self.snowmap.setup2dTexture(hfield_size, hfield_size, Texture.TFloat, Texture.FRed)
        # self.snowmap.setWrapU(SamplerState.WMClamp)
        # self.snowmap.setWrapV(SamplerState.WMClamp)
        # self.snowmap.setMinfilter(SamplerState.FTLinear)
        # self.snowmap.setMagfilter(SamplerState.FTLinear)
        # self.snowmap.setAnisotropicDegree(16)

        # self.terrain = TerrainNode()
        # self.terrain.setHeightfieldSize(hfield_size)
        # self.terrain.setPosition(Vec3(-hfield_size*0.5, -hfield_size*0.5, 0))
        # self.terrain.setCullingEnabled(False)

        # # self.terrain.setChunkBounds(0, self.terrain_height)
        # self.terrain.loadChunkBoundsFromString(self.terrain_bounds, 0, self.terrain_height)

        # self.terrain.setParent(self.terrain_node)
        # self.terrain.setChunkSize(32)

        # self.terrain.setTargetTriangleWidth(8.0)

        # self.terrain.setMaterials(['rock', 'grass', 'gravel', 'snow', 'moss'])
        # self.terrain.setCompiledMaterialPath("Data/Terrain/Materials/")

        # self.terrain.setHeightmap("Data/Terrain/" + layout + "/heightmap.png")
        # self.terrain.setBlurredHeightmap("Data/Terrain/" + layout + "/blurred_heightmap.png")
        # self.terrain.setFlowmap("Data/Terrain/" + layout + "/flowmap.png")
        # # self.terrain.setDetailmap("Data/Terrain/detail.png.txo")
        # self.terrain.setConvexitymap("Data/Terrain/" + layout + "/convexity.png")

        # self.terrain.getElement().setShaderInput("terrain_size", hfield_size)
        # self.terrain.getElement().setShaderInput("terrain_height", self.terrain_height)


        # mountain_tx = loader.loadTexture("Data/Terrain/mountain_color.png")
        # mountain_tx.setMinfilter(SamplerState.FTLinearMipmapLinear)
        # mountain_tx.setMagfilter(SamplerState.FTLinear)
        # mountain_tx.setWrapU(SamplerState.WMMirror)
        # mountain_tx.setWrapV(SamplerState.WMMirror)
        # mountain_tx.setFormat(Texture.FSrgb)

        # self.terrain.getElement().setShaderInput("mountainLayerTex", mountain_tx)
        # self.terrain.getElement().setShaderInput("snowmap", self.snowmap)

        # # self.terrain.getElement().hide(self.renderPipeline.getShadowPassBitmask())
        # # self.terrain.setBasecolormap("terrain/color.png")
        # self.terrain.initialize()


    def _compute_snowmap(self):
        
        tsize = self.snowmap.getXSize()
        shader = Shader.loadCompute(Shader.SLGLSL, "Data/Shader/Terrain/compute_snow.compute")

        dummy = NodePath("dummy")
        dummy.setShader(shader)
        dummy.setShaderInput("terrainHeight", self.terrain_height)
        dummy.setShaderInput("snowmapDest", self.snowmap)
        dummy.setShaderInput("heightmap", self.terrain.getHeightmap())
        dummy.setShaderInput("flowmap", self.terrain.getFlowmap())
        dummy.setShaderInput("convexmap", self.terrain.getConvexmap())

        sattr = dummy.get_attrib(ShaderAttrib)

        self.graphicsEngine.dispatch_compute((tsize / 16, tsize / 16, 1), sattr, self.win.get_gsg())



App().run()