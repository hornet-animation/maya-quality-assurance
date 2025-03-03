from . import utils, widgets
from .. import collections
import os

class QualityAssuranceWindow(utils.QWidget):
    def __init__(self, parent, collection):
        utils.QWidget.__init__(self, parent)

        # set ui
        self.setParent(parent)
        self.setWindowFlags(utils.Qt.Window)

        self.setWindowTitle("Quality Assurance")
        self.setWindowIcon(
            utils.QIcon(utils.getIconPath("QA_icon.png"))
        )
        self.resize(700, 700)
        overview = collections.getCollectionsCategories()
        if os.environ['AVALON_TASK'] and os.environ['AVALON_TASK'] in overview:
            collection = os.environ['AVALON_TASK']

        # create layout
        layout = utils.QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # add collections
        self.collections = widgets.CollectionsWidget(self, collection)
        layout.addWidget(self.collections)

        # add container
        self.container = widgets.QualityAssuranceWidget(self, collection)
        layout.addWidget(self.container)

        # connections
        self.collections.currentIndexChanged.connect(self.container.refresh)


def show(collection="MDL",autorun=False):
    qa = QualityAssuranceWindow(utils.mayaWindow(), collection)
    qa.show()
    if autorun:
        qa.container.doFindAll()
