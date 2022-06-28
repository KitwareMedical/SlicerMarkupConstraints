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

logic.setConstraint(C, 'midpoint', A, B)
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

### `'midpoint', *args: ControlPoint`

Set target position to the mean of deps positions.

### `'lock', dep: ControlPoint`

Set target position to match dep position.

### `'project', root: ControlPoint, axis: ControlPoint`

Set target position to lie on the line from root to axis.

### `'distance', root: ControlPoint, distance: float`

Set target position to be a certain distance from root.

## Custom Constraints

Invoking `logic.setConstraint(target, kind, *args)` will add appropriate observers on all
`*args`; when any `ControlPoint` arg is modified, the constraint function is found via 
`kind` and invoked with `func(target, *args)`. This function should update the position of
`target` to be constrained via `*args`.

For example, `logic.setConstraint(T, 'midpoint', A, B)` will invoke `midpoint(T, A, B)`
whenever `A` or `B` is modified.

To register a custom constraint function, use `@MarkupConstraintsLogic.register`. For example:

```python
from MarkupConstraints import MarkupConstraintsLogic, ControlPoint

@MarkupConstraintsLogic.register('my_constraint')
def my_constraint(target: ControlPoint, source: ControlPoint, arg: float): 
    ...  # update target.position

logic = MarkupConstraintsLogic()

T: ControlPoint = ...
S: ControlPoint = ...
F: float = ...
logic.setConstraint(T, 'my_constraint', S, F)
```
