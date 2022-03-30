from maya import cmds
import pymel.core as pm
from ..utils import QualityAssurance, reference


class FreezeTransforms(QualityAssurance):
    """
    Transforms will be checked to see if they have unfrozen attributes When
    fixing this error transforms will be frozen.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Freeze Transforms"
        self._message = "{0} transform(s) are not frozen"
        self._categories = ["Modelling"]
        self._selectable = True

        self._ignoreNodes = ["|persp", "|front", "|top", "|side"]

        self._attributes = [
            ".tx", "ty", "tz",
            ".rx", "ry", "rz",
            ".sx", "sy", "sz"
        ]
        self._values = [
            0, 0, 0,
            0, 0, 0,
            1, 1, 1
        ]

    # ------------------------------------------------------------------------

    @property
    def ignoreNodes(self):
        """
        :return: Nodes to ignore
        :rtype: list
        """
        return self._ignoreNodes

    @property
    def defaultState(self):
        """
        :return: Default state of attributes with values
        :rtype: list
        """
        return zip(self._attributes, self._values)

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Unfrozen transforms
        :rtype: generator
        """
        transforms = self.ls(transforms=True, l=True)
        transforms = reference.removeReferenced(transforms)

        for transform in transforms:
            if transform in self.ignoreNodes:
                continue

            for attr, value in self.defaultState:
                if not cmds.objExists(transform + attr):
                    continue

                if cmds.getAttr(transform + attr) != value:
                    yield transform

    def _fix(self, transform):
        """
        :param str transform:
        """
        cmds.makeIdentity(
            transform,
            apply=True,
            translate=True,
            rotate=True,
            scale=True
        )


class DeleteHistory(QualityAssurance):
    """
    Mesh shapes will be checked to see if they have history attached to them.
    When fixing this error the history will be deleted.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "History"
        self._message = "{0} mesh(es) contain history nodes"
        self._categories = ["Modelling"]
        self._selectable = True

        self._ignoreNodes = [
            "tweak", "groupParts", "groupId",
            "shape", "shadingEngine", "mesh"
        ]


    # ------------------------------------------------------------------------

    @property
    def ignoreNodes(self):
        """
        :return: Nodes to ignore
        :rtype: list
        """
        return self._ignoreNodes

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Meshes with history
        :rtype: generator
        """

        meshes = self.ls(type="mesh", l=True)
        meshes = reference.removeReferenced(meshes)

        for mesh in meshes:
            history = cmds.listHistory(mesh) or []
            types = [cmds.nodeType(h) for h in history]

            for t in types:
                if t in self.ignoreNodes:
                    continue

                yield mesh
                break

    def _fix(self, mesh):
        """
        :param str mesh:
        """
        cmds.delete(mesh, ch=True)


class DeleteAnimation(QualityAssurance):
    """
    All animation curves will be added to the error list. When fixing this
    error the animation curves will be deleted
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Animation"
        self._message = "{0} animation curve(s) in the scene"
        self._categories = ["Modelling"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Animation curves
        :rtype: generator
        """

        animCurves = self.ls(type="animCurve")
        animCurves = reference.removeReferenced(animCurves)

        for animCurve in animCurves:
            yield animCurve

    def _fix(self, animCurve):
        """
        :param str animCurve:
        """
        cmds.delete(animCurve)

class NoNamespace(QualityAssurance):
    """Ensure the nodes don't have a namespace"""
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "No Namespaces"
        self._message = "{0} Namespaces found"
        self._categories = ["Modelling"]
        self._selectable = False

    def get_namespace(self,node_name):
        # ensure only node's name (not parent path)
        node_name = node_name.rsplit("|")[-1]
        # ensure only namespace
        return node_name.rpartition(":")[0]

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: list of namespaces
        :rtype: generator
        """

        nodes = cmds.ls(long=True)
        for node in nodes:
            if self.get_namespace(node): yield node
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
        if len(namespaces) > 2:
            #default namespace components cant be merged back
            namespaces.remove('UI')
            namespaces.remove('shared')
            for nspace in namespaces:
                yield nspace

    def _fix(self,node):
        """
        :param str animCurve:
        """
        nodes = cmds.ls(long=True)
        spacesNodes = [node for node in nodes if self.get_namespace(node)]
        nodes = pm.ls(spacesNodes)
        for node in nodes:
            namespace = node.namespace()
            if namespace:
                name = node.nodeName()
                node.rename(name[len(namespace):])
        namespaces = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True)
        if 'UI' in namespaces or 'shared' in namespaces:
            namespaces.remove('UI')
            namespaces.remove('shared')
        for nspace in namespaces:
            cmds.namespace( removeNamespace=nspace, mergeNamespaceWithRoot=True)
class UVSetMap1(QualityAssurance):
    """Ensure meshes have the default UV set"""
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "has UV set map1"
        self._message = "{0} mesh has map1 renamed and must be fixed"
        self._categories = ["Modelling"]
        self._selectable = False
    # ------------------------------------------------------------------------
    def _find(self):
        """
        :return: list of meshes without map1 uv set
        :rtype: generator
        """
        meshes = cmds.ls(type='mesh', long=True)

        invalid = []
        for mesh in meshes:

            # Get existing mapping of uv sets by index
            indices = cmds.polyUVSet(mesh, query=True, allUVSetsIndices=True)
            maps = cmds.polyUVSet(mesh, query=True, allUVSets=True)
            mapping = dict(zip(indices, maps))

            # Get the uv set at index zero.
            name = mapping[0]
            if name != "map1":
                yield mesh


    def _fix(self, mesh):
        """
        :param str animCurve:
        """
        print(mesh)
        # Get existing mapping of uv sets by index
        indices = cmds.polyUVSet(mesh, query=True, allUVSetsIndices=True)
        maps = cmds.polyUVSet(mesh, query=True, allUVSets=True)
        mapping = dict(zip(indices, maps))

        # Ensure there is no uv set named map1 to avoid
        # a clash on renaming the "default uv set" to map1
        existing = set(maps)
        if "map1" in existing:
            print('existing')
            # Find a unique name index
            i = 2
            while True:
                name = "map{0}".format(i)
                if name not in existing:
                    break
                i += 1

            cmds.polyUVSet(mesh,
                            rename=True,
                            uvSet="map1",
                            newUVSet=name)

        # Rename the initial index to map1
        original = mapping[0]
        cmds.polyUVSet(mesh,
                        rename=True,
                        uvSet=original,
                        newUVSet="map1")
class TransformSuffix(QualityAssurance):
    """Validates transform suffix based on the type of its children shapes.

    Suffices must be:
        - mesh:
            _GEO (regular geometry)
            _GES (geometry to be smoothed at render)
            _GEP (proxy geometry; usually not to be rendered)
            _OSD (open subdiv smooth at rendertime)
        - nurbsCurve: _CRV
        - nurbsSurface: _NRB
        - locator: _LOC
        - null/group: _GRP

    .. warning::
        This grabs the first child shape as a reference and doesn't use the
        others in the check.

    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Transform Suffix Naming Convention"
        self._message = "{0} Transforms with wrong naming"
        self._categories = ["Modelling"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: list of namespaces
        :rtype: generator
        """
        SUFFIX_NAMING_TABLE = {'mesh': ["_GEO", "_GES", "_GEP", "_OSD"],
                           'nurbsCurve': ["_CRV"],
                           'nurbsSurface': ["_NRB"],
                           'locator': ["_LOC"],
                           None: ['_GRP']}

        ALLOW_IF_NOT_IN_SUFFIX_TABLE = True
        transforms = cmds.ls(sl=self._selectable,type='transform', long=True)
        for transform in transforms:
            shapes = cmds.listRelatives(transform,
                                        shapes=True,
                                        fullPath=True,
                                        noIntermediate=True)

            shape_type = cmds.nodeType(shapes[0]) if shapes else None

            if shape_type in SUFFIX_NAMING_TABLE:
                suffices = SUFFIX_NAMING_TABLE[shape_type]
                for suffix in suffices:
                    if not transform.upper().endswith(suffix.upper()):
                        yield transform



    def _fix(self,transforms):
        """
        :param str transform:
        cant fix automatically because its impossible to know what specifically is wrong
        """
        print(" Incorrectly named transforms, please fix: " + transforms)
