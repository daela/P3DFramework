
#include "TerrainMeshRenderer.h"

NotifyCategoryDef(terrain, "rs");

TerrainMeshRenderer::TerrainMeshRenderer() {
    chunk_size = 32;
    heightfield_size = 8192;
    chunks_rendered = 0;
    base_chunk = NULL;
    max_visible_chunks = 65536 + 1;
    terrain_offset.set(0, 0, 0);
    terrain_scale.set(1.0, 1.0, 500.0);
    chunk_data = NULL;
    chunk_data_pointer = NULL;
    depth = 0;
    focal_camera = NULL;
    focal_lens = NULL;
    chunk_bounds_data = NULL;
    chunk_bounds_chunk_size = 0;
    chunk_bounds_depth = 0;
    target_triangle_width = 7;
    current_cam_bounds = NULL;
    culling_enabled = true;
}

TerrainMeshRenderer::~TerrainMeshRenderer() {
    cout << "TODO: TerrainMeshRenderer destructor!" << endl;
    // cleanup chunk_mesh
    // cleanup base_chunk (recursive)
    // cleanup chunk_data
    // cleanup chunk_bounds_data

    chunk_mesh.remove_node();
}



void TerrainMeshRenderer::create() {

    if (chunk_mesh.is_empty()) {
        terrain_cat.error() << "Chunk mesh not loaded yet, call load_chunk_mesh" << endl;
        return;
    }

    if (heightfield_size < 1) {
        terrain_cat.error() << "No heightfield size set!" << endl;
        return;
    }

    depth = log(double(heightfield_size / chunk_size)) / log(2.0) + 1;


    if (chunk_bounds_data != NULL) {
        if (chunk_bounds_chunk_size != chunk_size) {
            terrain_cat.error() << "Loaded bounds file has a different chunk size! (" << chunk_bounds_chunk_size << " instead of " << chunk_size << ")" << endl;
            return;
        }

        if (chunk_bounds_depth != depth) {
            terrain_cat.error() << "Loaded bounds file has a different chunk depth! (" << chunk_bounds_depth <<  " instead of " << depth << ")"  << endl;
            return;
        }
    }

    chunk_data = new Texture("tex");
    chunk_data->setup_buffer_texture(max_visible_chunks, Texture::T_float, Texture::F_rgba32, GeomEnums::UH_dynamic);


    // Create the chunks
    base_chunk = new TerrainChunk();
    base_chunk->average_height = 0.5;
    base_chunk->min_height = 0.0;
    base_chunk->max_height = 1.0;
    base_chunk->depth = 0;
    base_chunk->chunk_size = heightfield_size;
    base_chunk->x = 0;
    base_chunk->y = 0;
    base_chunk->clod_factor = 0.0;
    base_chunk->bounds = NULL;
    for (int i = 0; i < 4; i++) {
        base_chunk->border_heights[i] = 0.5;
    }

    extract_chunk_bounds(base_chunk);
    create_children(base_chunk);

    chunk_mesh.set_shader_input("chunkDataBuffer", chunk_data);
    chunk_mesh.set_shader_input("terrainOffset", terrain_offset);
    chunk_mesh.set_shader_input("terrainScale", terrain_scale);

}


void TerrainMeshRenderer::create_children(TerrainChunk *chunk) {

    if (chunk->depth + 1 >= depth) {
        return;
    }

    // Create the children
    for (int y = 0; y < 2; y++) {
        for (int x = 0; x < 2; x++) {
            TerrainChunk *child = new TerrainChunk();
            child->average_height = 0.5;
            child->min_height = 0.0;
            child->max_height = 1.0;
            child->chunk_size = chunk->chunk_size / 2;
            for (int i = 0; i < 4; i++) {
                child->border_heights[i] = 0.5;
            }
            child->x = chunk->x + x * child->chunk_size;
            child->y = chunk->y + y * child->chunk_size;
            child->depth = chunk->depth + 1;
            child->clod_factor = 0.0;
            child->bounds = NULL;
            chunk->children[x + y*2] = child;
            extract_chunk_bounds(child);
            create_children(child);
        }
    }
}


void TerrainMeshRenderer::update() {

    if (base_chunk == NULL) {
        terrain_cat.error() << "Terrain not created yet" << endl;
        return;
    }


    if (focal_camera == NULL || focal_lens == NULL) {
        terrain_cat.error() << "No focus set! Use set_focus() first." << endl;
        return;
    }

    current_node_transform = chunk_mesh.get_transform(*focal_camera)->get_mat();
    current_cam_transform = LMatrix4(focal_lens->get_projection_mat());
    current_rel_cam_pos = focal_camera->get_pos(chunk_mesh);
    current_cam_bounds = focal_lens->make_bounds();

    // mutiply the camera bounds with it's transform
    DCAST(GeometricBoundingVolume, current_cam_bounds)->xform(focal_camera->get_mat(chunk_mesh));


    chunk_data_pointer = (float*) chunk_data->modify_ram_image().p();
    chunks_rendered = 0;
    traverse(base_chunk);

    // cout << "Instance count:" << chunks_rendered << endl;
    chunk_mesh.set_instance_count(chunks_rendered);

}


void TerrainMeshRenderer::traverse(TerrainChunk *chunk, bool check_bounds) {
        
    if (culling_enabled && check_bounds) {
        int intersection = check_frustum(chunk);
        if (intersection == BoundingVolume::IF_no_intersection) {
            // Chunk out of frustum
            return;
        }

        if ( (intersection & BoundingVolume::IF_all) != 0) {
            // Chunk fully in frustum, don't do bounding checks for children
            check_bounds = false;
        }
    }

    if (should_subdivide(chunk)) {
        for (int i = 0; i < 4; i++) {
            traverse(chunk->children[i], check_bounds);
        }
    } else {
        render_chunk(chunk);
    }
}



void TerrainMeshRenderer::render_chunk(TerrainChunk *chunk) {

    if(chunks_rendered >= max_visible_chunks ) {
        if (chunks_rendered == max_visible_chunks) {
            terrain_cat.error() << "Too many visible chunks!" << endl;
        }
        return;
    }

    nassertv(chunk_data_pointer != NULL);

    // cout << "Rendering chunk (" << chunk->x << " / " << chunk->y << ") at level " << chunk->depth << endl;

    int data_offset = chunks_rendered * 4;

    chunk_data_pointer[data_offset + 0] = (float)chunk->x;
    chunk_data_pointer[data_offset + 1] = (float)chunk->y;
    chunk_data_pointer[data_offset + 2] = (float)chunk->chunk_size;
    chunk_data_pointer[data_offset + 3] = chunk->clod_factor;

    chunks_rendered ++;
}

int TerrainMeshRenderer::check_frustum(TerrainChunk *chunk) {
    if (chunk->bounds == NULL || current_cam_bounds == NULL) return BoundingVolume::IF_all;
    return current_cam_bounds->contains(chunk->bounds);
}


bool TerrainMeshRenderer::should_subdivide(TerrainChunk *chunk) {
    

    LVecBase2 projected_points[4];

    // Project each chunk edge to camera space
    for (int y = 0; y < 2; y++) {
        for (int x = 0; x < 2; x++) {

            LPoint3 edge_point = transform_point(LPoint3(chunk->x + x * chunk->chunk_size, chunk->y + y * chunk->chunk_size, chunk->border_heights[x+y*2]));

            LPoint3 point_3d = edge_point * current_node_transform;
            LVecBase4 point_cam_space = current_cam_transform.xform(LVecBase4(point_3d.get_x(), point_3d.get_y(), point_3d.get_z(), 1.0));
            if (point_cam_space.get_w() == 0.0) {
                point_cam_space.set(1000000.0, 1000000.0, -1000000.0, 0.0);
                // cout << "Point out of space" << endl;
            }
            point_cam_space.normalize();
            projected_points[x + y*2].set(point_cam_space.get_x() * 1600.0, point_cam_space.get_z() * 900.0);
        }
    }

    // Compute edge length
    float edge_0 = (projected_points[0] - projected_points[1]).length();
    float edge_1 = (projected_points[1] - projected_points[3]).length();
    float edge_2 = (projected_points[3] - projected_points[2]).length();
    float edge_3 = (projected_points[2] - projected_points[0]).length();

    float max_edge_len = max(edge_0, max(edge_1, max(edge_2, edge_3)));
    float tess_factor = (max_edge_len / target_triangle_width) / (float)chunk_size;

    chunk->clod_factor = max(0.0, min(1.0, (2.0 - tess_factor)));

    // Do this at the end so every chunk gets a clod factor
    if (chunk->depth + 1 >= depth) return false;

    return tess_factor > 2.0;
}

void TerrainMeshRenderer::set_heightfield_size(int size) {
    nassertv(size > 1 && size <= 8192);
    nassertv(base_chunk == NULL);
    heightfield_size = size;
}

void TerrainMeshRenderer::set_focus(NodePath *cam, Lens *lens) {
    focal_camera = cam;
    focal_lens = lens;
}

void TerrainMeshRenderer::set_scale(float sx, float sy, float height) {
    terrain_scale.set(sx, sy, height);
}

void TerrainMeshRenderer::set_scale(LVecBase3 scale) {
    terrain_scale = scale;
}

void TerrainMeshRenderer::set_pos(float x, float y, float z) {
    terrain_offset.set(x, y, z);
}

void TerrainMeshRenderer::set_pos(LVecBase3 pos) {
    terrain_offset = pos;
}


void TerrainMeshRenderer::set_target_triangle_width(float width) {
    nassertv(width >= 1.0)
    target_triangle_width = width;
}

void TerrainMeshRenderer::set_culling_enabled(bool enabled) {
    culling_enabled = enabled;
}


void TerrainMeshRenderer::extract_chunk_bounds(TerrainChunk *chunk) {

    // cout << "Extract bounds for level " << chunk->depth << "(" << chunk->chunk_size << ") " << " (" << (chunk->x/chunk->chunk_size) << " / " << (chunk->y/chunk->chunk_size) << ")" << endl;

    if (chunk_bounds_data != NULL) {
        int data_offset = 0;
        int c_size = 1;
        for (int i = 0; i < chunk->depth; i++) {
            data_offset += c_size * c_size * 7;
            c_size *= 2;
        }
        
        data_offset += ((chunk->y/chunk->chunk_size) + c_size * (chunk->x/chunk->chunk_size)) * 7;
        chunk->min_height = chunk_bounds_data[data_offset + 0];
        chunk->max_height = chunk_bounds_data[data_offset + 1];
        chunk->average_height = chunk_bounds_data[data_offset + 2];

        for (int i = 0; i < 4; i++) {
            chunk->border_heights[i] = chunk_bounds_data[data_offset + 3 + i];
        }

        chunk->bounds = new BoundingBox(
            transform_point(LPoint3(chunk->x, chunk->y, chunk->min_height)),
            transform_point(LPoint3(chunk->x + chunk->chunk_size, chunk->y + chunk->chunk_size, chunk->max_height))
        );
    }

}

LPoint3 TerrainMeshRenderer::transform_point(LPoint3 point) {
    return LPoint3(
        point.get_x() * terrain_scale.get_x() + terrain_offset.get_x(),
        point.get_y() * terrain_scale.get_y() + terrain_offset.get_y(),
        point.get_z() * terrain_scale.get_z() + terrain_offset.get_z()
    );
}

void TerrainMeshRenderer::load_bounds(const string &filename) {
    terrain_cat.debug() << "Loading bounds from " << filename << endl;

    std::ifstream infile(filename.c_str(), ios::in | ios::binary | ios::ate);

    if (!infile.is_open()) {
        terrain_cat.error() << "Couldnt open bounds file!" << endl;
        return;
    }

    int header_size = 3 * 4;
    int fsize = infile.tellg();

    if (fsize % 4 != 0 || fsize < header_size) {
        terrain_cat.error() << "Corrupted bounds file!" << endl;
        return;
    }



    infile.seekg(0, ios::beg);

    int num_floats = fsize/4 - header_size/4;

    // infile.write((char*)dg.get_data(), dg.get_length());
    terrain_cat.debug() << "Recieving " << num_floats << " floats" << endl;

    int magic_header = 0;
    int num_levels = 0;
    int file_chunk_size = 0;

    // Read header
    infile.read((char *)&magic_header, 4);

    // Read amount of levels
    infile.read((char *)&num_levels, 4);

    // Read chunk size
    infile.read((char *)&file_chunk_size, 4);

    // Check for errors
    if (magic_header != 0x70B14500) {
        terrain_cat.error() << "Invalid file header! Could not read bounds file." << endl;
        return;
    }

    if (num_levels < 1 || num_levels > 16) {
        terrain_cat.error() << "Invalid amount of levels in bounds file: " << num_levels << endl;
        return;
    }

    if (file_chunk_size != chunk_size) {
        terrain_cat.error() << "Unappropriate bounds file, expected chunk size of " << chunk_size << " but got " << file_chunk_size << endl;
        return;
    }

    // Compute expected data length
    int start_chunk_size = 1;
    int expected_file_size = header_size;
    for (int d = 0; d < num_levels; d++) {
        expected_file_size += start_chunk_size * start_chunk_size * 4 * 7;
        start_chunk_size *= 2;
    }

    // Check if the bounds file contains enough data
    if (expected_file_size != fsize) {
        terrain_cat.error() << "Invalid file length, expected " << expected_file_size << " but got " << fsize << endl;
        return;
    }

    chunk_bounds_chunk_size = file_chunk_size;
    chunk_bounds_depth = num_levels;
    chunk_bounds_data = new float[num_floats];
    infile.read((char *)chunk_bounds_data, num_floats * 4 );
    infile.close();

}

void TerrainMeshRenderer::load_chunk_mesh(const string &filename) {
    nassertv(chunk_mesh.is_empty());

    Loader *loader = Loader::get_global_ptr();
    PT(PandaNode) node = loader->load_sync(filename);

    if (node == NULL) {
        terrain_cat.error() << "Could not load chunk mesh" << endl;
        return;
    }

    node->set_final(true);
    node->set_bounds(new OmniBoundingVolume());

    chunk_mesh = NodePath(node);
}

NodePath TerrainMeshRenderer::get_node() {
    return chunk_mesh;
}


void TerrainMeshRenderer::generate_bounds(const string &filename, const string &dest, const int chunk_size) {


    terrain_cat.info() << "Loading heightfield" << endl;
    PNMImage img(filename);

    if (img.get_x_size() < 1 || img.get_y_size() < 1) {
        terrain_cat.error() << "could not load heightfield!" << endl;
        return;
    } 

    if (img.get_x_size() != img.get_y_size()) {
        terrain_cat.error() << "non-square heightfield!" << endl;
        return;
    }

    // OpenGL uses inverted y-coordinate, so we have to flip the heightmap
    img.flip(false, true, false);


    int num_levels = log(double(img.get_x_size() / chunk_size)) / log(2.0) + 1;
    Datagram dg;

    // Header with magic number
    dg.add_int32(0x70B14500);
    dg.add_int32(num_levels);
    dg.add_int32(chunk_size);

    for (int level = 0, num_chunks = 1; level < num_levels; level ++, num_chunks *= 2) {

        terrain_cat.info() << "Computing level " << level << " (" << num_chunks << ")" << endl;

        int chunk_size = img.get_x_size() / num_chunks;
        int chunk_add = chunk_size - 1;

        for (int x = 0; x < num_chunks; x++) {
            for (int y = 0; y < num_chunks; y++) {
                int cx = x * chunk_size;
                int cy = y * chunk_size;

                // Compute min, max and average chunk height
                float min_val = 1.0, max_val = 0.0, avg_val = 0.0;

                for (int sx = cx; sx < cx + chunk_size; sx++) {
                    for (int sy = cy; sy < cy + chunk_size; sy++) {
                        float val = img.get_gray(sx, sy);
                        min_val = min(min_val, val);
                        max_val = max(max_val, val);
                        avg_val += val;
                    }
                }

                avg_val /= chunk_size * chunk_size;

                dg.add_float32(min_val);
                dg.add_float32(max_val);
                dg.add_float32(avg_val);

                // Store borders in order 0,0 1,0 0,1 11
                dg.add_float32(img.get_gray(cx, cy));
                dg.add_float32(img.get_gray(cx + chunk_add, cy));
                dg.add_float32(img.get_gray(cx, cy + chunk_add));
                dg.add_float32(img.get_gray(cx + chunk_add, cy + chunk_add));
            }
        }


    }

    std::ofstream outfile;
    outfile.open(dest.c_str(), ios::out | ios::binary);
    outfile.write((char*)dg.get_data(), dg.get_length());
    outfile.close();
}

