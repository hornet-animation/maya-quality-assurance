"""
New collections can be added in the COLLECTIONS variable. Since this 
COLLECTIONS variable is an OrderedDict, it will keep the order. A 
collection can be defined by who will be using it. Currently it is
divided by different specialties. Each specialty contains a list of 
categories that will be displayed. The category names link to the categories
defined in the quality assurance checks themselves. 
"""
from collections import OrderedDict


COLLECTION = OrderedDict(
    [
        (
            "ANIM", [
                "Scene",
                "Animation",
                "Scene"
            ]
        ),
        (
            "MDL", [
                "Scene",
                "Modelling",
                "Geometry",
                "UV",
                "Shaders",
                "Render Stats"
            ]
        ),
        (
            "RIG", [
                "Scene",
                "Rigging",
                "Skinning",
                "Shaders",
                "Render Stats"
            ]
        ),
        (
            "SHD", [
                "Scene",
                "Shaders",
                "Textures",
                "UV",
                "Render Stats"
            ]
        ),
        (
            "LGT Arnold", [
                "Scene",
                "Arnold",
                "Textures"
            ]
        )
    ]
)


def getCollectionsCategories():
    """
    :return: List of all collection names
    :rtype: list
    """
    return COLLECTION.keys()


def getCollections():
    """
    :return: Collection overview
    :rtype: OrderedDict
    """
    return COLLECTION
