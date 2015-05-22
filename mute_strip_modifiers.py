"""
Mute/unmute all VSE strip modifiers at once, to speed up viewing.
"""
import bpy
import os
import subprocess

bl_info = {
    "name": "Mute Strip Modifiers",
    "description": "Mute / Unmute VSE strip modifiers",
    "author": "Joe Button",
    "version": (1, 0),
    "blender": (2, 73, 0),
    "location": "Sequencer",
    "warning": "Highly sketchy",
    "wiki_url": "",
    "category": "Sequencer"
}


class MuteStripModifiers(bpy.types.Operator):
    """Mute / Unmute VSE strip modifiers"""
    bl_idname = "vse.mutestripmodifiers"
    bl_label = "Mute Strip Modifiers"

    def execute(self, context):
        dest_state = None
        for s in context.scene.sequence_editor.sequences_all:
            for m in s.modifiers:
                if dest_state is None:
                    dest_state = not m.mute
                m.mute = dest_state
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(MuteStripModifiers.bl_idname)


def register():
    bpy.utils.register_class(MuteStripModifiers)
    bpy.types.SEQUENCER_MT_strip.append(menu_func)


def unregister():
    bpy.utils.unregister_class(MuteStripModifiers)


if __name__ == "__main__":
    register()
