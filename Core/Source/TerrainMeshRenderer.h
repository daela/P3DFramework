#pragma once

#include <cmath>
#include <iostream>
#include <fstream>

#include "dtool_config.h"
#include "pandabase.h"
#include "datagram.h"
#include "pnmImage.h"
#include "nodePath.h"
#include "loader.h"
#include "omniBoundingVolume.h"
#include "texture.h"
#include "geomEnums.h"
#include "lens.h"
#include "boundingBox.h"

NotifyCategoryDecl(terrain, EXPORT_CLASS, EXPORT_TEMPL);

class TerrainMeshRenderer {

    struct TerrainChunk {

        float average_height;
        float min_height;
        float max_height;
        float border_heights[4];
        float clod_factor;
        int depth;
        int chunk_size;
        int x, y;

        PT(BoundingBox) bounds;

        // The 4 children in the order 0|0 1|0 0|1 1|1
        TerrainChunk *children[4];
    };

    PUBLISHED:
		TerrainMeshRenderer();
		~TerrainMeshRenderer();

        void create();
        void update();

        void set_heightfield_size(int size);
        void set_focus(NodePath *cam, Lens *lens);
        void load_chunk_mesh(const string &filename);
        void load_bounds(const string &filename);

        void set_scale(float sx, float sy, float height);
        void set_scale(LVecBase3 scale);
        void set_pos(float x, float y, float z);
        void set_pos(LVecBase3 pos);
        void set_target_triangle_width(float width);

        void set_culling_enabled(bool enabled);

        NodePath get_node();

        static void generate_bounds(const string &filename, const string &dest, int chunk_size=32);

    protected:

        void create_children(TerrainChunk *chunk);
        void traverse(TerrainChunk *chunk, bool check_bounds = true);
        int check_frustum(TerrainChunk *chunk);
        bool should_subdivide(TerrainChunk *chunk);
        void render_chunk(TerrainChunk *chunk);

        void extract_chunk_bounds(TerrainChunk *chunk);
        inline LPoint3 transform_point(LPoint3 point);

        float target_triangle_width;

        int heightfield_size;
        int chunk_size;
        int depth;

        int max_visible_chunks;

        int chunks_rendered;

        float *chunk_data_pointer;

        LVecBase3 terrain_scale;
        LVecBase3 terrain_offset;

        NodePath *focal_camera;
        Lens *focal_lens;

        NodePath chunk_mesh;
        PT(Texture) chunk_data;

        TerrainChunk *base_chunk;

        LMatrix4        current_node_transform;
        LMatrix4        current_cam_transform;
        PT(BoundingVolume) current_cam_bounds;
        LVecBase3f      current_rel_cam_pos;

        float *chunk_bounds_data;
        int chunk_bounds_chunk_size;
        int chunk_bounds_depth;

        bool culling_enabled;

};
