import typing
import unittest
import weakref
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
from typing import Callable

import numpy as np
import slicer
import vtk
from slicer.ScriptedLoadableModule import ScriptedLoadableModule
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleWidget
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleLogic
from slicer.ScriptedLoadableModule import ScriptedLoadableModuleTest
from slicer.util import VTKObservationMixin


class MarkupConstraints(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)

        parent.title = "Markup Constraints"
        parent.categories = ["Developer Tools"]
        parent.dependencies = ["Markups"]
        parent.contributors = ["David Allemang (Kitware Inc.)"]
        parent.helpText = """
        Markup Constraints is a collection of utilities to constrain the
        positions of markup control points based on the positions of other
        control points or models in the scene.
        """
        parent.acknowledgementText = """
        This work was supported by the National Institute of Dental and
        Craniofacial Research and the National Institute of Biomedical
        Imaging and Bioengineering of the National Institutes of Health.
        """
        self.parent = parent


class MarkupConstraintsWidget(ScriptedLoadableModuleWidget):
    pass


class ControlPoint:
    def __init__(self, node: "slicer.vtkMRMLMarkupsNode", id_: str):
        self.node = node
        self.id = id_

    @property
    def idx(self):
        return self.node.GetNthControlPointIndexByID(self.id)

    @property
    def position(self) -> Tuple[float, float, float]:
        return self.node.GetNthControlPointPositionWorld(self.idx)

    @position.setter
    def position(self, pos):
        if pos is None:
            self.node.UnsetNthControlPointPosition(self.idx)
        else:
            mode = self.node.GetNthControlPointPositionStatus(self.idx)
            self.node.SetNthControlPointPositionWorld(self.idx, pos, mode)

    @property
    def label(self):
        return self.node.GetNthControlPointLabel(self.idx)

    @label.setter
    def label(self, value):
        self.node.SetNthControlPointLabel(self.idx, value)

    @property
    def description(self):
        return self.node.GetNthControlPointDescription(self.idx)

    @description.setter
    def description(self, value):
        self.node.SetNthControlPointDescription(self.idx, value)

    @property
    def visibility(self):
        return self.node.GetNthControlPointVisibility(self.idx)

    @visibility.setter
    def visibility(self, value):
        self.node.SetNthControlPointVisibility(self.idx, value)

    @property
    def exists(self):
        return self.idx >= 0

    def setLocked(self, locked):
        self.node.SetNthControlPointLocked(self.idx, locked)

    @classmethod
    def new(cls, node: "slicer.vtkMRMLMarkupsNode", pos=(0, 0, 0)):
        idx = node.AddControlPoint(vtk.vtkVector3d())
        id_ = node.GetNthControlPointID(idx)
        cp = cls(node, id_)
        cp.position = pos
        return cp

    def __bool__(self):
        return self.exists

# Todo expand API via abstract class.
Constraint: Callable[[ControlPoint, ...], None]


class NodeAdaptor:
    """Adapts any vtkObject by handling ModifiedEvent."""

    def __init__(self):
        self._observers = {}  # {item: tag}

    def wrap(self, item, method):
        def wrapped(obj, event):
            with slicer.util.NodeModify(obj):
                return method(item, event)

        return wrapped

    def getVtkObject(self, item):
        return item

    def events(self):
        return vtk.vtkCommand.ModifiedEvent,

    def is_valid(self, item):  # todo generic type hints
        # used to detect ex. a deleted control point
        return True

    def addObservers(self, item, method, priority=0.0):
        events = self.events()

        if item in self._observers:
            return

        wrapped = self.wrap(item, method)
        obj = self.getVtkObject(item)
        tags = [obj.AddObserver(event, wrapped, priority) for event in events]

        self._observers[item] = obj, tags

    def delObservers(self, item):
        if item not in self._observers:
            return

        obj, tags = self._observers.pop(item)

        for tag in tags:
            obj.RemoveObserver(tag)


class TransformableNodeAdaptor(NodeAdaptor):
    """Adaptor for vtkMRMLTransformableNode; also observes TransformModifiedEvent."""

    def events(self):
        # todo generator
        #  yield from super().events()
        #  yield slicer.vtkMRMLTransformableNode.TransformModifiedEvent
        return super().events() + (
            slicer.vtkMRMLTransformableNode.TransformModifiedEvent,
        )


class ControlPointAdaptor(NodeAdaptor):
    """Adapts a single control point in a markup node.
    Observers are only invoked if the particular control point is modified, handled by
    caching the positions of observed control points.
    """

    _cache: weakref.WeakKeyDictionary[ControlPoint, Tuple[str, Tuple[float, float, float]]]

    def __init__(self):
        super().__init__()

        self._cache = weakref.WeakKeyDictionary()

    def events(self):
        return (
            slicer.vtkMRMLMarkupsNode.PointAddedEvent,
            slicer.vtkMRMLMarkupsNode.PointModifiedEvent,
            slicer.vtkMRMLMarkupsNode.PointRemovedEvent,
        )

    def wrap(self, item: ControlPoint, method):
        def wrapped(obj, event):
            with slicer.util.NodeModify(obj):
                label, position = self._cache.get(item, (None, None))

                if item in self._cache and label == item.label and np.allclose(position, item.position):
                    return None

                method(item, event)

                self._cache[item] = item.label, item.position

        return wrapped

    def getVtkObject(self, item):
        return item.node

    def is_valid(self, item: ControlPoint):
        return item.exists


class MarkupConstraintsLogic(
    ScriptedLoadableModuleLogic,
    VTKObservationMixin,
):
    _registry = {}

    _adaptors = {
        vtk.vtkObject: NodeAdaptor(),
        slicer.vtkMRMLTransformableNode: TransformableNodeAdaptor(),
        ControlPoint: ControlPointAdaptor(),
    }

    _constraints: Dict[ControlPoint, Tuple[str, Tuple, Tuple]]
    _dependencies: weakref.WeakKeyDictionary[ControlPoint, List[ControlPoint]]

    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)
        VTKObservationMixin.__init__(self)

        self._constraints = {}
        # {target: (kind, args, extras)}
        # used to track how each target is constrained

        self._dependencies = weakref.WeakKeyDictionary()
        # {arg: [*targets]}}
        # used to determine the points to update after a given point is moved

    @classmethod
    def adaptor(cls, item) -> NodeAdaptor:
        typ = type(item)
        bases = typ.__mro__
        for base in bases:
            if base in cls._adaptors:
                return cls._adaptors[base]
        raise TypeError(f"Missing adaptor for {typ!r} with bases {bases}")

    def _onModify(self, item, event):
        to_remove = []

        for target in self._dependencies[item]:
            adaptor = self.adaptor(target)
            if not adaptor.is_valid(target):
                to_remove.append(target)
            else:
                kind, args, extras = self._constraints[target]
                func = self._registry[kind]
                func(target, *args)

        for target in to_remove:
            self.delConstraint(target)

    def setConstraint(
        self,
        target: ControlPoint,
        kind: str,
        *args: Union[ControlPoint, Any],
        extras: typing.Iterable[Union[ControlPoint, Any]] = (),
    ):
        self.delConstraint(target)

        args = tuple(args)
        extras = tuple(extras)

        self._constraints[target] = (kind, args, extras)

        cons: Constraint = self._registry[kind]

        for arg in set(args + extras):
            try:
                adaptor = self.adaptor(arg)  # use mro to find most-specified adaptor
            except TypeError:
                continue

            adaptor.addObservers(arg, self._onModify, priority=100.0)

            deps = self._dependencies.setdefault(arg, [])
            deps.append(target)

        cons(target, *args)

    def hasConstraint(self, target: ControlPoint):
        return target in self._constraints

    def delConstraint(self, target: ControlPoint):
        if not self.hasConstraint(target):
            return

        kind, args, extras = self._constraints.pop(target)

        for arg in set(args + extras):
            try:
                adaptor = self.adaptor(arg)
            except TypeError:
                continue

            adaptor.delObservers(arg)

            self._dependencies[arg].remove(target)

            if not self._dependencies[arg]:
                del self._dependencies[arg]

    @classmethod
    def registerConstraint(cls, key, func):
        cls._registry[key] = func


def constraint(obj=..., *, key=None):
    if obj is ...:
        return lambda f: constraint(f, key=key)

    if key is None:
        key = obj.__name__

    MarkupConstraintsLogic.registerConstraint(key, obj)

    return obj


@constraint
def midpoint(target: ControlPoint, *sources: ControlPoint):
    """Move target position to the mean of source positions."""

    pos = vtk.vtkVector3d()
    for dep in sources:
        vtk.vtkMath.Add(pos, dep.position, pos)
    vtk.vtkMath.MultiplyScalar(pos, 1 / len(sources))

    target.position = pos


@constraint
def lock(target: ControlPoint, dest: ControlPoint):
    """Move target to the destination position. Source is ignored but required for
    interactive locking.
    """

    target.position = dest.position


@constraint
def project(
    target: ControlPoint,
    source: ControlPoint,
    root: ControlPoint,
    axis: ControlPoint,
):
    """Move target to the point on the line from root to axis nearest to source
    position.
    """
    root = vtk.vtkVector3d(root.position)
    axis = vtk.vtkVector3d(axis.position)
    pos = vtk.vtkVector3d(source.position)

    vtk.vtkMath.Subtract(axis, root, axis)
    vtk.vtkMath.Subtract(pos, root, pos)

    t = vtk.vtkMath.Dot(pos, axis) / vtk.vtkMath.Dot(axis, axis)

    vtk.vtkMath.MultiplyScalar(axis, t)
    vtk.vtkMath.Add(axis, root, axis)
    target.position = axis


@constraint
def distance(
    target: ControlPoint,
    source: ControlPoint,
    root: ControlPoint,
    length: float,
):
    """Move target to the point on the sphere centered at root with radius distance
    nearest to source position.
    """

    root = vtk.vtkVector3d(root.position)
    pos = vtk.vtkVector3d(source.position)

    vtk.vtkMath.Subtract(pos, root, pos)
    vtk.vtkMath.Normalize(pos)
    vtk.vtkMath.MultiplyScalar(pos, length)
    vtk.vtkMath.Add(pos, root, pos)

    target.position = pos


@constraint
def nearest(
    target: ControlPoint,
    source: ControlPoint,
    model: slicer.vtkMRMLNode,
):
    locator = vtk.vtkPointLocator()
    locator.SetDataSet(model.GetPolyData())
    locator.AutomaticOn()

    points = slicer.util.arrayFromModelPoints(model)

    temp = vtk.vtkVector3d()

    model.TransformPointFromWorld(source.position, temp)
    index = locator.FindClosestPoint(temp)

    model.TransformPointToWorld(points[index], temp)
    target.position = temp


class MarkupConstraintsTest(
    ScriptedLoadableModuleTest,
    unittest.TestCase,
):
    def runTest(self):
        # Constraint and ControlPoint tests are in ./Testing/
        # API tests should go here
        raise NotImplementedError
