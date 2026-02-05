"""
Blender 3D Visualization Generator for RASO Platform

This module provides 3D visualization capabilities using Blender Python API
for scientific modeling, molecular structures, network graphs, and complex visualizations.
"""

import os
import sys
import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging
import json
import math

logger = logging.getLogger(__name__)


class Visualization3DType(Enum):
    """Types of 3D visualizations that can be generated."""
    MOLECULAR = "molecular"
    NETWORK_GRAPH = "network_graph"
    DATA_VISUALIZATION = "data_visualization"
    SCIENTIFIC_MODEL = "scientific_model"
    GEOMETRIC_SHAPE = "geometric_shape"
    MATHEMATICAL_SURFACE = "mathematical_surface"


@dataclass
class BlenderScene3D:
    """3D scene configuration for Blender rendering."""
    scene_id: str
    visualization_type: Visualization3DType
    objects: List[Dict[str, Any]]
    camera_settings: Dict[str, Any]
    lighting_settings: Dict[str, Any]
    animation_settings: Dict[str, Any]
    render_settings: Dict[str, Any]
    blender_script: str
    duration: float


@dataclass
class Molecule3D:
    """3D molecular structure definition."""
    atoms: List[Dict[str, Any]]  # [{"element": "C", "position": [x, y, z], "radius": 1.0}]
    bonds: List[Dict[str, Any]]  # [{"atom1": 0, "atom2": 1, "type": "single"}]
    name: str


@dataclass
class NetworkGraph3D:
    """3D network graph definition."""
    nodes: List[Dict[str, Any]]  # [{"id": "node1", "position": [x, y, z], "size": 1.0}]
    edges: List[Dict[str, Any]]  # [{"from": "node1", "to": "node2", "weight": 1.0}]
    layout: str  # "spring", "circular", "hierarchical"


class Blender3DGenerator:
    """Generator for 3D visualizations using Blender Python API."""
    
    def __init__(self):
        self.blender_executable = None
        self.blender_available = False
        self.temp_dir = None
        
    async def initialize(self) -> bool:
        """Initialize Blender 3D generator."""
        try:
            # Try to find Blender executable
            self.blender_executable = await self._find_blender_executable()
            
            if self.blender_executable:
                # Test Blender availability
                self.blender_available = await self._test_blender()
                
                if self.blender_available:
                    # Create temporary directory for Blender scripts
                    self.temp_dir = Path(tempfile.mkdtemp(prefix="blender_3d_"))
                    logger.info(f"✅ Blender 3D Generator initialized successfully")
                    logger.info(f"   Blender executable: {self.blender_executable}")
                    logger.info(f"   Temp directory: {self.temp_dir}")
                    return True
                else:
                    logger.warning("❌ Blender executable found but not working properly")
            else:
                logger.warning("❌ Blender executable not found")
                logger.info("   To use 3D visualizations, install Blender from https://www.blender.org/")
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize Blender 3D Generator: {e}")
            return False
    
    async def _find_blender_executable(self) -> Optional[str]:
        """Find Blender executable on the system."""
        # Common Blender installation paths
        possible_paths = [
            # Windows
            "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe",
            "C:/Program Files/Blender Foundation/Blender 3.6/blender.exe",
            "C:/Program Files/Blender Foundation/Blender 3.5/blender.exe",
            "C:/Program Files/Blender Foundation/Blender 3.4/blender.exe",
            # macOS
            "/Applications/Blender.app/Contents/MacOS/Blender",
            # Linux
            "/usr/bin/blender",
            "/usr/local/bin/blender",
            "/snap/bin/blender",
        ]
        
        # Check if blender is in PATH
        try:
            result = await asyncio.create_subprocess_exec(
                "blender", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                return "blender"  # Available in PATH
        except:
            pass
        
        # Check common installation paths
        for path in possible_paths:
            if Path(path).exists():
                return path
        
        return None
    
    async def _test_blender(self) -> bool:
        """Test if Blender is working properly."""
        try:
            # Create a simple test script
            test_script = '''
import bpy
print("Blender Python API test successful")
'''
            
            test_script_path = self.temp_dir / "test_script.py" if self.temp_dir else Path("test_script.py")
            test_script_path.write_text(test_script)
            
            # Run Blender with the test script
            process = await asyncio.create_subprocess_exec(
                self.blender_executable,
                "--background",
                "--python", str(test_script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Clean up test script
            if test_script_path.exists():
                test_script_path.unlink()
            
            return process.returncode == 0 and b"test successful" in stdout
            
        except Exception as e:
            logger.error(f"Blender test failed: {e}")
            return False
    
    async def generate_molecular_visualization(
        self,
        molecule: Molecule3D,
        scene_id: str,
        duration: float = 10.0,
        animation_type: str = "rotation"
    ) -> Optional[BlenderScene3D]:
        """Generate 3D molecular visualization."""
        try:
            if not self.blender_available:
                logger.error("Blender not available for molecular visualization")
                return None
            
            # Create Blender script for molecular visualization
            blender_script = self._create_molecular_script(molecule, animation_type, duration)
            
            # Configure scene settings
            objects = []
            for i, atom in enumerate(molecule.atoms):
                objects.append({
                    "type": "sphere",
                    "name": f"atom_{i}_{atom['element']}",
                    "position": atom["position"],
                    "scale": atom.get("radius", 1.0),
                    "material": self._get_atom_material(atom["element"])
                })
            
            for i, bond in enumerate(molecule.bonds):
                objects.append({
                    "type": "cylinder",
                    "name": f"bond_{i}",
                    "start_pos": molecule.atoms[bond["atom1"]]["position"],
                    "end_pos": molecule.atoms[bond["atom2"]]["position"],
                    "radius": 0.1,
                    "material": self._get_bond_material(bond.get("type", "single"))
                })
            
            scene = BlenderScene3D(
                scene_id=scene_id,
                visualization_type=Visualization3DType.MOLECULAR,
                objects=objects,
                camera_settings=self._get_molecular_camera_settings(),
                lighting_settings=self._get_molecular_lighting_settings(),
                animation_settings={
                    "type": animation_type,
                    "duration": duration,
                    "fps": 30
                },
                render_settings=self._get_default_render_settings(),
                blender_script=blender_script,
                duration=duration
            )
            
            return scene
            
        except Exception as e:
            logger.error(f"Error generating molecular visualization: {e}")
            return None
    
    async def generate_network_graph_3d(
        self,
        network: NetworkGraph3D,
        scene_id: str,
        duration: float = 15.0,
        animation_type: str = "force_directed"
    ) -> Optional[BlenderScene3D]:
        """Generate 3D network graph visualization."""
        try:
            if not self.blender_available:
                logger.error("Blender not available for network graph visualization")
                return None
            
            # Calculate node positions if not provided
            if not all("position" in node for node in network.nodes):
                network = self._calculate_3d_layout(network)
            
            # Create Blender script for network visualization
            blender_script = self._create_network_script(network, animation_type, duration)
            
            # Configure scene objects
            objects = []
            
            # Add nodes
            for i, node in enumerate(network.nodes):
                objects.append({
                    "type": "sphere",
                    "name": f"node_{node['id']}",
                    "position": node["position"],
                    "scale": node.get("size", 1.0),
                    "material": self._get_node_material(node.get("type", "default"))
                })
            
            # Add edges
            for i, edge in enumerate(network.edges):
                from_node = next(n for n in network.nodes if n["id"] == edge["from"])
                to_node = next(n for n in network.nodes if n["id"] == edge["to"])
                
                objects.append({
                    "type": "cylinder",
                    "name": f"edge_{i}",
                    "start_pos": from_node["position"],
                    "end_pos": to_node["position"],
                    "radius": 0.05 * edge.get("weight", 1.0),
                    "material": self._get_edge_material()
                })
            
            scene = BlenderScene3D(
                scene_id=scene_id,
                visualization_type=Visualization3DType.NETWORK_GRAPH,
                objects=objects,
                camera_settings=self._get_network_camera_settings(),
                lighting_settings=self._get_network_lighting_settings(),
                animation_settings={
                    "type": animation_type,
                    "duration": duration,
                    "fps": 30
                },
                render_settings=self._get_default_render_settings(),
                blender_script=blender_script,
                duration=duration
            )
            
            return scene
            
        except Exception as e:
            logger.error(f"Error generating network graph visualization: {e}")
            return None
    
    async def generate_mathematical_surface(
        self,
        equation: str,
        scene_id: str,
        duration: float = 12.0,
        x_range: Tuple[float, float] = (-5, 5),
        y_range: Tuple[float, float] = (-5, 5),
        resolution: int = 50
    ) -> Optional[BlenderScene3D]:
        """Generate 3D mathematical surface visualization."""
        try:
            if not self.blender_available:
                logger.error("Blender not available for mathematical surface visualization")
                return None
            
            # Create Blender script for mathematical surface
            blender_script = self._create_surface_script(
                equation, x_range, y_range, resolution, duration
            )
            
            # Configure scene
            objects = [{
                "type": "mesh",
                "name": "mathematical_surface",
                "equation": equation,
                "x_range": x_range,
                "y_range": y_range,
                "resolution": resolution,
                "material": self._get_surface_material()
            }]
            
            scene = BlenderScene3D(
                scene_id=scene_id,
                visualization_type=Visualization3DType.MATHEMATICAL_SURFACE,
                objects=objects,
                camera_settings=self._get_surface_camera_settings(),
                lighting_settings=self._get_surface_lighting_settings(),
                animation_settings={
                    "type": "rotation_and_zoom",
                    "duration": duration,
                    "fps": 30
                },
                render_settings=self._get_default_render_settings(),
                blender_script=blender_script,
                duration=duration
            )
            
            return scene
            
        except Exception as e:
            logger.error(f"Error generating mathematical surface: {e}")
            return None
    
    async def render_scene(
        self,
        scene: BlenderScene3D,
        output_dir: str,
        quality: str = "medium"
    ) -> Optional[str]:
        """Render 3D scene using Blender."""
        try:
            if not self.blender_available:
                logger.error("Blender not available for rendering")
                return None
            
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create output file path
            output_file = output_path / f"{scene.scene_id}_3d.mp4"
            
            # Write Blender script to file
            script_path = self.temp_dir / f"{scene.scene_id}_script.py"
            script_path.write_text(scene.blender_script)
            
            # Update render settings based on quality
            render_settings = self._get_quality_render_settings(quality)
            
            # Run Blender rendering
            logger.info(f"Rendering 3D scene {scene.scene_id} with Blender...")
            
            process = await asyncio.create_subprocess_exec(
                self.blender_executable,
                "--background",
                "--python", str(script_path),
                "--",
                str(output_file),
                json.dumps(render_settings),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and output_file.exists():
                logger.info(f"✅ 3D scene rendered successfully: {output_file}")
                return str(output_file)
            else:
                logger.error(f"❌ Blender rendering failed:")
                logger.error(f"   stdout: {stdout.decode()}")
                logger.error(f"   stderr: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Error rendering 3D scene: {e}")
            return None
    
    def _create_molecular_script(
        self,
        molecule: Molecule3D,
        animation_type: str,
        duration: float
    ) -> str:
        """Create Blender Python script for molecular visualization."""
        return f'''
import bpy
import bmesh
import mathutils
import json
import sys
from mathutils import Vector

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set up scene
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = int({duration} * 30)  # 30 FPS

# Molecule data
atoms = {json.dumps(molecule.atoms)}
bonds = {json.dumps(molecule.bonds)}

# Create materials
def create_atom_material(element):
    mat = bpy.data.materials.new(name=f"Material_{{element}}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    
    # Element colors (simplified)
    colors = {{
        "H": (1.0, 1.0, 1.0, 1.0),  # White
        "C": (0.2, 0.2, 0.2, 1.0),  # Dark gray
        "N": (0.0, 0.0, 1.0, 1.0),  # Blue
        "O": (1.0, 0.0, 0.0, 1.0),  # Red
        "S": (1.0, 1.0, 0.0, 1.0),  # Yellow
        "P": (1.0, 0.5, 0.0, 1.0),  # Orange
    }}
    
    color = colors.get(element, (0.5, 0.5, 0.5, 1.0))
    bsdf.inputs[0].default_value = color
    bsdf.inputs[7].default_value = 0.1  # Roughness
    bsdf.inputs[15].default_value = 1.4  # IOR
    
    return mat

def create_bond_material():
    mat = bpy.data.materials.new(name="Bond_Material")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs[0].default_value = (0.7, 0.7, 0.7, 1.0)  # Light gray
    bsdf.inputs[7].default_value = 0.3  # Roughness
    return mat

# Create atoms
atom_objects = []
for i, atom in enumerate(atoms):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=atom.get("radius", 1.0),
        location=atom["position"]
    )
    
    atom_obj = bpy.context.active_object
    atom_obj.name = f"Atom_{{i}}_{{atom['element']}}"
    
    # Apply material
    mat = create_atom_material(atom["element"])
    atom_obj.data.materials.append(mat)
    
    atom_objects.append(atom_obj)

# Create bonds
bond_material = create_bond_material()
for i, bond in enumerate(bonds):
    atom1_pos = Vector(atoms[bond["atom1"]]["position"])
    atom2_pos = Vector(atoms[bond["atom2"]]["position"])
    
    # Calculate bond direction and length
    direction = atom2_pos - atom1_pos
    length = direction.length
    center = (atom1_pos + atom2_pos) / 2
    
    # Create cylinder for bond
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.1,
        depth=length,
        location=center
    )
    
    bond_obj = bpy.context.active_object
    bond_obj.name = f"Bond_{{i}}"
    
    # Rotate cylinder to align with bond direction
    bond_obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    
    # Apply material
    bond_obj.data.materials.append(bond_material)

# Set up camera
bpy.ops.object.camera_add(location=(10, -10, 5))
camera = bpy.context.active_object
camera.rotation_euler = (1.1, 0, 0.785)

# Set up lighting
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
sun = bpy.context.active_object
sun.data.energy = 3

bpy.ops.object.light_add(type='AREA', location=(-5, -5, 5))
area_light = bpy.context.active_object
area_light.data.energy = 2

# Animation setup
if "{animation_type}" == "rotation":
    # Rotate entire molecule
    bpy.ops.object.empty_add(location=(0, 0, 0))
    empty = bpy.context.active_object
    empty.name = "Molecule_Center"
    
    # Parent all atoms and bonds to empty
    for obj in atom_objects + [o for o in bpy.data.objects if o.name.startswith("Bond_")]:
        obj.parent = empty
    
    # Animate rotation
    empty.rotation_euler = (0, 0, 0)
    empty.keyframe_insert(data_path="rotation_euler", frame=1)
    
    empty.rotation_euler = (0, 0, 6.28)  # 2π radians
    empty.keyframe_insert(data_path="rotation_euler", frame=scene.frame_end)
    
    # Set interpolation to linear
    for fcurve in empty.animation_data.action.fcurves:
        for keyframe in fcurve.keyframe_points:
            keyframe.interpolation = 'LINEAR'

# Set render settings
scene.render.engine = 'CYCLES'
scene.render.filepath = sys.argv[-2] if len(sys.argv) > 1 else "/tmp/molecular_render"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'

# Parse render settings from command line
if len(sys.argv) > 2:
    render_settings = json.loads(sys.argv[-1])
    scene.render.resolution_x = render_settings.get("resolution_x", 1920)
    scene.render.resolution_y = render_settings.get("resolution_y", 1080)
    scene.cycles.samples = render_settings.get("samples", 128)

# Set camera as active
scene.camera = camera

# Render animation
bpy.ops.render.render(animation=True)
'''
    
    def _create_network_script(
        self,
        network: NetworkGraph3D,
        animation_type: str,
        duration: float
    ) -> str:
        """Create Blender Python script for network graph visualization."""
        return f'''
import bpy
import bmesh
import mathutils
import json
import sys
import random
from mathutils import Vector

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set up scene
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = int({duration} * 30)  # 30 FPS

# Network data
nodes = {json.dumps(network.nodes)}
edges = {json.dumps(network.edges)}

# Create materials
def create_node_material(node_type="default"):
    mat = bpy.data.materials.new(name=f"Node_Material_{{node_type}}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    
    # Node type colors
    colors = {{
        "default": (0.2, 0.6, 1.0, 1.0),  # Blue
        "important": (1.0, 0.2, 0.2, 1.0),  # Red
        "secondary": (0.2, 1.0, 0.2, 1.0),  # Green
        "hub": (1.0, 0.8, 0.0, 1.0),  # Yellow
    }}
    
    color = colors.get(node_type, colors["default"])
    bsdf.inputs[0].default_value = color
    bsdf.inputs[7].default_value = 0.2  # Roughness
    bsdf.inputs[15].default_value = 1.4  # IOR
    
    return mat

def create_edge_material():
    mat = bpy.data.materials.new(name="Edge_Material")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs[0].default_value = (0.5, 0.5, 0.5, 0.8)  # Semi-transparent gray
    bsdf.inputs[21].default_value = 0.2  # Alpha
    return mat

# Create nodes
node_objects = []
for i, node in enumerate(nodes):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=node.get("size", 1.0),
        location=node["position"]
    )
    
    node_obj = bpy.context.active_object
    node_obj.name = f"Node_{{node['id']}}"
    
    # Apply material
    mat = create_node_material(node.get("type", "default"))
    node_obj.data.materials.append(mat)
    
    node_objects.append(node_obj)

# Create edges
edge_material = create_edge_material()
for i, edge in enumerate(edges):
    # Find node positions
    from_node = next(n for n in nodes if n["id"] == edge["from"])
    to_node = next(n for n in nodes if n["id"] == edge["to"])
    
    from_pos = Vector(from_node["position"])
    to_pos = Vector(to_node["position"])
    
    # Calculate edge direction and length
    direction = to_pos - from_pos
    length = direction.length
    center = (from_pos + to_pos) / 2
    
    # Create cylinder for edge
    radius = 0.05 * edge.get("weight", 1.0)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius,
        depth=length,
        location=center
    )
    
    edge_obj = bpy.context.active_object
    edge_obj.name = f"Edge_{{i}}"
    
    # Rotate cylinder to align with edge direction
    edge_obj.rotation_euler = direction.to_track_quat('Z', 'Y').to_euler()
    
    # Apply material
    edge_obj.data.materials.append(edge_material)

# Set up camera
bpy.ops.object.camera_add(location=(15, -15, 10))
camera = bpy.context.active_object
camera.rotation_euler = (1.0, 0, 0.785)

# Set up lighting
bpy.ops.object.light_add(type='SUN', location=(10, 10, 15))
sun = bpy.context.active_object
sun.data.energy = 3

bpy.ops.object.light_add(type='AREA', location=(-10, -10, 8))
area_light = bpy.context.active_object
area_light.data.energy = 2

# Animation setup
if "{animation_type}" == "force_directed":
    # Animate nodes with slight movement
    for i, node_obj in enumerate(node_objects):
        # Add slight random movement
        for frame in range(1, scene.frame_end + 1, 30):
            offset = Vector((
                random.uniform(-0.5, 0.5),
                random.uniform(-0.5, 0.5),
                random.uniform(-0.2, 0.2)
            ))
            
            node_obj.location = Vector(nodes[i]["position"]) + offset
            node_obj.keyframe_insert(data_path="location", frame=frame)

elif "{animation_type}" == "rotation":
    # Rotate entire network
    bpy.ops.object.empty_add(location=(0, 0, 0))
    empty = bpy.context.active_object
    empty.name = "Network_Center"
    
    # Parent all objects to empty
    all_objects = node_objects + [o for o in bpy.data.objects if o.name.startswith("Edge_")]
    for obj in all_objects:
        obj.parent = empty
    
    # Animate rotation
    empty.rotation_euler = (0, 0, 0)
    empty.keyframe_insert(data_path="rotation_euler", frame=1)
    
    empty.rotation_euler = (0, 0, 6.28)  # 2π radians
    empty.keyframe_insert(data_path="rotation_euler", frame=scene.frame_end)

# Set render settings
scene.render.engine = 'CYCLES'
scene.render.filepath = sys.argv[-2] if len(sys.argv) > 1 else "/tmp/network_render"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'

# Parse render settings from command line
if len(sys.argv) > 2:
    render_settings = json.loads(sys.argv[-1])
    scene.render.resolution_x = render_settings.get("resolution_x", 1920)
    scene.render.resolution_y = render_settings.get("resolution_y", 1080)
    scene.cycles.samples = render_settings.get("samples", 128)

# Set camera as active
scene.camera = camera

# Render animation
bpy.ops.render.render(animation=True)
'''
    
    def _create_surface_script(
        self,
        equation: str,
        x_range: Tuple[float, float],
        y_range: Tuple[float, float],
        resolution: int,
        duration: float
    ) -> str:
        """Create Blender Python script for mathematical surface visualization."""
        return f'''
import bpy
import bmesh
import mathutils
import json
import sys
import math
from mathutils import Vector

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set up scene
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = int({duration} * 30)  # 30 FPS

# Surface parameters
equation = "{equation}"
x_min, x_max = {x_range[0]}, {x_range[1]}
y_min, y_max = {y_range[0]}, {y_range[1]}
resolution = {resolution}

# Create surface mesh
def create_surface_mesh():
    # Create new mesh
    mesh = bpy.data.meshes.new("MathSurface")
    
    # Generate vertices
    vertices = []
    faces = []
    
    x_step = (x_max - x_min) / resolution
    y_step = (y_max - y_min) / resolution
    
    # Generate grid of vertices
    for i in range(resolution + 1):
        for j in range(resolution + 1):
            x = x_min + i * x_step
            y = y_min + j * y_step
            
            # Evaluate equation (simplified - replace with actual equation parsing)
            try:
                # Simple equation evaluation (extend for more complex equations)
                if "sin" in equation and "cos" in equation:
                    z = math.sin(x) * math.cos(y)
                elif "x**2" in equation and "y**2" in equation:
                    z = x*x + y*y
                elif "x*y" in equation:
                    z = x * y
                else:
                    # Default: paraboloid
                    z = (x*x + y*y) / 10
            except:
                z = 0
            
            vertices.append((x, y, z))
    
    # Generate faces (quads)
    for i in range(resolution):
        for j in range(resolution):
            # Vertex indices for current quad
            v1 = i * (resolution + 1) + j
            v2 = v1 + 1
            v3 = v1 + (resolution + 1)
            v4 = v3 + 1
            
            # Create two triangles for each quad
            faces.append([v1, v2, v4, v3])
    
    # Create mesh
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    
    return mesh

# Create surface object
surface_mesh = create_surface_mesh()
surface_obj = bpy.data.objects.new("MathematicalSurface", surface_mesh)
bpy.context.collection.objects.link(surface_obj)

# Create material
mat = bpy.data.materials.new(name="Surface_Material")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]

# Gradient material based on height
bsdf.inputs[0].default_value = (0.2, 0.8, 1.0, 1.0)  # Blue
bsdf.inputs[7].default_value = 0.1  # Roughness
bsdf.inputs[15].default_value = 1.4  # IOR

surface_obj.data.materials.append(mat)

# Set up camera
bpy.ops.object.camera_add(location=(12, -12, 8))
camera = bpy.context.active_object
camera.rotation_euler = (1.1, 0, 0.785)

# Set up lighting
bpy.ops.object.light_add(type='SUN', location=(8, 8, 12))
sun = bpy.context.active_object
sun.data.energy = 3

bpy.ops.object.light_add(type='AREA', location=(-8, -8, 6))
area_light = bpy.context.active_object
area_light.data.energy = 2

# Animation: rotate around surface
empty = bpy.data.objects.new("Surface_Center", None)
bpy.context.collection.objects.link(empty)
empty.location = (0, 0, 0)

# Parent camera to empty for orbital animation
camera.parent = empty
camera.parent_type = 'OBJECT'

# Animate rotation
empty.rotation_euler = (0, 0, 0)
empty.keyframe_insert(data_path="rotation_euler", frame=1)

empty.rotation_euler = (0, 0, 6.28)  # 2π radians
empty.keyframe_insert(data_path="rotation_euler", frame=scene.frame_end)

# Set render settings
scene.render.engine = 'CYCLES'
scene.render.filepath = sys.argv[-2] if len(sys.argv) > 1 else "/tmp/surface_render"
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'

# Parse render settings from command line
if len(sys.argv) > 2:
    render_settings = json.loads(sys.argv[-1])
    scene.render.resolution_x = render_settings.get("resolution_x", 1920)
    scene.render.resolution_y = render_settings.get("resolution_y", 1080)
    scene.cycles.samples = render_settings.get("samples", 128)

# Set camera as active
scene.camera = camera

# Render animation
bpy.ops.render.render(animation=True)
'''
    
    def _calculate_3d_layout(self, network: NetworkGraph3D) -> NetworkGraph3D:
        """Calculate 3D positions for network nodes using spring layout."""
        import random
        
        # Simple 3D spring layout algorithm
        nodes = network.nodes.copy()
        edges = network.edges
        
        # Initialize random positions if not set
        for node in nodes:
            if "position" not in node:
                node["position"] = [
                    random.uniform(-5, 5),
                    random.uniform(-5, 5),
                    random.uniform(-2, 2)
                ]
        
        # Simple force-directed layout (simplified)
        for iteration in range(50):
            forces = {node["id"]: [0, 0, 0] for node in nodes}
            
            # Repulsive forces between all nodes
            for i, node1 in enumerate(nodes):
                for j, node2 in enumerate(nodes):
                    if i != j:
                        pos1 = Vector(node1["position"])
                        pos2 = Vector(node2["position"])
                        diff = pos1 - pos2
                        distance = max(diff.length, 0.1)
                        
                        # Repulsive force
                        force = diff.normalized() * (1.0 / (distance * distance))
                        forces[node1["id"]][0] += force.x
                        forces[node1["id"]][1] += force.y
                        forces[node1["id"]][2] += force.z * 0.5  # Reduce Z force
            
            # Attractive forces for connected nodes
            for edge in edges:
                from_node = next(n for n in nodes if n["id"] == edge["from"])
                to_node = next(n for n in nodes if n["id"] == edge["to"])
                
                pos1 = Vector(from_node["position"])
                pos2 = Vector(to_node["position"])
                diff = pos2 - pos1
                distance = diff.length
                
                # Attractive force
                force = diff.normalized() * (distance * 0.1)
                forces[from_node["id"]][0] += force.x
                forces[from_node["id"]][1] += force.y
                forces[from_node["id"]][2] += force.z * 0.5
                
                forces[to_node["id"]][0] -= force.x
                forces[to_node["id"]][1] -= force.y
                forces[to_node["id"]][2] -= force.z * 0.5
            
            # Apply forces with damping
            damping = 0.9
            for node in nodes:
                force = forces[node["id"]]
                node["position"][0] += force[0] * damping
                node["position"][1] += force[1] * damping
                node["position"][2] += force[2] * damping * 0.5  # Reduce Z movement
        
        return NetworkGraph3D(
            nodes=nodes,
            edges=edges,
            layout="spring_3d"
        )
    
    def _get_atom_material(self, element: str) -> Dict[str, Any]:
        """Get material properties for atomic elements."""
        materials = {
            "H": {"color": [1.0, 1.0, 1.0], "roughness": 0.1},
            "C": {"color": [0.2, 0.2, 0.2], "roughness": 0.2},
            "N": {"color": [0.0, 0.0, 1.0], "roughness": 0.1},
            "O": {"color": [1.0, 0.0, 0.0], "roughness": 0.1},
            "S": {"color": [1.0, 1.0, 0.0], "roughness": 0.2},
            "P": {"color": [1.0, 0.5, 0.0], "roughness": 0.2},
        }
        return materials.get(element, {"color": [0.5, 0.5, 0.5], "roughness": 0.3})
    
    def _get_bond_material(self, bond_type: str) -> Dict[str, Any]:
        """Get material properties for chemical bonds."""
        return {"color": [0.7, 0.7, 0.7], "roughness": 0.3}
    
    def _get_node_material(self, node_type: str) -> Dict[str, Any]:
        """Get material properties for network nodes."""
        materials = {
            "default": {"color": [0.2, 0.6, 1.0], "roughness": 0.2},
            "important": {"color": [1.0, 0.2, 0.2], "roughness": 0.1},
            "secondary": {"color": [0.2, 1.0, 0.2], "roughness": 0.2},
            "hub": {"color": [1.0, 0.8, 0.0], "roughness": 0.1},
        }
        return materials.get(node_type, materials["default"])
    
    def _get_edge_material(self) -> Dict[str, Any]:
        """Get material properties for network edges."""
        return {"color": [0.5, 0.5, 0.5], "roughness": 0.3, "alpha": 0.8}
    
    def _get_surface_material(self) -> Dict[str, Any]:
        """Get material properties for mathematical surfaces."""
        return {"color": [0.2, 0.8, 1.0], "roughness": 0.1, "metallic": 0.2}
    
    def _get_molecular_camera_settings(self) -> Dict[str, Any]:
        """Get camera settings for molecular visualizations."""
        return {
            "location": [10, -10, 5],
            "rotation": [1.1, 0, 0.785],
            "lens": 50,
            "clip_start": 0.1,
            "clip_end": 1000
        }
    
    def _get_network_camera_settings(self) -> Dict[str, Any]:
        """Get camera settings for network visualizations."""
        return {
            "location": [15, -15, 10],
            "rotation": [1.0, 0, 0.785],
            "lens": 35,
            "clip_start": 0.1,
            "clip_end": 1000
        }
    
    def _get_surface_camera_settings(self) -> Dict[str, Any]:
        """Get camera settings for surface visualizations."""
        return {
            "location": [12, -12, 8],
            "rotation": [1.1, 0, 0.785],
            "lens": 50,
            "clip_start": 0.1,
            "clip_end": 1000
        }
    
    def _get_molecular_lighting_settings(self) -> Dict[str, Any]:
        """Get lighting settings for molecular visualizations."""
        return {
            "sun": {"location": [5, 5, 10], "energy": 3, "angle": 0.1},
            "area": {"location": [-5, -5, 5], "energy": 2, "size": 2}
        }
    
    def _get_network_lighting_settings(self) -> Dict[str, Any]:
        """Get lighting settings for network visualizations."""
        return {
            "sun": {"location": [10, 10, 15], "energy": 3, "angle": 0.1},
            "area": {"location": [-10, -10, 8], "energy": 2, "size": 3}
        }
    
    def _get_surface_lighting_settings(self) -> Dict[str, Any]:
        """Get lighting settings for surface visualizations."""
        return {
            "sun": {"location": [8, 8, 12], "energy": 3, "angle": 0.1},
            "area": {"location": [-8, -8, 6], "energy": 2, "size": 2}
        }
    
    def _get_default_render_settings(self) -> Dict[str, Any]:
        """Get default render settings."""
        return {
            "engine": "CYCLES",
            "resolution_x": 1920,
            "resolution_y": 1080,
            "samples": 128,
            "format": "FFMPEG",
            "codec": "H264"
        }
    
    def _get_quality_render_settings(self, quality: str) -> Dict[str, Any]:
        """Get render settings based on quality level."""
        settings = self._get_default_render_settings()
        
        if quality == "low":
            settings.update({
                "resolution_x": 1280,
                "resolution_y": 720,
                "samples": 64
            })
        elif quality == "medium":
            settings.update({
                "resolution_x": 1920,
                "resolution_y": 1080,
                "samples": 128
            })
        elif quality == "high":
            settings.update({
                "resolution_x": 1920,
                "resolution_y": 1080,
                "samples": 256
            })
        
        return settings
    
    def get_system_requirements(self) -> Dict[str, Any]:
        """Get system requirements for 3D visualization."""
        return {
            "blender_available": self.blender_available,
            "blender_executable": self.blender_executable,
            "temp_directory": str(self.temp_dir) if self.temp_dir else None,
            "supported_types": [t.value for t in Visualization3DType],
            "requirements": {
                "blender": "3.4+ required for 3D visualizations",
                "memory": "4GB+ RAM recommended for complex scenes",
                "gpu": "CUDA/OpenCL GPU recommended for faster rendering"
            }
        }


# Global instance for easy access
blender_3d_generator = Blender3DGenerator()