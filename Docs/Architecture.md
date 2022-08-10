# Architecture Overview

## Introduction

The [Q3DC Extension][q3dc] is one of several extensions which has developed its own 
implementation of this kind of functionality. There is a need for a common infrastructure 
to deal with these constraints/rules which enables interoperation between such modules,
and supports serialization/deserialization of constrained markup nodes.

[q3dc]: https://github.com/DCBIA-OrthoLab/Q3DCExtension

## Events and Observations

The core functionality of the module should allow a developer to register a control point 
in a node as "constrained", defining what constraint to apply and any dependencies of that 
constraint.

When the constraint is defined, and whenever a dependency is modified, the constraint 
should be re-evaluated and the position of the constrained control point updated.  

I use VTKObservationMixin for this. It is important to be careful not to recurse 
indefinitely during the observation callback, but still propagate through chains of 
dependencies. 

## Data Structures

It is not possible to observe only a single control point for modification; the entire
markup node must observed. Therefore it is important to avoid recursion when control 
points within a single node depend on each other. To avoid recursion, I define a new 
`ControlPoint` type that contains a markup node and the ID of a control point within that
node. Constraints are then applied to `ControlPoint` instances.

Observer callbacks then identify the particular control points within the modified node 
that are affected, and invoke constraints on dependant control points. Invoking a 
constraint in this way should not trigger further callbacks; the dependency graph should 
be walked within the initial observation. After all, the modification was triggered by 
only one external event.

Notably, this approach is not thread-safe. I don't believe it would be required by any
_scripted_ modules that consume this API given the constraints of the Python interpreter.  

The dependency graph should be kept in-memory as a Python object; this way control point 
positions and other constraint parameters may be effectively cached. The graph should be 
stored in parameters and node references of the observed nodes; however only the 
information needed to reconstruct the graph should be stored. Cached constraint parameters
should not be. 

It is also important to consider the lifetime of the observed nodes; for this reason I 
created https://github.com/Slicer/Slicer/pull/6409. Cached positions and other constraint
parameters should be similarly stored using `weakref` references. 

## Cycle Detection and Error Messages

Python exceptions and logging will be used for all error reporting; as this module is only 
a development tool, it should be the responsibility of the consuming module to catch 
errors and present meaningful, contextual, messages to the user.

It would be useful for this module to detect if a cyclic constraint is added, to prevent 
infinite propagation of constraints. It may be possible in the future to use a more 
advanced constraint solver to handle some such cases, but for now basic propagation and
cycle detection should be enough.

## User-defined constraints

Module developers should be able to register their own constraint types. Constraints 
should be identified by a string identifier, and a registry of known constraints will be
used to find the appropriate constraints when a new constraint is added or a constrained 
markup node is deserialized.   

The constraint API will be handled as an abstract Python class to be registered when the 
defining module is loaded.

The API should include a method to determine constraint parameters from control points, 
for caching purposes and to identify the modified control points in the observer callback.
It should also include a method to apply the constraint to a target control point, given 
those parameters. This is abstract enough that the constraints _may_ deal with more than 
just positions of markups, although position constraints are the most natural (and the 
motivating) application. 

User documentation should be created once the API is more solidified.

## Why not include in Slicer Core?

I've chosen to build the module as a Python extension for ease of development and so the
module is not locked to the Slicer release schedule. In the future, when these features
are more mature, it may be sensible to move this functionality into Slicer core for ease
of use.

If it is added to Slicer core, I feel the constraints system should be restructured using
MRML nodes so they are truly part of the scene, rather than using node parameters and
references as is done now.
