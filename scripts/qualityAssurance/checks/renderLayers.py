from maya import cmds
from ..utils import QualityAssurance, reference
import re

class MissingAdjustments(QualityAssurance):
    """
    The scene will be processed for missing renderlayer adjustments. When
    fixing these errors the missing adjustments will be reconnected.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Missing Adjustments"
        self._message = "{0} missing renderlayer adjustment(s)"
        self._categories = ["Render Layers"]
        self._selectable = False

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Missing adjustments
        :rtype: generator
        """
        renderlayers = self.ls(type="renderLayer")
        renderlayers = reference.removeReferenced(renderlayers)

        # get current layer
        currentlayer = cmds.editRenderLayerGlobals(
            query=True,
            currentRenderLayer=True
        )

        for renderlayer in renderlayers:
            # skip if its a default layer.
            # default layers don't have render layer overrides.
            if renderlayer.count("defaultRenderLayer"):
                continue

            # get adjustment connections
            connections = cmds.listConnections(
                "{0}.outAdjustments".format(renderlayer),
                d=0,
                c=1,
                p=1
            ) or []

            # create adjustment connections iterator
            connectionsIter = iter(connections)

            # iterate adjustment connections
            for adjPlug in connectionsIter:
                adjValue = adjPlug.replace("outPlug", "outValue")
                scnPlug = connectionsIter.next()

                dsgPlugs = cmds.connectionInfo(adjValue, dfs=True)

                if dsgPlugs:
                    continue

                scnPlugParent = ""
                scnParentDstPlugs = []

                scnPlug = cmds.connectionInfo(scnPlug, ges=True)
                scnDstPlug = cmds.connectionInfo(scnPlug, dfs=True)

                if scnPlug.count("objectGroups"):
                    scnPlugParent = scnPlug.rsplit(".", 1)[0]
                    scnParentDstPlugs = cmds.connectionInfo(
                        scnPlugParent,
                        dfs=True
                    )

                SG = None
                parentSG = None
                parentsSGPlug = None

                defaultSG = "initialShadingGroup"

                # get (default) shading group
                for scnParentDstPlug in scnParentDstPlugs:
                    node = scnParentDstPlug.split(".")[0]
                    if cmds.nodeType(node) == "shadingEngine":
                        SG = node
                    elif (
                        node == "defaultRenderLayer"
                        and renderlayer != "defaultRenderLayer"
                    ):
                        defaultAdjValue = scnParentDstPlug.replace(
                            "outValue",
                            "outPlug"
                        )
                        defaultDsgPlugs = cmds.connectionInfo(
                            defaultAdjValue,
                            dfs=True
                        )

                        if defaultDsgPlugs:
                            defaultSG = defaultDsgPlugs[0].split(".")[0]

                # get parent shading group and plug
                if not SG:
                    for scnParentDstPlug in scnParentDstPlugs:
                        node = scnParentDstPlug.split(".")[0]
                        if cmds.nodeType(node) == "shadingEngine":
                            parentSG = node
                            parentSGPlug = scnParentDstPlug
                            break

                # if we are on the curent render layer
                if renderlayer == currentlayer and not SG:
                    if not parentSG:
                        yield [
                            scnPlug,
                            "{0}.dagSetMembers".format(defaultSG)
                        ]
                    else:
                        yield [
                            scnPlug,
                            "{0}.dagSetMembers".format(parentSG),
                            scnPlugParent,
                            parentSGPlug
                        ]

                # determine shader group to connect adjustment value
                if not SG:
                    if not parentSG:
                        SG = defaultSG
                    else:
                        SG = parentSG

                yield [
                    adjValue,
                    "{0}.dagSetMembers".format(SG),
                    scnPlugParent,
                    parentSGPlug
                ]

    def _fix(self, data):
        """
        :param list data:
        """
        if len(data) == 4:
            cmds.disconnectAttr(data[2], data[3])

        cmds.connectAttr(data[0], data[1], na=True, force=True)


class DuplicateAdjustments(QualityAssurance):
    """
    The scene will be processed for duplicate renderlayer adjustments. When
    fixing these errors the duplicate adjustments will be removed.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Duplicate Adjustments"
        self._message = "{0} duplicate renderlayer adjustment(s)"
        self._categories = ["Render Layers"]
        self._selectable = False

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Duplicate adjustments
        :rtype: generator
        """
        renderlayers = self.ls(type="renderLayer")
        renderlayers = reference.removeReferenced(renderlayers)

        for renderlayer in renderlayers:
            # skip if its a default layer.
            # default layers don't have render layer overrides.
            if renderlayer.count("defaultRenderLayer"):
                continue

            # get adjustment connections
            connections = cmds.listConnections(
                "{0}.outAdjustments".format(renderlayer),
                d=0,
                c=1,
                p=1
            ) or []

            # split adjustments into source and destimation
            source = connections[0::2]
            destination = connections[1::2]

            for i, (s1, d1) in enumerate(zip(source, destination)):
                for s2, d2 in zip(source[i+1:], destination[i+1:]):
                    if d1 == d2:
                        yield [d1, s1]

    def _fix(self, data):
        """
        :param list data:
        """
        # split data
        d1, s1 = data

        # disconnect plug connections
        cmds.disconnectAttr(d1, s1)

        # disconnection value connection
        plug = s1.replace("outPlug", "outValue")
        other = cmds.connectionInfo(plug, dfs=True)
        cmds.disconnectAttr(plug, other[0])


class MismatchedAdjustments(QualityAssurance):
    """
    The scene will be processed for mismatched renderlayer adjustments. When
    fixing these errors the mismatched adjustments will be reconnected.
    """
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Mismatched Adjustments"
        self._message = "{0} mismatched renderlayer adjustment(s)"
        self._categories = ["Render Layers"]
        self._selectable = False

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Mismatched adjustments
        :rtype: generator
        """
        # clean references
        references = cmds.ls(type="reference")
        for reference in references:
            if (
                reference.count("sharedReferenceNode")
                or not cmds.referenceQuery(reference, isLoaded=True)
            ):
                continue

            cmds.file(cleanReference=reference)

        # get renderlayers
        renderlayers = self.ls(type="renderLayer")
        currentlayer = cmds.editRenderLayerGlobals(query=True, currentRenderLayer=True)

        # set current renderlayer to be first
        renderlayers.remove(currentlayer)
        renderlayers.insert(0, currentlayer)

        for renderlayer in renderlayers:
            # skip default renderlayers
            if renderlayer.count("defaultRenderLayer"):
                continue

            # get shading group overrides
            sgOverrides = cmds.listConnections(
                "{0}.shadingGroupOverride".format(renderlayer),
                type="shadingEngine",
                s=1,
                d=0
            )

            # set current renderlayer
            cmds.editRenderLayerGlobals(currentRenderLayer=renderlayer)

            # get adjustment connections
            connections = cmds.listConnections(
                "{0}.outAdjustments".format(renderlayer),
                d=0,
                c=1,
                p=1
            ) or []

            # iterate adjustment connections
            connectionsIter = iter(connections)

            # loop connections
            for adjPlug in connectionsIter:
                adjValue = adjPlug.replace("outPlug", "outValue")
                scnPlug = connectionsIter.next()

                dsgPlugs = cmds.connectionInfo(adjValue, dfs=True)
                if not dsgPlugs:
                    continue

                SG = dsgPlugs[0].split(".")[0]
                if sgOverrides:
                    SG = sgOverrides[0]

                nodeType = cmds.nodeType(SG)
                if nodeType != "shadingEngine":
                    continue

                scnPlugParent = ""
                scnParentDstPlugs = []

                scnPlug = cmds.connectionInfo(scnPlug, ges=True)
                scnDstPlugs = cmds.connectionInfo(scnPlug, dfs=True)

                if scnPlug.find("objectGroups") != -1:
                    scnPlugParent = scnPlug.rsplit(".", 1)[0]
                    scnParentDstPlugs = cmds.connectionInfo(
                        scnPlugParent,
                        dfs=True
                    )

                # find error in destination plugs
                isFinished = False
                for scnDstPlug in scnDstPlugs:
                    node = scnDstPlug.split(".")[0]
                    if cmds.nodeType(node) == "shadingEngine":
                        if SG != node:
                            yield [
                                adjValue,
                                "{0}.dagSetMembers".format(node),
                                adjValue,
                                dsgPlugs[0]
                            ]

                        isFinished = True
                        break

                # if finished continue to next
                if isFinished:
                    continue

                # find error in parent destination plugs
                for scnParentDstPlug in scnParentDstPlugs:
                    node = scnParentDstPlug.split(".")[0]
                    if cmds.nodeType(node) == "shadingEngine":
                        if SG != node:
                            yield [
                                adjValue,
                                "{0}.dagSetMembers".format(node),
                                adjValue,
                                dsgPlugs[0]
                            ]

                        yield [
                            scnPlug,
                            "{0}.dagSetMembers".format(node),
                            scnPlugParent,
                            scnParentDstPlug
                        ]

        cmds.editRenderLayerGlobals(currentRenderLayer=currentlayer)

    def _fix(self, data):
        """
        :param list data:
        """
        # split data
        conSource, conDestination, delSource, delDestination = data

        # fix connections
        cmds.disconnectAttr(delSource, delDestination)
        cmds.connectAttr(conSource, conDestination, na=True, force=True)

#HORNET - new checks
class ValidateDisplacement(QualityAssurance):
    """Makes sure 'Ignore Displacement' is not checked in the feature overrides"""
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Displacement not ignored in Arnold Render"
        self._message = ""
        self._categories = ["Render Layers"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: Duplicate adjustments
        :rtype: generator
        """
        disp = cmds.getAttr("defaultArnoldRenderOptions.ignoreDisplacement")
        if disp == 1:
            yield "Displacement set to Ignore !"


    def _fix(self, data):
        disp = cmds.setAttr("defaultArnoldRenderOptions.ignoreDisplacement", 1)

class CheckMergeAOVs(QualityAssurance):
    """Makes sure 'Ignore Displacement' is not checked in the feature overrides"""
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "merge AOVs must be checked"
        self._message = "merge AOVs not checked"
        self._categories = ["Render Layers"]
        self._selectable = False

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: bool mergeAOVs
        :rtype: generator
        """
        merge = cmds.getAttr('defaultArnoldDriver.mergeAOVs')
        if merge == 0:
            yield "merge AOVs not checked"


    def _fix(self, data):
        cmds.setAttr('defaultArnoldDriver.mergeAOVs',1)
class SingleCamera(QualityAssurance):
    """Validate renderable camera count for layer and <Camera> token."""
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Render Single Camera"
        self._message = "{0} renderable cameras per layer"
        self._categories = ["Render Layers"]
        self._selectable = False
        self._urgency = 1
        self.ImagePrefixes = {
            'mentalray': 'defaultRenderGlobals.imageFilePrefix',
            'vray': 'vraySettings.fileNamePrefix',
            'arnold': 'defaultRenderGlobals.imageFilePrefix',
            'renderman': 'defaultRenderGlobals.imageFilePrefix',
            'redshift': 'defaultRenderGlobals.imageFilePrefix'
        }
        self.R_CAMERA_TOKEN = re.compile(r'%c|<camera>', re.IGNORECASE)

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: extra cameras
        :rtype: generator
        """
        self._message = "{0} renderable cameras"
        cameras = [c for c in cmds.ls(cameras=True) if not cmds.camera(c, q=True, startupCamera=True)]
        renderer = cmds.getAttr('defaultRenderGlobals.currentRenderer').lower()
        # handle various renderman names
        if renderer.startswith('renderman'):
            renderer = 'renderman'
        file_prefix = cmds.getAttr(self.ImagePrefixes[renderer]) or ''

        if len(cameras) > 1:
            if not re.search(self.R_CAMERA_TOKEN, file_prefix):
                # if there is <Camera> token in prefix and we have more then
                # 1 camera, all is ok.
                for camera in cameras:
                    yield camera
            print("Multiple renderable cameras found for %s:  \n\
                If only one camera is desired \
                please set render camera in Deadline Submitter" %
                cameras)
        elif len(cameras) < 1:
            self._message = "no renderable camera found"
            yield "no renderable camera found"
class Subdivision(QualityAssurance):
    """Makes sure 'Ignore Subdivision' is not checked in the feature overrides"""
    def __init__(self):
        QualityAssurance.__init__(self)

        self._name = "Not Ignoring Subdivision"
        self._message = "ignore subdiv set to {0} should be 0 "
        self._categories = ["Render Layers"]
        self._selectable = True

    # ------------------------------------------------------------------------

    def _find(self):
        """
        :return: extra cameras
        :rtype: generator
        """
        subdiv = cmds.getAttr("defaultArnoldRenderOptions.ignoreSubdivision")
        if subdiv == 1:
            yield subdiv
    def _fix(self):
        cmds.setAttr("defaultArnoldRenderOptions.ignoreSubdivision", 0)
