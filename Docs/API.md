# Constraints API Documentation

## Quick Start

```python
import slicer

from MarkupConstraints import MarkupConstraintsLogic, ControlPoint

logic = MarkupConstraintsLogic()

node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')
A = ControlPoint.new(node, [-1, 0, 0])
B = ControlPoint.new(node, [+1, 0, 0])
C = ControlPoint.new(node)

logic.setConstraint(C, 'midpoint', A, B)  # lock C to the midpoint of A and B.

axis = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode')
X = ControlPoint.new(axis, [-1, -1, 0])
Y = ControlPoint.new(axis, [+1, +1, 0])

proj = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode')
I = ControlPoint.new(proj, [0.5, 0, 0])
P = ControlPoint.new(node)

logic.setConstraint(P, 'project', I, X, Y)  # lock P to the projection of I onto line X-Y.

Q = ControlPoint.new(node)
logic.setConstraint(Q, 'project', Q, X, Y)  # keep Q projected onto line X-Y.
```

## `ControlPoint`

A `ControlPoint` instance is a simple wrapper to refer to a particular control point of a
particular `vtkMRMLMarkupsNode`.

## `MarkupConstraintsLogic`

### `setConstraint(target: ControlPoint, kind: str, *args: Any)`

The logic will set appropriate observers on `*args` such that, when an argument is 
modified, the appropriate constraint function will be called to constrain `target`.

For example `setConstraint(A, 'midpoint', B, C)` should be read to mean: "Constrain A to 
the midpoint of B and C."

## Default Constraints

### `'midpoint', *sources: ControlPoint`

Move target to the mean of source positions.

### `'lock', source: ControlPoint, dest: ControlPoint`

Move target to the destination position. Source is ignored but required for interactive 
locking.

### `'project', source: ControlPoint, root: ControlPoint, axis: ControlPoint`

Move target to the point on the line from root to axis nearest to source position.

### `'distance', source: ControlPoint, root: ControlPoint, distance: float`

Move target to the point on the sphere centered at root with radius distance nearest to
source position.

## Custom Constraints

Invoking `logic.setConstraint(target, kind, *args)` will add appropriate observers on all
`*args`; when any `ControlPoint` arg is modified, the constraint function is found via 
`kind` and invoked with `func(target, *args)`. This function should update the position of
`target` to be constrained via `*args`.

For example, `logic.setConstraint(T, 'midpoint', A, B)` will invoke `midpoint(T, A, B)`
whenever `A` or `B` is modified.

To register a custom constraint function, use `@MarkupConstraintsLogic.register`. For example:

```python
from MarkupConstraints import MarkupConstraintsLogic, ControlPoint, constraint

@constraint
def my_constraint(target: ControlPoint, source: ControlPoint, arg: float): 
    ...  # update target.position

logic = MarkupConstraintsLogic()

T: ControlPoint = ...
S: ControlPoint = ...
F: float = ...
logic.setConstraint(T, 'my_constraint', S, F)
```

## Custom Adaptors

Allow using other types as dependencies by extending `NodeAdaptor`. See `ControlPointAdaptor` for an example.

### `NodeAdaptor.wrap(item, method)`

Returns a VTK observer `observer(node, event)` which calls `method(item, event)` only if the wrapped item was updated.

### `NodeAdaptor.events()`

Returns a list of VTK events to be observed.

### `NodeAdaptor.getVtkObject(item)`

Gets the associated VTK object for a wrapped item. Observers are added to this object.
