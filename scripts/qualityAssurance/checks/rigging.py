from maya import cmds
from ..utils import QualityAssurance, reference


class DeleteNonDeformerHistory(QualityAssurance):
    """
    Meshes will be checked to see if they contain non-deformer history. Be
    carefull with this ceck as it is not always nessecary to fix this. History
    is not always a bad thing. When fixing this error the partial history will
    be baked.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Non Deformer History"
        self._message = "{0} mesh(es) contain non-deformer history nodes"
        self._categories = ["Rigging"]
        self._selectable = True

        self._ignoreNodeTypes = [
            "geometryFilter", "tweak", "groupParts",
            "groupId", "shape", "dagPose",
            "joint", "shadingEngine", "cluster",
            "transform", "diskCache", "time"
        ]

    # ------------------------------------------------------------------------

    @property
    def ignoreNodeTypes(self):
        return self._ignoreNodeTypes

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Meshes with non-deformer history
        :rtype: generator
        """
        meshes = self.ls(type="mesh")
        meshes = reference.removeReferenced(meshes)

        for mesh in meshes:
            history = cmds.listHistory(mesh)
            deformers = cmds.ls(history, type=self.ignoreNodeTypes)

            if len(history) != len(deformers):
                yield mesh

    def _fix(self, mesh):
        """
        :param str mesh:
        """
        cmds.bakePartialHistory(mesh, prePostDeformers=True)


class DeleteNonSetDrivenAnimation(QualityAssurance):
    """
    Animation curves will be checked to see if they are not set driven keys.
    Non set driven keys should not be present in the scene and will be deleted
    when fixing this error.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Non Set-Driven Animation"
        self._message = "{0} non set-driven animation curve(s) in the scene"
        self._categories = ["Rigging"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Non set driven key animation curves
        :rtype: generator
        """
        animCurves = self.ls(type="animCurve")
        animCurves = reference.removeReferenced(animCurves)

        for animCurve in animCurves:
            if not cmds.listConnections("{0}.input".format(animCurve)):
                yield animCurve

    def _fix(self, animCurve):
        """
        :param str animCurve:
        """
        cmds.delete(animCurve)

class ControlSets(QualityAssurance):
    """Validate rig controllers.

    Controls must have the transformation attributes on their default
    values of translate zero, rotate zero and scale one when they are
    unlocked attributes.

    Unlocked keyable attributes may not have any incoming connections. If
    these connections are required for the rig then lock the attributes.

    The visibility attribute must be locked.

    Note that `repair` will:
        - Lock all visibility attributes
        - Reset all default values for translate, rotate, scale
        - Break all incoming connections to keyable attributes

    """
    def __init__(self):
        QualityAssurance.__init__(self)
        self._name = "Control Sets layout"
        self._message = "{0} sets misconfigured"
        self._categories = ["Rigging"]
        self._selectable = False
        # Default controller values
        CONTROLLER_DEFAULTS = {
            "translateX": 0,
            "translateY": 0,
            "translateZ": 0,
            "rotateX": 0,
            "rotateY": 0,
            "rotateZ": 0,
            "scaleX": 1,
            "scaleY": 1,
            "scaleZ": 1
        }
    def _find(cls):

        controllers_sets = [i for i in cmds.ls(sets=True) if i == "controls_SET"]
        controls = cmds.sets(controllers_sets, query=True)
        if controls:
            print("control sets cant be on top level of outliner, must be child of the rig instance, and all controls must be in the rig's group")
            yield controls

    def get_non_default_attributes(self, control):
        """Return attribute plugs with non-default values

        Args:
            control (str): Name of control node.

        Returns:
            list: The invalid plugs

        """

        invalid = []
        for attr, default in self.CONTROLLER_DEFAULTS.items():
            if cmds.attributeQuery(attr, node=control, exists=True):
                plug = "{}.{}".format(control, attr)

                # Ignore locked attributes
                locked = cmds.getAttr(plug, lock=True)
                if locked:
                    continue

                value = cmds.getAttr(plug)
                if value != default:
                    print("Control non-default value: "
                                    "%s = %s" % (plug, value))
                    invalid.append(plug)

        return invalid
    def get_connected_attributes(self,control):
        """Return attribute plugs with incoming connections.

        This will also ensure no (driven) keys on unlocked keyable attributes.

        Args:
            control (str): Name of control node.

        Returns:
            list: The invalid plugs

        """
        import maya.cmds as mc

        # Support controls without any attributes returning None
        attributes = mc.listAttr(control, keyable=True, scalar=True) or []
        invalid = []
        for attr in attributes:
            plug = "{}.{}".format(control, attr)

            # Ignore locked attributes
            locked = cmds.getAttr(plug, lock=True)
            if locked:
                continue

            # Ignore proxy connections.
            if cmds.addAttr(plug, query=True, usedAsProxy=True):
                continue

            # Check for incoming connections
            if cmds.listConnections(plug, source=True, destination=False):
                invalid.append(plug)

        return invalid

class ControlSetsArnold(QualityAssurance):
    """Validate rig control curves have no keyable arnold attributes.

    The Arnold plug-in will create curve attributes like:
        - aiRenderCurve
        - aiCurveWidth
        - aiSampleRate
        - aiCurveShaderR
        - aiCurveShaderG
        - aiCurveShaderB

    Unfortunately these attributes visible in the channelBox are *keyable*
    by default and visible in the channelBox. As such pressing a regular "S"
    set key shortcut will set keys on these attributes too, thus cluttering
    the animator's scene.

    This validator will ensure they are hidden or unkeyable attributes.

    """
    order = pype.api.ValidateContentsOrder + 0.05
    label = "Rig Controllers (Arnold Attributes)"
    hosts = ["maya"]
    families = ["rig"]
    actions = [pype.api.RepairAction,
               pype.hosts.maya.action.SelectInvalidAction]

    attributes = [
        "rcurve",
        "cwdth",
        "srate",
        "ai_curve_shaderr",
        "ai_curve_shaderg",
        "ai_curve_shaderb"
    ]
    def __init__(self):
        QualityAssurance.__init__(self)
        self._name = "Control Sets Arnold Attributes"
        self._message = "{0} sets with curve attributes"
        self._categories = ["Rigging"]
        self._selectable = False
    def _find(self):
        controllers_sets = [i for i in cmds.ls(sets=True) if i == "controls_SET"]
        if not controllers_sets:
            yield []

        controls = cmds.sets(controllers_sets, query=True) or []
        if not controls:
            yield []

        shapes = cmds.ls(controls,
                         dag=True,
                         leaf=True,
                         long=True,
                         shapes=True,
                         noIntermediate=True)
        curves = cmds.ls(shapes, type="nurbsCurve", long=True)

        invalid = list()
        for node in curves:

            for attribute in cls.attributes:
                if cmds.attributeQuery(attribute, node=node, exists=True):
                    plug = "{}.{}".format(node, attribute)
                    if cmds.getAttr(plug, keyable=True):
                        invalid.append(node)
                        break

        yield invalid

    def _fix(cls, instance):

        invalid = self._find()
        with lib.undo_chunk():
            for node in invalid:
                for attribute in cls.attributes:
                    if cmds.attributeQuery(attribute, node=node, exists=True):
                        plug = "{}.{}".format(node, attribute)
                        cmds.setAttr(plug, channelBox=False, keyable=False)
