# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# ----------------------------------------------------------
# File: measureit_main.py
# Main panel for different Measureit general actions
# Author: Antonio Vazquez (antonioya)
#
# ----------------------------------------------------------
# noinspection PyUnresolvedReferences
import bpy
import bmesh
from bmesh import from_edit_mesh
# noinspection PyUnresolvedReferences
import bgl
import gpu
from gpu_extras.batch import batch_for_shader

from bpy.types import PropertyGroup, Panel, Object, Operator, SpaceView3D
from bpy.props import IntProperty, CollectionProperty, FloatVectorProperty, BoolProperty, StringProperty, \
                      FloatProperty, EnumProperty
from bpy.app.handlers import persistent
# noinspection PyUnresolvedReferences
from .measureit_geometry import *
from .measureit_render import *


# ------------------------------------------------------
# Handler to detect new Blend load
#
# ------------------------------------------------------
# noinspection PyUnusedLocal
@persistent
def load_handler(dummy):
    RunHintDisplayButton.handle_remove(None, bpy.context)


# ------------------------------------------------------
# Handler to detect save Blend
# Clear not used measured
#
# ------------------------------------------------------
# noinspection PyUnusedLocal
@persistent
def save_handler(dummy):
    # noinspection PyBroadException
    try:
        print("MeasureIt: Cleaning data")
        objlist = bpy.context.scene.objects
        for myobj in objlist:
            if 'MeasureGenerator' in myobj:
                mp = myobj.MeasureGenerator[0]
                x = 0
                for ms in mp.measureit_segments:
                    ms.name = "segment_" + str(x)
                    x += 1
                    if ms.glfree is True:
                        idx = mp.measureit_segments.find(ms.name)
                        if idx > -1:
                            print("MeasureIt: Removed segment not used")
                            mp.measureit_segments.remove(idx)

                # reset size
                mp.measureit_num = len(mp.measureit_segments)
    except:
        pass


bpy.app.handlers.load_post.append(load_handler)
bpy.app.handlers.save_pre.append(save_handler)


# ------------------------------------------------------------------
# Define property group class for measureit faces index
# ------------------------------------------------------------------
class MeasureitIndex(PropertyGroup):
    glidx = IntProperty(name="index",
                        description="vertex index")


# Register
bpy.utils.register_class(MeasureitIndex)


# ------------------------------------------------------------------
# Define property group class for measureit faces
# ------------------------------------------------------------------
class MeasureitFaces(PropertyGroup):
    glface = IntProperty(name="glface",
                         description="Face number")
    # Array of index
    measureit_index = CollectionProperty(type=MeasureitIndex)


# Register
bpy.utils.register_class(MeasureitFaces)


# ------------------------------------------------------------------
# Define property group class for measureit data
# ------------------------------------------------------------------
class MeasureitProperties(PropertyGroup):
    style: IntProperty(name="style",
                        description="Dimension Style to use",
                        min = 0)
    gltype: IntProperty(name="gltype",
                         description="Measure type (1-Segment, 2-Label, etc..)", default=1)
    glpointa: IntProperty(name="glpointa",
                           description="Hidden property for opengl")
    glpointb: IntProperty(name="glpointb",
                           description="Hidden property for opengl")
    glpointc: IntProperty(name="glpointc",
                           description="Hidden property for opengl")
    glcolor: FloatVectorProperty(name="glcolor",
                                  description="Color for the measure",
                                  default=(0.173, 0.545, 1.0, 1.0),
                                  min=0.1,
                                  max=1,
                                  subtype='COLOR',
                                  size=4)
    glview: BoolProperty(name="glview",
                          description="Measure visible/hide",
                          default=True)
    glspace: FloatProperty(name='glspace', min=-100, max=100, default=0.1,
                            precision=3,
                            description='Distance to display measure')
    glwidth: IntProperty(name='glwidth', min=1, max=20, default=1,
                          description='line width')
    glfree: BoolProperty(name="glfree",
                          description="This measure is free and can be deleted",
                          default=False)
    gltxt: StringProperty(name="gltxt", maxlen=256,
                           description="Short description (use | for line break)")
    gladvance: BoolProperty(name="gladvance",
                             description="Advanced options as line width or position",
                             default=False)
    gldefault: BoolProperty(name="gldefault",
                             description="Display measure in position calculated by default",
                             default=True)
    glnormalx: FloatProperty(name="glnormalx",
                              description="Change orientation in X axis",
                              default=1, min=-1, max=1, precision=2)
    glnormaly: FloatProperty(name="glnormaly",
                              description="Change orientation in Y axis",
                              default=0, min=-1, max=1, precision=2)
    glnormalz: FloatProperty(name="glnormalz",
                              description="Change orientation in Z axis",
                              default=0, min=-1, max=1, precision=2)
    glfont_size: IntProperty(name="Text Size",
                              description="Text size",
                              default=14, min=6, max=150)
    glfont_align: EnumProperty(items=(('L', "Left align", ""),
                                       ('C', "Center align", ""),
                                       ('R', "Right align", "")),
                                name="align Font",
                                description="Set Font alignment")
    glfont_rotat: IntProperty(name='Rotate', min=0, max=360, default=0,
                                description="Text rotation in degrees")
    gllink: StringProperty(name="gllink",
                            description="linked object for linked measures")
    glocwarning: BoolProperty(name="glocwarning",
                               description="Display a warning if some axis is not used in distance",
                               default=True)
    glocx: BoolProperty(name="glocx",
                         description="Include changes in X axis for calculating the distance",
                         default=True)
    glocy: BoolProperty(name="glocy",
                         description="Include changes in Y axis for calculating the distance",
                         default=True)
    glocz: BoolProperty(name="glocz",
                         description="Include changes in Z axis for calculating the distance",
                         default=True)
    glfontx: IntProperty(name="glfontx",
                          description="Change font position in X axis",
                          default=0, min=-3000, max=3000)
    glfonty: IntProperty(name="glfonty",
                          description="Change font position in Y axis",
                          default=0, min=-3000, max=3000)
    gldist: BoolProperty(name="gldist",
                          description="Display distance for this measure",
                          default=True)
    glnames: BoolProperty(name="glnames",
                           description="Display text for this measure",
                           default=True)
    gltot: EnumProperty(items=(('99', "-", "Select a group for sum"),
                                ('0', "A", ""),
                                ('1', "B", ""),
                                ('2', "C", ""),
                                ('3', "D", ""),
                                ('4', "E", ""),
                                ('5', "F", ""),
                                ('6', "G", ""),
                                ('7', "H", ""),
                                ('8', "I", ""),
                                ('9', "J", ""),
                                ('10', "K", ""),
                                ('11', "L", ""),
                                ('12', "M", ""),
                                ('13', "N", ""),
                                ('14', "O", ""),
                                ('15', "P", ""),
                                ('16', "Q", ""),
                                ('17', "R", ""),
                                ('18', "S", ""),
                                ('19', "T", ""),
                                ('20', "U", ""),
                                ('21', "V", ""),
                                ('22', "W", ""),
                                ('23', "X", ""),
                                ('24', "Y", ""),
                                ('25', "Z", "")),
                         name="Sum in Group",
                         description="Add segment length in selected group")
    glorto: EnumProperty(items=(('99', "None", ""),
                                 ('0', "A", "Point A must use selected point B location"),
                                 ('1', "B", "Point B must use selected point A location")),
                          name="Orthogonal",
                          description="Display point selected as orthogonal (select axis to copy)")
    glorto_x: BoolProperty(name="ox",
                            description="Copy X location",
                            default=False)
    glorto_y: BoolProperty(name="oy",
                            description="Copy Y location",
                            default=False)
    glorto_z: BoolProperty(name="oz",
                            description="Copy Z location",
                            default=False)
    glarrow_a: EnumProperty(items=(('99', "--", "No arrow"),
                                    ('1', "Line", "The point of the arrow are lines"),
                                    ('2', "Triangle", "The point of the arrow is triangle"),
                                    ('3', "TShape", "The point of the arrow is a T")),
                             name="A end",
                             description="Add arrows to point A")
    glarrow_b: EnumProperty(items=(('99', "--", "No arrow"),
                                    ('1', "Line", "The point of the arrow are lines"),
                                    ('2', "Triangle", "The point of the arrow is triangle"),
                                    ('3', "TShape", "The point of the arrow is a T")),
                             name="B end",
                             description="Add arrows to point B")
    glarrow_s: IntProperty(name="Size",
                            description="Arrow size",
                            default=15, min=6, max=500)

    glarc_full: BoolProperty(name="arcfull",
                              description="Create full circunference",
                              default=False)
    glarc_extrad: BoolProperty(name="arcextrad",
                                description="Adapt radio lengh to arc line",
                                default=True)
    glarc_rad: BoolProperty(name="arc rad",
                             description="Show arc radius",
                             default=True)
    glarc_len: BoolProperty(name="arc len",
                             description="Show arc length",
                             default=True)
    glarc_ang: BoolProperty(name="arc ang",
                             description="Show arc angle",
                             default=True)

    glarc_a: EnumProperty(items=(('99', "--", "No arrow"),
                                  ('1', "Line", "The point of the arrow are lines"),
                                  ('2', "Triangle", "The point of the arrow is triangle"),
                                  ('3', "TShape", "The point of the arrow is a T")),
                           name="Ar end",
                           description="Add arrows to point A")
    glarc_b: EnumProperty(items=(('99', "--", "No arrow"),
                                  ('1', "Line", "The point of the arrow are lines"),
                                  ('2', "Triangle", "The point of the arrow is triangle"),
                                  ('3', "TShape", "The point of the arrow is a T")),
                           name="Br end",
                           description="Add arrows to point B")
    glarc_s: IntProperty(name="Size",
                          description="Arrow size",
                          default=15, min=6, max=500)
    glarc_txradio: StringProperty(name="txradio",
                                   description="Text for radius", default="r=")
    glarc_txlen: StringProperty(name="txlen",
                                 description="Text for length", default="L=")
    glarc_txang: StringProperty(name="txang",
                                 description="Text for angle", default="A=")
    glcolorarea: FloatVectorProperty(name="glcolorarea",
                                      description="Color for the measure of area",
                                      default=(0.1, 0.1, 0.1, 1.0),
                                      min=0.1,
                                      max=1,
                                      subtype='COLOR',
                                      size=4)

    # Array of faces
    measureit_faces = CollectionProperty(type=MeasureitFaces)


# Register
bpy.utils.register_class(MeasureitProperties)


# ------------------------------------------------------------------
# Define object class (container of segments)
# Measureit
# ------------------------------------------------------------------
class MeasureContainer(PropertyGroup):
    measureit_num = IntProperty(name='Number of measures', min=0, max=1000, default=0,
                                description='Number total of measureit elements')
    # Array of segments
    measureit_segments = CollectionProperty(type=MeasureitProperties)


bpy.utils.register_class(MeasureContainer)
Object.MeasureGenerator = CollectionProperty(type=MeasureContainer)




# ------------------------------------------------------------------
# Define UI class
# show/Hide Dimensions
# ------------------------------------------------------------------
class MeasureitShowHidePanel(Panel):
    bl_idname = "measureit.showhidepanel"
    bl_label = "Show/Hide Dimensions"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MeasureIt'

    # -----------------------------------------------------
    # Draw (create UI interface)
    # -----------------------------------------------------
    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        # ------------------------------
        # Display Buttons
        # ------------------------------
        row = box.row()
        if context.window_manager.measureit_run_opengl is False:
            icon = 'PLAY'
            txt = 'Show'
        else:
            icon = "PAUSE"
            txt = 'Hide'

        row.operator("measureit.runopenglbutton", text=txt, icon=icon)
        row.prop(scene, "measureit_gl_ghost", text="", icon='GHOST_ENABLED')



# ------------------------------------------------------------------
# Define UI class
# Measureit
# ------------------------------------------------------------------
class MeasureitEditPanel(Panel):
    bl_idname = "measureit.editpanel"
    bl_label = "Dimensions"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MeasureIt'

    # -----------------------------------------------------
    # Verify if visible
    # -----------------------------------------------------
    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        if 'MeasureGenerator' not in o:
            return False
        else:
            mp = context.object.MeasureGenerator[0]
            if mp.measureit_num > 0:
                return True
            else:
                return False

    # -----------------------------------------------------
    # Draw (create UI interface)
    # -----------------------------------------------------
    # noinspection PyUnusedLocal
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        if context.object is not None:
            if 'MeasureGenerator' in context.object:
                box = layout.box()
                row = box.row()
                row.label(text=context.object.name)
                row = box.row()
                row.prop(scene, 'measureit_gl_precision', text="Precision")
                row = box.row()
                row.prop(scene, 'measureit_units')
                col = box.column(align=True)
                col.prop(scene, 'measureit_gl_show_d', text="Distances", toggle=True, icon="ALIGN_CENTER")
                col.prop(scene, 'measureit_gl_show_n', text="Texts", toggle=True, icon="FONT_DATA")
                
                row = box.row()
                row.prop(scene, 'measureit_hide_units', text="Hide measurement unit")
                # Scale factor
                row = box.row()
                row.prop(scene, 'measureit_scale', text="Scale")
                if scene.measureit_scale is True:
                    split = row.split(factor=0.25, align=False)
                    split.prop(scene, 'measureit_scale_color', text="")
                    split.prop(scene, 'measureit_scale_factor', text="1")
                    row = box.row()
                    row.separator()
                    row.prop(scene, 'measureit_gl_scaletxt', text="")
                    row.prop(scene, 'measureit_scale_font')
                    row.prop(scene, 'measureit_scale_precision', text="")
                    row = box.row()
                    row.separator()
                    row.prop(scene, 'measureit_scale_pos_x')
                    row.prop(scene, 'measureit_scale_pos_y')

                # Override
                row = box.row()
                row.prop(scene, 'measureit_ovr', text="Override")
                if scene.measureit_ovr is True:
                    split = row.split(factor=0.25, align=False)
                    split.prop(scene, 'measureit_ovr_color', text="")
                    split.prop(scene, 'measureit_ovr_width', text="Width")
                    row = box.row()
                    row.separator()
                    row.prop(scene, 'measureit_ovr_font', text="Font")
                    row.prop(scene, 'measureit_ovr_font_align', text="")
                    if scene.measureit_ovr_font_align == 'L':
                        row.prop(scene, 'measureit_ovr_font_rotation', text="Rotate")

                mp = context.object.MeasureGenerator[0]
                # -----------------
                # loop
                # -----------------
                if mp.measureit_num > 0:
                    box = layout.box()
                    row = box.row(align = True)
                    row.operator("measureit.expandallsegmentbutton", text="Expand all", icon="ADD")
                    row.operator("measureit.collapseallsegmentbutton", text="Collapse all", icon="REMOVE")
                    for idx in range(0, mp.measureit_num):
                        if mp.measureit_segments[idx].glfree is False:
                            add_item(box, idx, mp.measureit_segments[idx])

                row = box.row()
                row.operator("measureit.deleteallsegmentbutton", text="Delete all", icon="X")
                # -----------------
                # Sum loop segments
                # -----------------
                if mp.measureit_num > 0:
                    scale = bpy.context.scene.unit_settings.scale_length
                    tx = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S",
                          "T", "U", "V", "W", "X", "Y", "Z"]
                    tot = [0.0] * len(tx)
                    ac = [False] * len(tx)
                    myobj = context.object
                    obverts = get_mesh_vertices(myobj)
                    viewtot = False
                    for idx in range(0, mp.measureit_num):
                        ms = mp.measureit_segments[idx]
                        if (ms.gltype == 1 or ms.gltype == 12
                            or ms.gltype == 13 or ms.gltype == 14) and ms.gltot != '99' \
                                and ms.glfree is False:  # only segments
                            if bpy.context.mode == "EDIT_MESH":
                                bm = bmesh.from_edit_mesh(bpy.context.edit_object.data)
                                if hasattr(bm.verts, "ensure_lookup_table"):
                                    bm.verts.ensure_lookup_table()
                            if ms.glpointa <= len(obverts) and ms.glpointb <= len(obverts):
                                p1 = get_point(obverts[ms.glpointa].co, myobj)
                                if ms.gltype == 1:
                                    p2 = get_point(obverts[ms.glpointb].co, myobj)
                                elif ms.gltype == 12:
                                    p2 = get_point((0.0,
                                                    obverts[ms.glpointa].co[1],
                                                    obverts[ms.glpointa].co[2]), myobj)
                                elif ms.gltype == 13:
                                    p2 = get_point((obverts[ms.glpointa].co[0],
                                                    0.0,
                                                    obverts[ms.glpointa].co[2]), myobj)
                                else:
                                    p2 = get_point((obverts[ms.glpointa].co[0],
                                                    obverts[ms.glpointa].co[1],
                                                    0.0), myobj)

                                dist, distloc = distance(p1, p2, ms.glocx, ms.glocy, ms.glocz)
                                if dist == distloc:
                                    usedist = dist
                                else:
                                    usedist = distloc
                                usedist *= scale
                                tot[int(ms.gltot)] += usedist
                                ac[int(ms.gltot)] = True
                                viewtot = True
                    # -----------------
                    # Print values
                    # -----------------
                    if viewtot is True:
                        pr = scene.measureit_gl_precision
                        fmt = "%1." + str(pr) + "f"
                        units = scene.measureit_units

                        box = layout.box()
                        box.label(text="Totals", icon='SOLO_ON')
                        final = 0
                        for idx in range(0, len(tot)):
                            if ac[idx] is True:
                                final += tot[idx]
                                tx_dist = format_distance(fmt, units, tot[idx])
                                row = box.row(align = True)
                                row.label(text="Group " + tx[idx] + ":")
                                row.label(text=" ")
                                row.label(text=tx_dist)

                        # Grand total
                        row = box.row(align=True)
                        row.label(text="")
                        row.label(text=" ")
                        row.label(text="-" * 20)
                        tx_dist = format_distance(fmt, units, final)

                        row = box.row(align=True)
                        row.label(text="")
                        row.label(text=" ")
                        row.label(text=tx_dist)
                        # delete all
                        row = box.row()
                        row.operator("measureit.deleteallsumbutton", text="Delete all", icon="X")


# -----------------------------------------------------
# Add segment options to the panel.
# -----------------------------------------------------
def add_item(box, idx, segment):
    scene = bpy.context.scene
    box = box.box()
    row = box.row(align=True)
    if segment.glview is True:
        icon = "VISIBLE_IPO_ON"
    else:
        icon = "VISIBLE_IPO_OFF"

    row.prop(segment, 'glview', text="", toggle=True, icon=icon)
    row.prop(segment, 'gladvance', text="", toggle=True, icon="PREFERENCES")
    row.prop(segment, 'style', text="")
    row.prop(segment, 'gltxt', text="")
    op = row.operator("measureit.deletesegmentbutton", text="", icon="X")
    op.tag = idx  # saves internal data

    if segment.gladvance is True:
        col = box.column()
        col.use_property_split = True

        if segment.gltype == 20:  # Area special
            
            col.prop(segment, 'glcolorarea', text="Area Color")
            col.prop(segment, 'glcolor', text="Color")
        else:
            col.prop(segment, 'glcolor', text="Color")

        if segment.gltype != 9 and segment.gltype != 10 and segment.gltype != 20:
            col.prop(segment, 'gldefault', text="Automatic position")

            col = box.column(align=True)
            col.use_property_split = True

            col.prop(segment, 'glspace', text="Distance")
            col.prop(segment, 'glwidth', text="Lineweight")
            if segment.gldefault is False:
                col.prop(segment, 'glnormalx', text="X")
                col.prop(segment, 'glnormaly', text="Y")
                col.prop(segment, 'glnormalz', text="Z")
            
            

        col = box.column(align=True)
        col.use_property_split = True

        col.prop(segment, 'glfont_size', text="Font Size")
        col.prop(segment, 'glfont_rotat', text="Rotate")
        col.prop(segment, 'glfontx', text="X")
        col.prop(segment, 'glfonty', text="Y")
        col.prop(segment, 'glfont_align', text="Align")

        # Arrows
        if segment.gltype != 9 and segment.gltype != 10 and segment.gltype != 20:
            col = box.column(align=True)
            col.use_property_split = True

            col.prop(segment, 'glarrow_a', text="Arrow Start ")
            col.prop(segment, 'glarrow_b', text="End ")
            if segment.glarrow_a != '99' or segment.glarrow_b != '99':
                col.prop(segment, 'glarrow_s', text="Size")

        if segment.gltype != 2 and segment.gltype != 10:
            col = box.column(align=True)
            col.use_property_split = True
            if scene.measureit_gl_show_d is True and segment.gltype != 9 and segment.gltype != 21:
                if segment.gldist is True:
                    icon = "VISIBLE_IPO_ON"
                else:
                    icon = "VISIBLE_IPO_OFF"
                col.prop(segment, 'gldist', text="Distance", toggle=True, icon=icon)
            if scene.measureit_gl_show_n is True:
                if segment.glnames is True:
                    icon = "VISIBLE_IPO_ON"
                else:
                    icon = "VISIBLE_IPO_OFF"
                col.prop(segment, 'glnames', text="Text", toggle=True, icon=icon)
            # sum distances

            col = box.column(align=True)
            col.use_property_split = True

            if segment.gltype == 1 or segment.gltype == 12 or segment.gltype == 13 or segment.gltype == 14:
                col.prop(segment, 'gltot', text="Sum")

        

        # Loc axis
        if segment.gltype != 2 and segment.gltype != 9 and segment.gltype != 10 \
                and segment.gltype != 11 and segment.gltype != 12 and segment.gltype != 13 \
                and segment.gltype != 14 and segment.gltype != 20:
            row = box.row(align = True)
            row.prop(segment, 'glocx', text="X", toggle=True)
            row.prop(segment, 'glocy', text="Y", toggle=True)
            row.prop(segment, 'glocz', text="Z", toggle=True)
            if segment.glocx is False or segment.glocy is False or segment.glocz is False:
                row = box.row()
                if segment.gltype == 1:
                    row.prop(segment, 'glorto', text="Orthogonal")
                row.prop(segment, 'glocwarning', text="Warning")
                # ortogonal (only segments)
                if segment.gltype == 1:
                    if segment.glorto != "99":
                        row = box.row(align=True)
                        row.prop(segment, 'glorto_x', text="X", toggle=True)
                        row.prop(segment, 'glorto_y', text="Y", toggle=True)
                        row.prop(segment, 'glorto_z', text="Z", toggle=True)

        # Arc special
        if segment.gltype == 11:
            row = box.row(align = True)
            row.prop(segment, 'glarc_rad', text="Radius")
            row.prop(segment, 'glarc_len', text="Length")
            row.prop(segment, 'glarc_ang', text="Angle")

            row = box.row(align = True)
            row.prop(segment, 'glarc_txradio', text="")
            row.prop(segment, 'glarc_txlen', text="")
            row.prop(segment, 'glarc_txang', text="")
            row = box.row(align = True)
            row.prop(segment, 'glarc_full', text="Full Circle")
            if segment.glarc_rad is True:
                row.prop(segment, 'glarc_extrad', text="Adapt radio")

            row = box.row(align = True)
            row.prop(segment, 'glarc_a', text="")
            row.prop(segment, 'glarc_b', text="")
            if segment.glarc_a != '99' or segment.glarc_b != '99':
                row.prop(segment, 'glarc_s', text="Size")


# ------------------------------------------------------------------
# Define panel class for main functions.
# ------------------------------------------------------------------
class MeasureitMainPanel(Panel):
    bl_idname = "MEASUREIT_PT_main_panel"
    bl_label = "Add Dimension"
    bl_space_type = 'VIEW_3D'
    bl_region_type = "UI"
    bl_category = 'Measureit'

    # ------------------------------
    # Draw UI
    # ------------------------------
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # ------------------------------
        # Tool Buttons
        # ------------------------------

        # Tools
        box = layout.box()
        box.label(text="Add Measures")
        row = box.row()
        row.operator("measureit.addsegmentbutton", text="Segment", icon="ALIGN_CENTER")
        row = box.row()
        row.prop(scene, "measureit_sum", text="Sum")

        # To origin
        row = box.row()
        split = row.split(align=True)
        op = split.operator("measureit.addsegmentortobutton", text="X", icon="ALIGN_CENTER")
        op.tag = 0  # saves internal data
        op = split.operator("measureit.addsegmentortobutton", text="Y", icon="ALIGN_CENTER")
        op.tag = 1  # saves internal data
        op = split.operator("measureit.addsegmentortobutton", text="Z", icon="ALIGN_CENTER")
        op.tag = 2  # saves internal data

        row = box.row()
        row.operator("measureit.addanglebutton", text="Angle", icon="LINCURVE")
        row = box.row()
        row.operator("measureit.addarcbutton", text="Arc", icon="DRIVER_ROTATIONAL_DIFFERENCE")

        row = box.row()
        row.operator("measureit.addlabelbutton", text="Label", icon="FONT_DATA")
        row = box.row()
        row.operator("measureit.addnotebutton", text="Annotation", icon="FILE_NEW")

        row = box.row()
        row.operator("measureit.addlinkbutton", text="Link", icon="PIVOT_MEDIAN")
        row = box.row()
        row.operator("measureit.addoriginbutton", text="Origin", icon="PIVOT_CURSOR")

        row = box.row()
        row.operator("measureit.addareabutton", text="Area", icon="MESH_GRID")
        
        # ------------------------------
        # Linework Tools
        # ------------------------------

        box = layout.box()
        box.label(text="Add Lines")
        row = box.row()
        row.operator("measureit.addlinebutton", text="Line", icon="ALIGN_CENTER")

        # ------------------------------
        # Debug data
        # ------------------------------
        box = layout.box()
        row = box.row(align=False)
        if scene.measureit_debug is False:
            row.prop(scene, "measureit_debug", icon="TRIA_RIGHT",
                     text="Mesh Debug", emboss=False)
        else:
            row.prop(scene, "measureit_debug", icon="TRIA_DOWN",
                     text="Mesh Debug", emboss=False)

            row = box.row()
            split = row.split(factor=0.10, align=True)
            split.prop(scene, 'measureit_debug_obj_color', text="")
            split.prop(scene, "measureit_debug_objects", icon="OBJECT_DATA")
            split.prop(scene, "measureit_debug_object_loc", icon="EMPTY_DATA")

            row = box.row()
            split = row.split(factor=0.10, align=True)
            split.prop(scene, 'measureit_debug_vert_color', text="")
            split.prop(scene, "measureit_debug_vertices", icon="VERTEXSEL")
            split.prop(scene, "measureit_debug_vert_loc", icon="EMPTY_DATA")
            if scene.measureit_debug_vert_loc is True:
                split.prop(scene, 'measureit_debug_vert_loc_toggle', text="")

            row = box.row()
            split = row.split(factor=0.10, align=True)
            split.prop(scene, 'measureit_debug_edge_color', text="")
            split = split.split(factor=0.5, align=True)
            split.prop(scene, "measureit_debug_edges", icon="EDGESEL")

            row = box.row()
            split = row.split(factor=0.10, align=True)
            split.prop(scene, 'measureit_debug_face_color', text="")
            split = split.split(factor=0.5, align=True)
            split.prop(scene, "measureit_debug_faces", icon="FACESEL")

            row = box.row()
            split = row.split(factor=0.10, align=True)
            split.prop(scene, 'measureit_debug_norm_color', text="")
            if scene.measureit_debug_normals is False:
                split = split.split(factor=0.50, align=True)
                split.prop(scene, "measureit_debug_normals", icon="DRIVER_TRANSFORM")
            else:
                split = split.split(factor=0.5, align=True)
                split.prop(scene, "measureit_debug_normals", icon="DRIVER_TRANSFORM")
                split.prop(scene, "measureit_debug_normal_size")
                row = box.row()
                split = row.split(factor=0.10, align=True)
                split.separator()
                split.prop(scene, "measureit_debug_normal_details")
                split.prop(scene, 'measureit_debug_width', text="Thickness")

            row = box.row(align=True)
            row.prop(scene, "measureit_debug_select", icon="GHOST_ENABLED")
            row.prop(scene, 'measureit_debug_font', text="Font")
            row.prop(scene, 'measureit_debug_precision', text="Precision")


# ------------------------------------------------------------------
# Define panel class for conf functions.
# ------------------------------------------------------------------
class MeasureitConfPanel(Panel):
    bl_idname = "measureit_conf_panel"
    bl_label = "Dimension Styles"
    bl_space_type = 'VIEW_3D'
    bl_region_type = "UI"
    bl_category = 'Measureit'
    bl_options = {'DEFAULT_CLOSED'}

    # ------------------------------
    # Draw UI
    # ------------------------------
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Configuration data
        box = layout.box()
        box.label(text = 'Default Settings')
        row = box.row()
        split = row.split(factor=0.2, align=True)
        
        split.prop(scene, "measureit_default_color", text="")
        split.prop(scene, "measureit_gl_txt", text="")

        col = box.column(align=True)
        col.use_property_split = True
        col.prop(scene, "measureit_default_style", text="Style")
        col.prop(scene, "measureit_hint_space", text="Distance")
        col.prop(scene, "measureit_gl_width", text="Lineweight")

        col = box.column(align=True)
        col.use_property_split = True
        col.prop(scene, "measureit_font_size")
        col.prop(scene, "measureit_font_rotation", text="Rotate")
        col.prop(scene, "measureit_font_align", text="Alignment")
        # Arrow
        col = box.column()
        col.use_property_split = True

        col.prop(scene, "measureit_glarrow_a", text="Arrow Start")
        col.prop(scene, "measureit_glarrow_b", text="End")
        if scene.measureit_glarrow_a != '99' or scene.measureit_glarrow_b != '99':
            col.prop(scene, "measureit_glarrow_s", text="Size")
        row = box.row(align=True)

        box = layout.box()
        box.label(text="Dimension Styles")
        col = box.column()
        col.operator("measureit.adddimstylebutton", text="New Dimension Style", icon="ADD")
        
        #-------------------
        # Add Styles to Panel
        #--------------------
        if 'StyleGenerator' in context.scene:
            styleGen = context.scene.StyleGenerator[0]

            if styleGen.style_num > 0:
                box = layout.box()
                for idx in range(0, styleGen.style_num):
                    add_style_item(box, idx, styleGen.measureit_styles[idx])
      
        col = box.column()
        col.operator("measureit.deleteallstylesbutton", text="Delete All Styles", icon="X")

def add_style_item(box, idx, style):
    scene = bpy.context.scene
    box = box.box()
    row = box.row(align=True)
    if style.glview is True:
        icon = "VISIBLE_IPO_ON"
    else:
        icon = "VISIBLE_IPO_OFF"
    
    row.prop(style, 'glview', text="", toggle=True, icon=icon)
    row.prop(style, 'gladvance', text="", toggle=True, icon="PREFERENCES")

    split = row.split(factor=0.25, align=True)
    split.prop(style, 'glcolor', text="")
    split.prop(style, 'styleName', text="")
    #op = row.operator("measureit.deletesegmentbutton", text="", icon="X")
    #op.tag = idx  # saves internal data

    if style.gladvance is True:
        col = box.column()
        col.use_property_split = True
        col.prop(style, 'gltxt', text="Text")
        col.prop(style, 'gldefault', text="Automatic position")

        col = box.column(align=True)
        col.use_property_split = True

        col.prop(style, 'glspace', text="Distance")
        col.prop(style, 'glwidth', text="Lineweight")
        if style.gldefault is False:
            col.prop(style, 'glnormalx', text="X")
            col.prop(style, 'glnormaly', text="Y")
            col.prop(style, 'glnormalz', text="Z")
    
        col = box.column(align=True)
        col.use_property_split = True

        col.prop(style, 'glfont_size', text="Font Size")
        col.prop(style, 'glfont_rotat', text="Rotate")
        col.prop(style, 'glfontx', text="X")
        col.prop(style, 'glfonty', text="Y")
        col.prop(style, 'glfont_align', text="Align")
        
        # Arrows
        
        col = box.column(align=True)
        col.use_property_split = True

        col.prop(style, 'glarrow_a', text="Arrow Start ")
        col.prop(style, 'glarrow_b', text="End ")
        if style.glarrow_a != '99' or style.glarrow_b != '99':
            col.prop(style, 'glarrow_s', text="Size")

# ------------------------------------------------------------------
# Define panel class for render functions.
# ------------------------------------------------------------------
class MeasureitRenderPanel(Panel):
    bl_idname = "measureit_render_panel"
    bl_label = "MeasureIt Render"
    bl_space_type = 'VIEW_3D'
    bl_region_type = "UI"
    bl_category = 'Measureit'
    bl_options = {'DEFAULT_CLOSED'}

    # ------------------------------
    # Draw UI
    # ------------------------------
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Render settings
        box = layout.box()
        row = box.row()
        row.prop(scene, "measureit_render_type")
        row = box.row()
        row.operator("measureit.rendersegmentbutton", icon='SCRIPT')
        row = box.row()
        row.prop(scene, "measureit_render", text="Save render image")
        row = box.row()
        row.prop(scene, "measureit_rf", text="Frame")
        if scene.measureit_rf is True:
            row.prop(scene, "measureit_rf_color", text="Color")
            row = box.row()
            row.prop(scene, "measureit_rf_border", text="Space")
            row.prop(scene, "measureit_rf_line", text="Width")


# -------------------------------------------------------------
# Defines button that adds a measure segment
#
# -------------------------------------------------------------
class AddSegmentButton(Operator):
    bl_idname = "measureit.addsegmentbutton"
    bl_label = "Add"
    bl_description = "(EDITMODE only) Add a new measure segment between 2 vertices (select 2 vertices or more)"
    bl_category = 'Measureit'

    # ------------------------------
    # Poll
    # ------------------------------
    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        else:
            if o.type == "MESH":
                if bpy.context.mode == 'EDIT_MESH':
                    return True
                else:
                    return False
            else:
                return False

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            scene = context.scene
            mainobject = context.object
            mylist = get_smart_selected(mainobject)
            if len(mylist) < 2:  # if not selected linked vertex
                mylist = get_selected_vertex(mainobject)

            if len(mylist) >= 2:
                if 'MeasureGenerator' not in mainobject:
                    mainobject.MeasureGenerator.add()

                mp = mainobject.MeasureGenerator[0]
                for x in range(0, len(mylist) - 1, 2):
                    # -----------------------
                    # Only if not exist
                    # -----------------------
                    if exist_segment(mp, mylist[x], mylist[x + 1]) is False:
                        # Create all array elements
                        for cont in range(len(mp.measureit_segments) - 1, mp.measureit_num):
                            mp.measureit_segments.add()

                        # Set values
                        ms = mp.measureit_segments[mp.measureit_num]
                        ms.gltype = 1
                        ms.style = scene.measureit_default_style
                        ms.glpointa = mylist[x]
                        ms.glpointb = mylist[x + 1]
                        ms.glarrow_a = scene.measureit_glarrow_a
                        ms.glarrow_b = scene.measureit_glarrow_b
                        ms.glarrow_s = scene.measureit_glarrow_s
                        # color
                        ms.glcolor = scene.measureit_default_color
                        # dist
                        ms.glspace = scene.measureit_hint_space
                        # text
                        ms.gltxt = scene.measureit_gl_txt
                        ms.glfont_size = scene.measureit_font_size
                        ms.glfont_align = scene.measureit_font_align
                        ms.glfont_rotat = scene.measureit_font_rotation
                        # Sum group
                        ms.gltot = scene.measureit_sum
                        # Add index
                        mp.measureit_num += 1

                # redraw
                context.area.tag_redraw()
                return {'FINISHED'}
            else:
                self.report({'ERROR'},
                            "MeasureIt: Select at least two vertices for creating measure segment.")
                return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


# -------------------------------------------------------------
# Defines button that adds an area measure
#
# -------------------------------------------------------------
class AddAreaButton(Operator):
    bl_idname = "measureit.addareabutton"
    bl_label = "Area"
    bl_description = "(EDITMODE only) Add a new measure for area (select 1 o more faces)"
    bl_category = 'Measureit'

    # ------------------------------
    # Poll
    # ------------------------------
    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        else:
            if o.type == "MESH":
                if bpy.context.mode == 'EDIT_MESH':
                    return True
                else:
                    return False
            else:
                return False

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            scene = context.scene
            mainobject = context.object
            mylist = get_selected_faces(mainobject)
            if len(mylist) >= 1:
                if 'MeasureGenerator' not in mainobject:
                    mainobject.MeasureGenerator.add()

                mp = mainobject.MeasureGenerator[0]
                mp.measureit_segments.add()
                ms = mp.measureit_segments[mp.measureit_num]
                ms.gltype = 20

                f = -1
                for face in mylist:
                    # Create array elements
                    ms.measureit_faces.add()
                    f += 1
                    # Set values
                    mf = ms.measureit_faces[f]
                    mf.glface = f
                    i = 0
                    for v in face:
                        mf.measureit_index.add()
                        mi = mf.measureit_index[i]
                        mi.glidx = v
                        i += 1

                # color
                rgb = scene.measureit_default_color
                ms.glcolor = (rgb[0], rgb[1], rgb[2], 0.4)
                # dist
                ms.glspace = scene.measureit_hint_space
                # text
                ms.gltxt = scene.measureit_gl_txt
                ms.glfont_size = scene.measureit_font_size
                ms.glfont_align = scene.measureit_font_align
                ms.glfont_rotat = scene.measureit_font_rotation
                # Sum group
                ms.gltot = scene.measureit_sum
                # Add index
                mp.measureit_num += 1
                # redraw
                context.area.tag_redraw()
                return {'FINISHED'}
            else:
                self.report({'ERROR'},
                            "MeasureIt: Select at least one face for creating area measure. ")
                return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


# -------------------------------------------------------------
# Defines button that adds a measure segment to x/y/z origin
#
# -------------------------------------------------------------
class AddSegmentOrtoButton(Operator):
    bl_idname = "measureit.addsegmentortobutton"
    bl_label = "Add"
    bl_description = "(EDITMODE only) Add a new measure segment from vertex to object origin for one " \
                     "axis (select 1 vertex)"
    bl_category = 'Measureit'
    tag = IntProperty()

    # ------------------------------
    # Poll
    # ------------------------------
    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        else:
            if o.type == "MESH":
                if bpy.context.mode == 'EDIT_MESH':
                    return True
                else:
                    return False
            else:
                return False

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            scene = context.scene
            mainobject = context.object
            mylist = get_smart_selected(mainobject)
            if len(mylist) < 1:  # if not selected linked vertex
                mylist = get_selected_vertex(mainobject)

            if len(mylist) >= 1:
                if 'MeasureGenerator' not in mainobject:
                    mainobject.MeasureGenerator.add()

                mp = mainobject.MeasureGenerator[0]
                for x in range(0, len(mylist)):
                    # -----------------------
                    # Only if not exist
                    # -----------------------
                    if exist_segment(mp, mylist[x], mylist[x], 12 + int(self.tag)) is False:
                        # Create all array elements
                        for cont in range(len(mp.measureit_segments) - 1, mp.measureit_num):
                            mp.measureit_segments.add()

                        # Set values
                        ms = mp.measureit_segments[mp.measureit_num]
                        ms.gltype = 12 + int(self.tag)
                        ms.glpointa = mylist[x]
                        ms.glpointb = mylist[x]
                        ms.glarrow_a = scene.measureit_glarrow_a
                        ms.glarrow_b = scene.measureit_glarrow_b
                        ms.glarrow_s = scene.measureit_glarrow_s
                        # color
                        ms.glcolor = scene.measureit_default_color
                        # dist
                        ms.glspace = scene.measureit_hint_space
                        # text
                        ms.gltxt = scene.measureit_gl_txt
                        ms.glfont_size = scene.measureit_font_size
                        ms.glfont_align = scene.measureit_font_align
                        ms.glfont_rotat = scene.measureit_font_rotation
                        # Sum group
                        ms.gltot = scene.measureit_sum
                        # Add index
                        mp.measureit_num += 1

                # redraw
                context.area.tag_redraw()
                return {'FINISHED'}
            else:
                self.report({'ERROR'},
                            "MeasureIt: Select at least one vertex for creating measure segment.")
                return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


# -------------------------------------------------------------
# Defines button that adds an angle measure
#
# -------------------------------------------------------------
class AddAngleButton(Operator):
    bl_idname = "measureit.addanglebutton"
    bl_label = "Angle"
    bl_description = "(EDITMODE only) Add a new angle measure (select 3 vertices, 2nd is angle vertex)"
    bl_category = 'Measureit'

    # ------------------------------
    # Poll
    # ------------------------------
    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        else:
            if o.type == "MESH":
                if bpy.context.mode == 'EDIT_MESH':
                    return True
                else:
                    return False
            else:
                return False

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            scene = context.scene
            mainobject = context.object
            mylist = get_selected_vertex_history(mainobject)
            if len(mylist) == 3:
                if 'MeasureGenerator' not in mainobject:
                    mainobject.MeasureGenerator.add()

                mp = mainobject.MeasureGenerator[0]
                # -----------------------
                # Only if not exist
                # -----------------------
                if exist_segment(mp, mylist[0], mylist[1], 9, mylist[2]) is False:
                    # Create all array elements
                    for cont in range(len(mp.measureit_segments) - 1, mp.measureit_num):
                        mp.measureit_segments.add()

                    # Set values
                    ms = mp.measureit_segments[mp.measureit_num]
                    ms.gltype = 9
                    ms.glpointa = mylist[0]
                    ms.glpointb = mylist[1]
                    ms.glpointc = mylist[2]
                    # color
                    ms.glcolor = scene.measureit_default_color
                    # dist
                    ms.glspace = scene.measureit_hint_space
                    # text
                    ms.gltxt = scene.measureit_gl_txt
                    ms.glfont_size = scene.measureit_font_size
                    ms.glfont_align = scene.measureit_font_align
                    ms.glfont_rotat = scene.measureit_font_rotation
                    # Add index
                    mp.measureit_num += 1

                # redraw
                context.area.tag_redraw()
                return {'FINISHED'}
            else:
                self.report({'ERROR'},
                            "MeasureIt: Select three vertices for creating angle measure")
                return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


# -------------------------------------------------------------
# Defines button that adds an arc measure
#
# -------------------------------------------------------------
class AddArcButton(Operator):
    bl_idname = "measureit.addarcbutton"
    bl_label = "Angle"
    bl_description = "(EDITMODE only) Add a new arc measure (select 3 vertices of the arc," \
                     " vertices 1st and 3rd are arc extremes)"
    bl_category = 'Measureit'

    # ------------------------------
    # Poll
    # ------------------------------
    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        else:
            if o.type == "MESH":
                if bpy.context.mode == 'EDIT_MESH':
                    return True
                else:
                    return False
            else:
                return False

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            scene = context.scene
            mainobject = context.object
            mylist = get_selected_vertex_history(mainobject)
            if len(mylist) == 3:
                if 'MeasureGenerator' not in mainobject:
                    mainobject.MeasureGenerator.add()

                mp = mainobject.MeasureGenerator[0]
                # -----------------------
                # Only if not exist
                # -----------------------
                if exist_segment(mp, mylist[0], mylist[1], 11, mylist[2]) is False:
                    # Create all array elements
                    for cont in range(len(mp.measureit_segments) - 1, mp.measureit_num):
                        mp.measureit_segments.add()

                    # Set values
                    ms = mp.measureit_segments[mp.measureit_num]
                    ms.gltype = 11
                    ms.glpointa = mylist[0]
                    ms.glpointb = mylist[1]
                    ms.glpointc = mylist[2]
                    ms.glarrow_a = scene.measureit_glarrow_a
                    ms.glarrow_b = scene.measureit_glarrow_b
                    ms.glarrow_s = scene.measureit_glarrow_s
                    # color
                    ms.glcolor = scene.measureit_default_color
                    # dist
                    ms.glspace = scene.measureit_hint_space
                    # text
                    ms.gltxt = scene.measureit_gl_txt
                    ms.glfont_size = scene.measureit_font_size
                    ms.glfont_align = scene.measureit_font_align
                    ms.glfont_rotat = scene.measureit_font_rotation
                    # Add index
                    mp.measureit_num += 1

                # redraw
                context.area.tag_redraw()
                return {'FINISHED'}
            else:
                self.report({'ERROR'},
                            "MeasureIt: Select three vertices for creating arc measure")
                return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


# -------------------------------------------------------------
# Defines button that adds a label segment
#
# -------------------------------------------------------------
class AddLabelButton(Operator):
    bl_idname = "measureit.addlabelbutton"
    bl_label = "Add"
    bl_description = "(EDITMODE only) Add a new measure label (select 1 vertex)"
    bl_category = 'Measureit'

    # ------------------------------
    # Poll
    # ------------------------------
    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        else:
            if o.type == "MESH":
                if bpy.context.mode == 'EDIT_MESH':
                    return True
                else:
                    return False
            else:
                return False

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            scene = context.scene
            mainobject = context.object
            mylist = get_selected_vertex(mainobject)
            if len(mylist) == 1:
                if 'MeasureGenerator' not in mainobject:
                    mainobject.MeasureGenerator.add()

                mp = mainobject.MeasureGenerator[0]
                # -----------------------
                # Only if not exist
                # -----------------------
                if exist_segment(mp, mylist[0], mylist[0], 2) is False:  # Both equal
                    # Create all array elements
                    for cont in range(len(mp.measureit_segments) - 1, mp.measureit_num):
                        mp.measureit_segments.add()

                    # Set values
                    ms = mp.measureit_segments[mp.measureit_num]
                    ms.gltype = 2
                    ms.glpointa = mylist[0]
                    ms.glpointb = mylist[0]  # Equal
                    ms.glarrow_a = scene.measureit_glarrow_a
                    ms.glarrow_b = scene.measureit_glarrow_b
                    ms.glarrow_s = scene.measureit_glarrow_s
                    # color
                    ms.glcolor = scene.measureit_default_color
                    # dist
                    ms.glspace = scene.measureit_hint_space
                    # text
                    ms.gltxt = scene.measureit_gl_txt
                    ms.glfont_size = scene.measureit_font_size
                    ms.glfont_align = scene.measureit_font_align
                    ms.glfont_rotat = scene.measureit_font_rotation
                    # Add index
                    mp.measureit_num += 1

                # redraw
                context.area.tag_redraw()
                return {'FINISHED'}
            else:
                self.report({'ERROR'},
                            "MeasureIt: Select one vertex for creating measure label")
                return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


# -------------------------------------------------------------
# Defines button that adds a link
#
# -------------------------------------------------------------
class AddLinkButton(Operator):
    bl_idname = "measureit.addlinkbutton"
    bl_label = "Add"
    bl_description = "(OBJECT mode only) Add a new measure between objects (select 2 " \
                     "objects and optionally 1 or 2 vertices)"
    bl_category = 'Measureit'

    # ------------------------------
    # Poll
    # ------------------------------
    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        else:
            if o.type == "MESH" or o.type == "EMPTY" or o.type == "CAMERA" or o.type == "LAMP":
                if bpy.context.mode == 'OBJECT':
                    return True
                else:
                    return False
            else:
                return False

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            scene = context.scene
            mainobject = context.object
            # -------------------------------
            # Verify number of objects
            # -------------------------------
            if len(context.selected_objects) != 2:
                self.report({'ERROR'},
                            "MeasureIt: Select two objects only, and optionally 1 vertex or 2 vertices "
                            "(one of each object)")
                return {'FINISHED'}
            # Locate other object
            linkobject = None
            for o in context.selected_objects:
                if o.name != mainobject.name:
                    linkobject = o.name
            # Verify destination vertex
            lkobj = bpy.data.objects[linkobject]
            mylinkvertex = get_selected_vertex(lkobj)
            if len(mylinkvertex) > 1:
                self.report({'ERROR'},
                            "MeasureIt: The destination object has more than one vertex selected. "
                            "Select only 1 or none")
                return {'FINISHED'}
            # Verify origin vertex
            myobjvertex = get_selected_vertex(mainobject)
            if len(mylinkvertex) > 1:
                self.report({'ERROR'},
                            "MeasureIt: The active object has more than one vertex selected. Select only 1 or none")
                return {'FINISHED'}

            # -------------------------------
            # Add properties
            # -------------------------------
            flag = False
            if 'MeasureGenerator' not in mainobject:
                mainobject.MeasureGenerator.add()

            mp = mainobject.MeasureGenerator[0]

            # if exist_segment(mp, mylist[0], mylist[0], 3) is False:
            #     flag = True
            # Create all array elements
            for cont in range(len(mp.measureit_segments) - 1, mp.measureit_num):
                mp.measureit_segments.add()

            # Set values
            ms = mp.measureit_segments[mp.measureit_num]
            # -----------------------
            # Vertex to Vertex
            # -----------------------
            if len(myobjvertex) == 1 and len(mylinkvertex) == 1:
                ms.gltype = 3
                ms.glpointa = myobjvertex[0]
                ms.glpointb = mylinkvertex[0]
                flag = True
            # -----------------------
            # Vertex to Object
            # -----------------------
            if len(myobjvertex) == 1 and len(mylinkvertex) == 0:
                ms.gltype = 4
                ms.glpointa = myobjvertex[0]
                ms.glpointb = 0
                flag = True
            # -----------------------
            # Object to Vertex
            # -----------------------
            if len(myobjvertex) == 0 and len(mylinkvertex) == 1:
                ms.gltype = 5
                ms.glpointa = 0
                ms.glpointb = mylinkvertex[0]
                flag = True
            # -----------------------
            # Object to Object
            # -----------------------
            if len(myobjvertex) == 0 and len(mylinkvertex) == 0:
                ms.gltype = 8
                ms.glpointa = 0
                ms.glpointb = 0  # Equal
                flag = True

            # ------------------
            # only if created
            # ------------------
            if flag is True:
                ms.glarrow_a = scene.measureit_glarrow_a
                ms.glarrow_b = scene.measureit_glarrow_b
                ms.glarrow_s = scene.measureit_glarrow_s
                # color
                ms.glcolor = scene.measureit_default_color
                # dist
                ms.glspace = scene.measureit_hint_space
                # text
                ms.gltxt = scene.measureit_gl_txt
                ms.glfont_size = scene.measureit_font_size
                ms.glfont_align = scene.measureit_font_align
                ms.glfont_rotat = scene.measureit_font_rotation
                # link
                ms.gllink = linkobject
                # Add index
                mp.measureit_num += 1

                # -----------------------
                # Only if not exist
                # -----------------------
                # redraw
                context.area.tag_redraw()
                return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


# -------------------------------------------------------------
# Defines button that adds an origin segment
#
# -------------------------------------------------------------
class AddOriginButton(Operator):
    bl_idname = "measureit.addoriginbutton"
    bl_label = "Add"
    bl_description = "(OBJECT mode only) Add a new measure to origin (select object and optionally 1 vertex)"
    bl_category = 'Measureit'

    # ------------------------------
    # Poll
    # ------------------------------
    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        else:
            if o.type == "MESH" or o.type == "EMPTY" or o.type == "CAMERA" or o.type == "LAMP":
                if bpy.context.mode == 'OBJECT':
                    return True
                else:
                    return False
            else:
                return False

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            scene = context.scene
            mainobject = context.object
            mylist = get_selected_vertex(mainobject)
            if 'MeasureGenerator' not in mainobject:
                mainobject.MeasureGenerator.add()

            mp = mainobject.MeasureGenerator[0]
            # Create all array elements
            for cont in range(len(mp.measureit_segments) - 1, mp.measureit_num):
                mp.measureit_segments.add()

            # -----------------------
            # Set values
            # -----------------------
            ms = mp.measureit_segments[mp.measureit_num]
            flag = False
            if len(mylist) > 0:
                if len(mylist) == 1:
                    if exist_segment(mp, mylist[0], mylist[0], 6) is False:  # Both equal
                        flag = True
                        # Vertex to origin
                        ms.gltype = 6
                        ms.glpointa = mylist[0]
                        ms.glpointb = mylist[0]
                else:
                    self.report({'ERROR'},
                                "MeasureIt: Enter in EDITMODE and select one vertex only for creating "
                                "measure from vertex to origin")
                    return {'FINISHED'}
            else:
                # Object to origin
                if exist_segment(mp, 0, 0, 7) is False:  # Both equal
                    flag = True
                    ms.gltype = 7
                    ms.glpointa = 0
                    ms.glpointb = 0
            # ------------------
            # only if created
            # ------------------
            if flag is True:
                ms.glarrow_a = scene.measureit_glarrow_a
                ms.glarrow_b = scene.measureit_glarrow_b
                ms.glarrow_s = scene.measureit_glarrow_s
                # color
                ms.glcolor = scene.measureit_default_color
                # dist
                ms.glspace = scene.measureit_hint_space
                # text
                ms.gltxt = scene.measureit_gl_txt
                ms.glfont_size = scene.measureit_font_size
                ms.glfont_align = scene.measureit_font_align
                ms.glfont_rotat = scene.measureit_font_rotation
                # Add index
                mp.measureit_num += 1

            # redraw
            context.area.tag_redraw()

            return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


# -------------------------------------------------------------
# Defines button that deletes a measure segment
#
# -------------------------------------------------------------
class DeleteSegmentButton(Operator):
    bl_idname = "measureit.deletesegmentbutton"
    bl_label = "Delete"
    bl_description = "Delete a measure"
    bl_category = 'Measureit'
    tag= IntProperty()

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            mainobject = context.object
            mp = mainobject.MeasureGenerator[0]
            ms = mp.measureit_segments[self.tag]
            ms.glfree = True
            # Delete element
            mp.measureit_segments.remove(self.tag)
            mp.measureit_num -= 1
            # redraw
            context.area.tag_redraw()
            return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


# -------------------------------------------------------------
# Defines button that deletes all measure segments
#
# -------------------------------------------------------------
class DeleteAllSegmentButton(Operator):
    bl_idname = "measureit.deleteallsegmentbutton"
    bl_label = "Delete"
    bl_description = "Delete all measures (it cannot be undone)"
    bl_category = 'Measureit'
    tag= IntProperty()

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            mainobject = context.object
            mp = mainobject.MeasureGenerator[0]

            while len(mp.measureit_segments) > 0:
                mp.measureit_segments.remove(0)

            # reset size
            mp.measureit_num = len(mp.measureit_segments)
            # redraw
            context.area.tag_redraw()
            return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


# -------------------------------------------------------------
# Defines button that deletes all measure segment sums
#
# -------------------------------------------------------------
class DeleteAllSumButton(Operator):
    bl_idname = "measureit.deleteallsumbutton"
    bl_label = "Delete"
    bl_description = "Delete all sum groups"
    bl_category = 'Measureit'
    tag= IntProperty()

    # ------------------------------
    # Execute button action
    # ------------------------------
    # noinspection PyMethodMayBeStatic
    def execute(self, context):
        if context.object is not None:
            if 'MeasureGenerator' in context.object:
                mp = context.object.MeasureGenerator[0]
                for idx in range(0, mp.measureit_num):
                    ms = mp.measureit_segments[idx]
                    ms.gltot = '99'

            return {'FINISHED'}


# -------------------------------------------------------------
# Defines button that expands all measure segments
#
# -------------------------------------------------------------
class ExpandAllSegmentButton(Operator):
    bl_idname = "measureit.expandallsegmentbutton"
    bl_label = "Expand"
    bl_description = "Expand all measure properties"
    bl_category = 'Measureit'
    tag= IntProperty()

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            mainobject = context.object
            mp = mainobject.MeasureGenerator[0]

            for i in mp.measureit_segments:
                i.gladvance = True

            return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


# -------------------------------------------------------------
# Defines button that collapses all measure segments
#
# -------------------------------------------------------------
class CollapseAllSegmentButton(Operator):
    bl_idname = "measureit.collapseallsegmentbutton"
    bl_label = "Collapse"
    bl_description = "Collapses all measure properties"
    bl_category = 'Measureit'
    tag= IntProperty()

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            mainobject = context.object
            mp = mainobject.MeasureGenerator[0]

            for i in mp.measureit_segments:
                i.gladvance = False

            return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


# -------------------------------------------------------------
# Defines button for render option
#
# -------------------------------------------------------------
class RenderSegmentButton(Operator):
    bl_idname = "measureit.rendersegmentbutton"
    bl_label = "Render"
    bl_description = "Create a render image with measures. Use UV/Image editor to view image generated"
    bl_category = 'Measureit'
    tag= IntProperty()

    # ------------------------------
    # Execute button action
    # ------------------------------
    # noinspection PyMethodMayBeStatic,PyUnusedLocal
    def execute(self, context):
        scene = context.scene
        msg = "New image created with measures. Open it in UV/image editor"
        camera_msg = "Unable to render. No camera found"
        # -----------------------------
        # Check camera
        # -----------------------------
        if scene.camera is None:
            self.report({'ERROR'}, camera_msg)
            return {'FINISHED'}
        # -----------------------------
        # Use default render
        # -----------------------------
        if scene.measureit_render_type == "1":
            # noinspection PyBroadException
            try:
                result = bpy.data.images['Render Result']
                bpy.ops.render.render()
            except:
                bpy.ops.render.render()
            print("MeasureIt: Using current render image on buffer")
            if render_main(self, context) is True:
                self.report({'INFO'}, msg)

        # -----------------------------
        # OpenGL image
        # -----------------------------
        if scene.measureit_render_type == "2":
            self.set_camera_view()
            self.set_only_render(True)

            print("MeasureIt: Rendering opengl image")
            bpy.ops.render.opengl()
            if render_main(self, context) is True:
                self.report({'INFO'}, msg)

            self.set_only_render(False)

        # -----------------------------
        # OpenGL Animation
        # -----------------------------
        if scene.measureit_render_type == "3":
            oldframe = scene.frame_current
            self.set_camera_view()
            self.set_only_render(True)
            flag = False
            # loop frames
            for frm in range(scene.frame_start, scene.frame_end + 1):
                scene.frame_set(frm)
                print("MeasureIt: Rendering opengl frame %04d" % frm)
                bpy.ops.render.opengl()
                flag = render_main(self, context, True)
                if flag is False:
                    break

            self.set_only_render(False)
            scene.frame_current = oldframe
            if flag is True:
                self.report({'INFO'}, msg)

        # -----------------------------
        # Image
        # -----------------------------
        if scene.measureit_render_type == "4":
            print("MeasureIt: Rendering image")
            bpy.ops.render.render()
            if render_main(self, context) is True:
                self.report({'INFO'}, msg)

        # -----------------------------
        # Animation
        # -----------------------------
        if scene.measureit_render_type == "5":
            oldframe = scene.frame_current
            flag = False
            # loop frames
            for frm in range(scene.frame_start, scene.frame_end + 1):
                scene.frame_set(frm)
                print("MeasureIt: Rendering frame %04d" % frm)
                bpy.ops.render.render()
                flag = render_main(self, context, True)
                if flag is False:
                    break

            scene.frame_current = oldframe
            if flag is True:
                self.report({'INFO'}, msg)

        return {'FINISHED'}

    # ---------------------
    # Set cameraView
    # ---------------------
    # noinspection PyMethodMayBeStatic
    def set_camera_view(self):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].region_3d.view_perspective = 'CAMERA'

    # -------------------------------------
    # Set only render status
    # -------------------------------------
    # noinspection PyMethodMayBeStatic
    def set_only_render(self, status):
        screen = bpy.context.screen

        v3d = False
        s = None
        # get spaceview_3d in current screen
        for a in screen.areas:
            if a.type == 'VIEW_3D':
                for s in a.spaces:
                    if s.type == 'VIEW_3D':
                        v3d = s
                        break

        if v3d is not False:
            s.show_only_render = status


# -------------------------------------------------------------
# Defines a new note
#
# -------------------------------------------------------------
class AddNoteButton(Operator):
    bl_idname = "measureit.addnotebutton"
    bl_label = "Note"
    bl_description = "(OBJECT mode only) Add a new annotation"
    bl_category = 'Measureit'
    tag= IntProperty()

    # ------------------------------
    # Poll
    # ------------------------------
    # noinspection PyUnusedLocal
    @classmethod
    def poll(cls, context):
        if bpy.context.mode == 'OBJECT':
            return True
        else:
            return False

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            bpy.ops.object.empty_add(type='PLAIN_AXES')
            myempty = bpy.data.objects[bpy.context.active_object.name]
            myempty.location = bpy.context.scene.cursor_location
            myempty.empty_display_size = 0.01
            myempty.name = "Annotation"
            # Add properties
            scene = context.scene
            mainobject = myempty
            if 'MeasureGenerator' not in mainobject:
                mainobject.MeasureGenerator.add()

            mp = mainobject.MeasureGenerator[0]
            # Create all array elements
            for cont in range(len(mp.measureit_segments) - 1, mp.measureit_num):
                mp.measureit_segments.add()

            # Set values
            ms = mp.measureit_segments[mp.measureit_num]
            ms.gltype = 10
            ms.glpointa = 0
            ms.glpointb = 0  # Equal
            # color
            ms.glcolor = scene.measureit_default_color
            # dist
            ms.glspace = scene.measureit_hint_space
            # text
            ms.gltxt = scene.measureit_gl_txt
            ms.glfont_size = scene.measureit_font_size
            ms.glfont_align = scene.measureit_font_align
            ms.glfont_rotat = scene.measureit_font_rotation
            # Add index
            mp.measureit_num += 1

            # redraw
            context.area.tag_redraw()
            return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


# -------------------------------------------------------------
# Defines button that enables/disables the tip display
#
# -------------------------------------------------------------
class RunHintDisplayButton(Operator):
    bl_idname = "measureit.runopenglbutton"
    bl_label = "Display hint data manager"
    bl_description = "Main control for enabling or disabling the display of measurements in the viewport"
    bl_category = 'Measureit'

    _handle = None  # keep function handler

    # ----------------------------------
    # Enable gl drawing adding handler
    # ----------------------------------
    @staticmethod
    def handle_add(self, context):
        if RunHintDisplayButton._handle is None:
            RunHintDisplayButton._handle = SpaceView3D.draw_handler_add(draw_callback_px, (self, context),
                                                                        'WINDOW',
                                                                        'POST_PIXEL')
            context.window_manager.measureit_run_opengl = True

    # ------------------------------------
    # Disable gl drawing removing handler
    # ------------------------------------
    # noinspection PyUnusedLocal
    @staticmethod
    def handle_remove(self, context):
        if RunHintDisplayButton._handle is not None:
            SpaceView3D.draw_handler_remove(RunHintDisplayButton._handle, 'WINDOW')
        RunHintDisplayButton._handle = None
        context.window_manager.measureit_run_opengl = False

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            if context.window_manager.measureit_run_opengl is False:
                self.handle_add(self, context)
                context.area.tag_redraw()
            else:
                self.handle_remove(self, context)
                context.area.tag_redraw()

            return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}



class AddLineButton(Operator):
    bl_idname = "measureit.addlinebutton"
    bl_label = "Add"
    bl_description = "(EDITMODE only) Add a new measure segment between 2 vertices (select 2 vertices or more)"
    bl_category = 'Measureit'

    # ------------------------------
    # Poll
    # ------------------------------
    @classmethod
    def poll(cls, context):
        o = context.object
        if o is None:
            return False
        else:
            if o.type == "MESH":
                if bpy.context.mode == 'EDIT_MESH':
                    return True
                else:
                    return False
            else:
                return False

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            scene = context.scene
            mainobject = context.object
            mylist = get_smart_selected(mainobject)
            if len(mylist) < 2:  # if not selected linked vertex
                mylist = get_selected_vertex(mainobject)

            if len(mylist) >= 2:
                if 'MeasureGenerator' not in mainobject:
                    mainobject.MeasureGenerator.add()

                mp = mainobject.MeasureGenerator[0]
                for x in range(0, len(mylist) - 1, 2):
                    # -----------------------
                    # Only if not exist
                    # -----------------------
                    if exist_segment(mp, mylist[x], mylist[x + 1]) is False:
                        # Create all array elements
                        for cont in range(len(mp.measureit_segments) - 1, mp.measureit_num):
                            mp.measureit_segments.add()

                        # Set values
                        ms = mp.measureit_segments[mp.measureit_num]
                        ms.gltype = 21
                        ms.style = scene.measureit_default_style
                        ms.glpointa = mylist[x]
                        ms.glpointb = mylist[x + 1]
                        ms.glarrow_a = scene.measureit_glarrow_a
                        ms.glarrow_b = scene.measureit_glarrow_b
                        ms.glarrow_s = scene.measureit_glarrow_s
                        ms.glwidth = scene.measureit_gl_width
                        # color
                        ms.glcolor = scene.measureit_default_color
                        # dist
                        ms.glspace = scene.measureit_hint_space
                        # text
                        ms.gltxt = 'line'
                        ms.glnames = False
                        ms.gldist = False
                        ms.glfont_size = scene.measureit_font_size
                        ms.glfont_align = scene.measureit_font_align
                        ms.glfont_rotat = scene.measureit_font_rotation
                        
                        # Sum group
                        ms.gltot = scene.measureit_sum
                        # Add index
                        mp.measureit_num += 1

                # redraw
                context.area.tag_redraw()
                return {'FINISHED'}
            else:
                self.report({'ERROR'},
                            "MeasureIt: Select at least two vertices for creating measure segment.")
                return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


class AddDimStyleButton(Operator):
    bl_idname = "measureit.adddimstylebutton"
    bl_label = "Add"
    bl_description = "Create A New Dimension Style"
    bl_category = 'Measureit'

    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            scene = context.scene
            mainobject = context.object
            mylist = get_smart_selected(mainobject)
            if 'StyleGenerator' not in scene:
                scene.StyleGenerator.add()

            styleGen = scene.StyleGenerator[0]
            styleGen.measureit_styles.add()

            newStyle = styleGen.measureit_styles[styleGen.style_num]

            #Style Properties
            newStyle.styleName = 'Style1'
            newStyle.glcolor = scene.measureit_default_color
            
            newStyle.glwidth = scene.measureit_gl_width
            newStyle.glarrow_a = scene.measureit_glarrow_a
            newStyle.glarrow_b = scene.measureit_glarrow_b
            newStyle.glarrow_s = scene.measureit_glarrow_s
            # dist
            newStyle.glspace = scene.measureit_hint_space
            # text
            newStyle.gltxt = scene.measureit_gl_txt
            newStyle.glfont_size = scene.measureit_font_size
            newStyle.glfont_align = scene.measureit_font_align
            newStyle.glfont_rotat = scene.measureit_font_rotation
            

            styleGen.style_num += 1
            context.area.tag_redraw()
            return {'FINISHED'}

        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}


class DeleteAllStylesButton(Operator):
    bl_idname = "measureit.deleteallstylesbutton"
    bl_label = "Delete"
    bl_description = "Delete all Styles (it cannot be undone)"
    bl_category = 'Measureit'
    tag= IntProperty()

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        if context.area.type == 'VIEW_3D':
            # Add properties
            scene =bpy.context.scene
            mainobject = context.object
            styleGen = scene.StyleGenerator[0]

            while len(styleGen.measureit_styles) > 0:
                styleGen.measureit_styles.remove(0)

            # reset size
            styleGen.style_num = len(styleGen.measureit_styles)
            # redraw
            context.area.tag_redraw()
            return {'FINISHED'}
        else:
            self.report({'WARNING'},
                        "View3D not found, cannot run operator")

        return {'CANCELLED'}



# -------------------------------------------------------------
# Handle all draw routines (OpenGL main entry point)
#
# -------------------------------------------------------------
def draw_main(context):
    region = bpy.context.region
    # Detect if Quadview to get drawing area
    if not context.space_data.region_quadviews:
        rv3d = bpy.context.space_data.region_3d
    else:
        # verify area
        if context.area.type != 'VIEW_3D' or context.space_data.type != 'VIEW_3D':
            return
        i = -1
        for region in context.area.regions:
            if region.type == 'WINDOW':
                i += 1
                if context.region.id == region.id:
                    break
        else:
            return

        rv3d = context.space_data.region_quadviews[i]

    scene = bpy.context.scene

    # Get visible collections
    viewLayer = bpy.context.view_layer

    visibleCollections = []

    for collection in viewLayer.layer_collection.children:
       if collection.exclude == False:
            visibleCollections.extend([collection])

    # Display selected or all
    if scene.measureit_gl_ghost is False:
        objlist = context.selected_objects
    else:
        objlist = context.scene.objects

    # Enable GL drawing
    #bgl.glEnable(bgl.GL_BLEND)
    # ---------------------------------------
    # Generate all OpenGL calls for measures
    # ---------------------------------------
    for myobj in objlist:
        if myobj.hide_viewport is False:
            if 'MeasureGenerator' in myobj:
                
                # verify visible layer
                for collection in visibleCollections:
                    objCollections = []
                    objCollections = myobj.users_collection
                    if objCollections[0].name == collection.collection.name:
                        op = myobj.MeasureGenerator[0]
                        draw_segments(context, myobj, op, region, rv3d)
                        break
    # ---------------------------------------
    # Generate all OpenGL calls for debug
    # ---------------------------------------
    if scene.measureit_debug is True:
        selobj = bpy.context.selected_objects
        for myobj in selobj:
            if scene.measureit_debug_objects is True:
                draw_object(context, myobj, region, rv3d)
            elif scene.measureit_debug_object_loc is True:
                draw_object(context, myobj, region, rv3d)
            if scene.measureit_debug_vertices is True:
                draw_vertices(context, myobj, region, rv3d)
            elif scene.measureit_debug_vert_loc is True:
                draw_vertices(context, myobj, region, rv3d)
            if scene.measureit_debug_edges is True:
                draw_edges(context, myobj, region, rv3d)
            if scene.measureit_debug_faces is True or scene.measureit_debug_normals is True:
                draw_faces(context, myobj, region, rv3d)

    # -----------------------
    # restore opengl defaults
    # -----------------------
    #bgl.glLineWidth(1)
    #bgl.glDisable(bgl.GL_BLEND)
    #bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


# -------------------------------------------------------------
# Handler for drawing OpenGl
# -------------------------------------------------------------
# noinspection PyUnusedLocal
def draw_callback_px(self, context):
    draw_main(context)


# -------------------------------------------------------------
# Check if the segment already exist
#
# -------------------------------------------------------------
def exist_segment(mp, pointa, pointb, typ=1, pointc=None):
    #  for ms in mp.measureit_segments[mp.measureit_num]
    for ms in mp.measureit_segments:
        if ms.gltype == typ and ms.glfree is False:
            if typ != 9:
                if ms.glpointa == pointa and ms.glpointb == pointb:
                    return True
                if ms.glpointa == pointb and ms.glpointb == pointa:
                    return True
            else:
                if ms.glpointa == pointa and ms.glpointb == pointb and ms.glpointc == pointc:
                    return True

    return False


# -------------------------------------------------------------
# Get vertex selected
# -------------------------------------------------------------
def get_selected_vertex(myobject):
    mylist = []
    # if not mesh, no vertex
    if myobject.type != "MESH":
        return mylist
    # --------------------
    # meshes
    # --------------------
    oldobj = bpy.context.object
    bpy.context.view_layer.objects.active = myobject
    flag = False
    if myobject.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
        flag = True

    bm = from_edit_mesh(myobject.data)
    tv = len(bm.verts)
    for v in bm.verts:
        if v.select:
            mylist.extend([v.index])

    if flag is True:
        bpy.ops.object.editmode_toggle()
    # Back context object
    bpy.context.view_layer.objects.active = oldobj

    # if select all vertices, then use origin
    if tv == len(mylist):
        return []

    return mylist


# -------------------------------------------------------------
# Get vertex selected
# -------------------------------------------------------------
def get_selected_vertex_history(myobject):
    mylist = []
    # if not mesh, no vertex
    if myobject.type != "MESH":
        return mylist
    # --------------------
    # meshes
    # --------------------
    oldobj = bpy.context.object
    bpy.context.view_layer.objects.active = myobject
    flag = False
    if myobject.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
        flag = True

    bm = from_edit_mesh(myobject.data)
    for v in bm.select_history:
        mylist.extend([v.index])

    if flag is True:
        bpy.ops.object.editmode_toggle()
    # Back context object
    bpy.context.view_layer.objects.active = oldobj

    return mylist


# -------------------------------------------------------------
# Get vertex selected segments
# -------------------------------------------------------------
def get_smart_selected(myobject):
    mylist = []
    # if not mesh, no vertex
    if myobject.type != "MESH":
        return mylist
    # --------------------
    # meshes
    # --------------------
    oldobj = bpy.context.object
    bpy.context.view_layer.objects.active = myobject
    flag = False
    if myobject.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
        flag = True

    bm = from_edit_mesh(myobject.data)
    for e in bm.edges:
        if e.select is True:
            mylist.extend([e.verts[0].index])
            mylist.extend([e.verts[1].index])

    if flag is True:
        bpy.ops.object.editmode_toggle()
    # Back context object
    bpy.context.view_layer.objects.active = oldobj

    return mylist


# -------------------------------------------------------------
# Get vertex selected faces
# -------------------------------------------------------------
def get_selected_faces(myobject):
    mylist = []
    # if not mesh, no vertex
    if myobject.type != "MESH":
        return mylist
    # --------------------
    # meshes
    # --------------------
    oldobj = bpy.context.object
    bpy.context.view_layer.objects.active = myobject
    flag = False
    if myobject.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')
        flag = True

    bm = from_edit_mesh(myobject.data)
    for e in bm.faces:
        myface = []
        if e.select is True:
            for i in range(0, len(e.verts)):
                myface.extend([e.verts[i].index])

            mylist.extend([myface])

    if flag is True:
        bpy.ops.object.editmode_toggle()
    # Back context object
    bpy.context.view_layer.objects.active = oldobj

    return mylist