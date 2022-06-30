import abc
import collections
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
        return self.node.GetNthControlPointPosition(self.idx)

    @position.setter
    def position(self, pos):
        self.node.SetNthControlPointPosition(self.idx, pos)

    def setLocked(self, locked):
        self.node.SetNthControlPointLocked(self.idx, locked)

    @classmethod
    def new(cls, node: "slicer.vtkMRMLMarkupsNode", pos=None):
        if pos is None:
            pos = vtk.vtkVector3d()
        elif not isinstance(pos, vtk.vtkVector3d):
            pos = vtk.vtkVector3d(pos)

        idx = node.AddControlPoint(pos or vtk.vtkVector3d())
        id_ = node.GetNthControlPointID(idx)
        return cls(node, id_)


class Constraint(typing.NamedTuple):
    func: Callable[[ControlPoint, ...], None]
    interactive: bool
    locked: bool

    def __call__(self, target, *args):
        self.func(target, *args)


class MarkupConstraintsLogic(
    ScriptedLoadableModuleLogic,
    VTKObservationMixin,
):
    _registry = {}

    _constraints: Dict[ControlPoint, Tuple[str, ...]]
    _dependencies: weakref.WeakKeyDictionary[
        "slicer.vtkMRMLMarkupsNode", Dict[str, List[ControlPoint]]
    ]
    _position_cache: weakref.WeakKeyDictionary[
        "slicer.vtkMRMLMarkupsNode", Dict[str, Tuple[float, float, float]]
    ]

    def __init__(self):
        ScriptedLoadableModuleLogic.__init__(self)
        VTKObservationMixin.__init__(self)

        self._constraints = {}
        # {target: (kind, *args)}
        # used to track which points are constrained, and how

        self._dependencies = weakref.WeakKeyDictionary()
        # {arg.node: {arg.id: [*targets]}}
        # used to determine the points to update after a given point is moved

        self._position_cache = weakref.WeakKeyDictionary()
        # {arg.node: {arg.id: position}}
        # used to determine whether a point has moved or not, to prevent extra updates

    def _onNodeModify(self, node, event):
        position_cache = self._position_cache.setdefault(node, {})

        with slicer.util.NodeModify(node):
            for arg_id, targets in self._dependencies[node].items():
                current = ControlPoint(node, arg_id).position
                cached = position_cache.get(arg_id, None)
                if cached and np.allclose(cached, current):
                    continue

                position_cache[arg_id] = current

                for target in targets:
                    kind, *args = self._constraints[target]
                    func = self._registry[kind]
                    func(target, *args)

    def setConstraint(
        self,
        target: ControlPoint,
        kind: str,
        *args: Union[ControlPoint, Any],
    ):
        _EVENTS = ()
        cons: Constraint = self._registry[kind]

        self._constraints[target] = (kind, *args)

        if cons.locked:
            target.setLocked(True)

        values = (target, *args) if cons.interactive else args
        for value in values:
            # check the value is a control point; if so, it should be observed and added
            # to the internal datastructures. if not it will pass through to the
            # constraint as a constant. to change the constant, invoke setConstraint
            # with a different value
            if isinstance(value, ControlPoint):
                if value.node not in self._dependencies:
                    for event in (
                        slicer.vtkMRMLMarkupsNode.PointAddedEvent,
                        slicer.vtkMRMLMarkupsNode.PointModifiedEvent,
                        slicer.vtkMRMLMarkupsNode.PointRemovedEvent,
                    ):
                        self.addObserver(
                            value.node,
                            event,
                            self._onNodeModify,
                            priority=100.0,
                        )

                node_dependencies = self._dependencies.setdefault(value.node, {})
                dependent_nodes = node_dependencies.setdefault(value.id, [])
                dependent_nodes.append(target)

        cons(target, *args)

    def delConstraint(self, target: ControlPoint):
        kind, *args = self._constraints.pop(target)
        cons: Constraint = self._registry[kind]

        if cons.locked:
            target.setLocked(False)

        values = (target, *args) if cons.interactive else args
        for value in values:
            self._dependencies[value.node][value.id].remove(target)

            if not self._dependencies[value.node][value.id]:
                del self._dependencies[value.node][value.id]

            if not self._dependencies[value.node]:
                del self._dependencies[value.node]

                for event in (
                    slicer.vtkMRMLMarkupsNode.PointAddedEvent,
                    slicer.vtkMRMLMarkupsNode.PointModifiedEvent,
                    slicer.vtkMRMLMarkupsNode.PointRemovedEvent,
                ):
                    self.removeObserver(value.node, event, self._onNodeModify)

    @classmethod
    def registerConstraint(cls, key, func, interactive, locked):
        cls._registry[key] = Constraint(func, interactive, locked)


def constraint(obj=..., *, key=None, interactive=False, locked=False):
    if obj is ...:

        def decorator(obj):
            return constraint(
                obj,
                key=key,
                interactive=interactive,
                locked=locked,
            )

        return decorator

    if key is None:
        key = obj.__name__

    MarkupConstraintsLogic.registerConstraint(key, obj, interactive, locked)

    return obj


@constraint(locked=True)
def imidpoint(target: ControlPoint, *deps: ControlPoint):
    """Set target position to the mean of deps positions."""

    pos = vtk.vtkVector3d()
    for dep in deps:
        vtk.vtkMath.Add(pos, dep.position, pos)
    vtk.vtkMath.MultiplyScalar(pos, 1 / len(deps))

    target.position = pos


@constraint(interactive=True)
def lock(target: ControlPoint, dep: ControlPoint):
    """Set target position to match dep position"""

    target.position = dep.position


@constraint(locked=True)
def project(
    target: ControlPoint,
    source: ControlPoint,
    root: ControlPoint,
    axis: ControlPoint,
):
    """Set target position to the position on the line from root to axis that is nearest
    to source position.
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


@constraint(interactive=True)
def iproject(target: ControlPoint, root: ControlPoint, axis: ControlPoint):
    """Interactive variant of 'project' constraint. Move the target position to the line
    from root to axis.
    """
    project(target, target, root, axis)


@constraint(locked=True)
def distance(
    target: ControlPoint,
    source: ControlPoint,
    root: ControlPoint,
    length: float,
):
    """Set target position to be source, shifted so it is a certain distance from
    root.
    """

    root = vtk.vtkVector3d(root.position)
    pos = vtk.vtkVector3d(source.position)

    vtk.vtkMath.Subtract(pos, root, pos)
    vtk.vtkMath.Normalize(pos)
    vtk.vtkMath.MultiplyScalar(pos, length)
    vtk.vtkMath.Add(pos, root, pos)

    target.position = pos


@constraint(interactive=True)
def idistance(
    target: ControlPoint,
    root: ControlPoint,
    length: float,
):
    """Interactive variant of 'distance'. Move the target position to be a certain
    distance from root.
    """
    distance(target, target, root, length)


class MarkupConstraintsTest(
    ScriptedLoadableModuleTest,
    unittest.TestCase,
):
    def runTest(self):
        # Constraint and ControlPoint tests are in ./Testing/
        # API tests should go here
        raise NotImplementedError
