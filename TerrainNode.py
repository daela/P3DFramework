



from panda3d.core import Texture, Vec2, Vec3, TexturePool, Filename, SamplerState
# from panda3d.core import 

import BrainzCore
import time


VERBOSE = False


class TerrainNode:

    mipmapMIN = SamplerState.FTLinearMipmapLinear
    mipmapMAG = SamplerState.FTLinear    
    anisotropicFactor = 16

    def __init__(self):

        if VERBOSE:
            print "Creating TerrainQuadtree"

        self._plane_quadtree   = BrainzCore.TerrainQuadtree()
        self._plane_quadtree.setScale(Vec2(1))
        self._plane_quadtree.setTesselationEnabled(True)

        self._initialized      = False
        self._parent           = None
        self._element_node     = None
        self.heightmap_tex    = None
        self.flowmap_tex      = None

        self.setMaterials([])
        self.setCompiledMaterialPath("")

        self.setHeightfieldSize(2048)
        self.setPosition(Vec3(0))
        self.setChunkBounds(0,100)
        self.setChunkSize(32)
        self.setTargetTriangleWidth(8.0)
        self.setDetailFactors(3,6)
        self.setCullingEnabled(True)

        try:
            self._focal_camera     = base.cam
            self._focal_lens       = base.camLens
        except Exception, msg:
            self._focal_camera     = None
            self._focal_lens       = None




    def setCullingEnabled(self, enabled):
        self._plane_quadtree.setCullingEnabled(enabled)


    def setPosition(self, pos):
        assert(not self._initialized)
        self._position = pos
        self._plane_quadtree.setPosition(self._position)

    def setHeightfieldSize(self, size):
        assert(not self._initialized)
        self._heightfield_size = size
        self._plane_quadtree.setHeightfieldSize(size)

        if VERBOSE:
            print "_heightfield_size =",self._heightfield_size

    def setMaterials(self, materials):
        assert(not self._initialized)
        self._materials = materials
        if VERBOSE:
            print "_materials =", materials

    def setCompiledMaterialPath(self, pt):
        assert(not self._initialized)
        self._material_path = pt

        if VERBOSE:
            print "_material_path=", pt

    def setChunkSize(self, size):
        assert(not self._initialized)
        self._chunk_size = size
        self._plane_quadtree.setChunkSize(self._chunk_size)

        if VERBOSE:
            print "_chunk_size =",self._chunk_size

    def setHeightmap(self, hmap_path):
        assert(self._parent)

        self.heightmap_tex = TexturePool.loadTexture(Filename.fromOsSpecific(hmap_path))
        # self.heightmap_tex = loader.loadTexture(hmap_path)

        self.heightmap_tex.setWrapU(SamplerState.WMClamp)
        self.heightmap_tex.setWrapV(SamplerState.WMClamp)
        self.heightmap_tex.setFormat(Texture.F_r16)
        self.heightmap_tex.setKeepRamImage(False)
        self.heightmap_tex.setMinfilter(SamplerState.FTLinearMipmapLinear)
        self.heightmap_tex.setMagfilter(SamplerState.FTLinear)
        self.heightmap_tex.setAnisotropicDegree(0)

        self._element_node.setShaderInput("heightmap", self.heightmap_tex)

    def setBlurredHeightmap(self, hmap_path):
        assert(self._parent)

        self.blurred_heightmap_tex = TexturePool.loadTexture(Filename.fromOsSpecific(hmap_path))
        self.blurred_heightmap_tex.setWrapU(SamplerState.WMClamp)
        self.blurred_heightmap_tex.setWrapV(SamplerState.WMClamp)
        self.blurred_heightmap_tex.setFormat(Texture.F_r16)
        self.blurred_heightmap_tex.setKeepRamImage(False)
        self.blurred_heightmap_tex.setMinfilter(SamplerState.FTLinearMipmapLinear)
        self.blurred_heightmap_tex.setMagfilter(SamplerState.FTLinear)
        self.blurred_heightmap_tex.setAnisotropicDegree(0)

        print "set blurred heightmap"
        self._element_node.setShaderInput("blurredHeightmap", self.blurred_heightmap_tex)

    def setDetailFactors(self, lowUntil, mediumUntil):
        assert(not self._initialized)
        self._plane_quadtree.setDetailFactors(lowUntil, mediumUntil)

    def getHeightmap(self):
        return self.heightmap_tex

    def getLODNode(self, lod):
        assert(lod >= 0 and lod < 3)

        if lod == 0:
            return self._plane_quadtree.get_low_detail_element()
        if lod == 1:
            return self._plane_quadtree.get_medium_detail_element()
        if lod == 2:
            return self._plane_quadtree.get_high_detail_element()

        return False

    def setFlowmap(self, fmap_path):
        assert(self._parent)

        self.flowmap_tex = loader.loadTexture(fmap_path)
        self.flowmap_tex.setWrapU(SamplerState.WMClamp)
        self.flowmap_tex.setWrapV(SamplerState.WMClamp)
        self.flowmap_tex.setKeepRamImage(False)
        self.flowmap_tex.setMinfilter(SamplerState.FTLinearMipmapLinear)
        self.flowmap_tex.setMagfilter(SamplerState.FTLinear)
        self.flowmap_tex.setAnisotropicDegree(2)

        self._element_node.setShaderInput("flowmap", self.flowmap_tex)

    def setSnowmap(self, smap_path):
        assert(self._parent)

        self.snowmap_tex = loader.loadTexture(smap_path)
        self.snowmap_tex.setWrapU(SamplerState.WMClamp)
        self.snowmap_tex.setWrapV(SamplerState.WMClamp)
        self.snowmap_tex.setKeepRamImage(False)
        self.snowmap_tex.setMinfilter(SamplerState.FTLinearMipmapLinear)
        self.snowmap_tex.setMagfilter(SamplerState.FTLinear)
        self.snowmap_tex.setAnisotropicDegree(2)

        self._element_node.setShaderInput("snowmap", self.snowmap_tex)

    def getFlowmap(self):
        return self.flowmap_tex

    def setDetailmap(self, dmap_path):
        assert(self._parent)

        self.detailmap_tex = loader.loadTexture(dmap_path)
        self.detailmap_tex.setWrapU(SamplerState.WMRepeat)
        self.detailmap_tex.setWrapV(SamplerState.WMRepeat)
        self.detailmap_tex.setKeepRamImage(False)
        self.detailmap_tex.setMinfilter(self.mipmapMIN)
        self.detailmap_tex.setMagfilter(self.mipmapMAG)
        self.detailmap_tex.setAnisotropicDegree(self.anisotropicFactor)

        self._element_node.setShaderInput("details", self.detailmap_tex)

    def setConvexitymap(self, cmap_path):
        assert(self._parent)

        self.convexmap_tex = loader.loadTexture(cmap_path)
        self.convexmap_tex.setWrapU(SamplerState.WMRepeat)
        self.convexmap_tex.setWrapV(SamplerState.WMRepeat)
        self.convexmap_tex.setKeepRamImage(False)
        self.convexmap_tex.setMinfilter(self.mipmapMIN)
        self.convexmap_tex.setMagfilter(self.mipmapMAG)
        self.convexmap_tex.setAnisotropicDegree(self.anisotropicFactor)

        self._element_node.setShaderInput("convexity", self.convexmap_tex)

    def getConvexmap(self):
        return self.convexmap_tex

    def setBasecolormap(self, cmap_path):
        assert(self._parent)

        self.basecolor_tex = loader.loadTexture(cmap_path)
        self.basecolor_tex.setWrapU(SamplerState.WMRepeat)
        self.basecolor_tex.setWrapV(SamplerState.WMRepeat)
        self.basecolor_tex.setKeepRamImage(False)
        self.basecolor_tex.setMinfilter(self.mipmapMIN)
        self.basecolor_tex.setMagfilter(self.mipmapMAG)
        self.basecolor_tex.setAnisotropicDegree(self.anisotropicFactor)

        self._element_node.setShaderInput("basecolor", self.basecolor_tex)

    def setChunkBounds(self, bottom, top):
        self._chunk_bounds = (bottom, top)
        self._plane_quadtree.setStaticBounds(*self._chunk_bounds)
        if VERBOSE:
            print "_chunk_bounds =",(self._chunk_bounds)

    def loadChunkBoundsFromFile(self, filename, bottom, top):
        try:
            handle = open(filename, "rb")
            content = handle.read()
            handle.close()
            
            self._plane_quadtree.setPrecomputedBounds(str(content), bottom, top)

            
        except Exception, msg:
            print "Could not open file:",msg
            return False


    def loadChunkBoundsFromString(self, data, bottom, top):        
        self._plane_quadtree.setPrecomputedBounds(str(data), bottom, top)



    def setTargetTriangleWidth(self, width):
        self._target_triangle_width = width
        self._plane_quadtree.setTargetTriangleWidth(width)

        if VERBOSE:
            print "_target_triangle_width =",self._target_triangle_width

    def setFocalCamera(self, cam):
        self._focal_camera = cam

    def setFocalLens(self, lens):
        self._focal_lens = lens

    def setParent(self, parent):
        assert(not self._initialized and self._parent is None and not parent.is_empty())
        self._parent = parent
        self._element_node = parent.attachNewNode("terrain_root")
        self._plane_quadtree.setParent(self._element_node)

    def getElement(self):
        return self._element_node

    def getParent(self):
        return self._parent

    def getPosition(self):
        return self._position

    def initialize(self):
        assert(not self._initialized)
        assert(self._focal_camera is not None and self._focal_lens is not None)
        assert(self._parent is not None)        

        if VERBOSE:
            print "TerrainQuadtree - initialize"
            t_init_begin = time.time()

        if VERBOSE:
            print "TerrainQuadtree - loading materials"

        from os.path import join, isfile

        state = SamplerState()

        state.setWrapU(SamplerState.WMRepeat)
        state.setWrapV(SamplerState.WMRepeat)
        # t.setKeepRamImage(False)
        # t.setMinfilter(SamplerState.FTLinear)
        state.setMinfilter(self.mipmapMIN)
        state.setMagfilter(self.mipmapMAG)
        state.setAnisotropicDegree(8)                

        for material in self._materials:
            tex0 = join(self._material_path, "{0}_1.png".format(material))
            tex1 = join(self._material_path, "{0}_2.png".format(material))
            assert(isfile(tex0) and isfile(tex1))

            tex0t = loader.loadTexture(tex0)
            tex1t = loader.loadTexture(tex1)

            tex0t.setFormat(Texture.FSrgbAlpha)
            tex1t.setFormat(Texture.FRgba)

            
            self._element_node.setShaderInput("mt_{0}_0".format(material), tex0t, state)
            self._element_node.setShaderInput("mt_{0}_1".format(material), tex1t, state)


        self._initialized = True

        self._plane_quadtree.setFocalCamera(self._focal_camera)
        self._plane_quadtree.setFocalLens(self._focal_lens)


        self._plane_quadtree.init()

        if VERBOSE:
            t_init_end = time.time()
            t_init = t_init_end - t_init_begin
            print t_init * 1000.0, "ms to initialize"

        self.update()
        
    def update(self):
        assert(self._initialized)
        self._plane_quadtree.update()
