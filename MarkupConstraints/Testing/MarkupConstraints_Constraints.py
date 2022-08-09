import unittest

import slicer

from MarkupConstraints import MarkupConstraintsLogic, ControlPoint


class TestConstraints(unittest.TestCase):
    def test_lock(self):
        logic = MarkupConstraintsLogic()
        node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")

        A = ControlPoint.new(node, (-1.0, 0.0, +1))
        T = ControlPoint.new(node)

        logic.setConstraint(T, "lock", T, A)
        self.assertEqual(T.position, (-1.0, 0.0, +1.0), "Apply on set")

        A.position = (-1.0, 0.0, -1.0)
        self.assertEqual(T.position, (-1.0, 0.0, -1.0), "Apply on arg change")

        T.position = (0.0, 0.0, 0.0)
        self.assertEqual(T.position, (-1.0, 0.0, -1.0), "Apply on target change")

    def test_midpoint(self):
        logic = MarkupConstraintsLogic()
        node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")

        A = ControlPoint.new(node, (-1.0, 0.0, +1.0))
        B = ControlPoint.new(node, (+1.0, 0.0, +1.0))
        T = ControlPoint.new(node)

        logic.setConstraint(T, "midpoint", A, B, extras=[T])
        self.assertEqual(T.position, (0.0, 0.0, 1.0), "Apply on set.")

        A.position = (-1.0, 0.0, -1.0)
        self.assertEqual(T.position, (0.0, 0.0, 0.0), "Apply on arg change.")

        B.position = (+1.0, 0.0, -1.0)
        self.assertEqual(T.position, (0.0, 0.0, -1.0), "Apply on arg change.")

        T.position = (0.0, 0.0, 0.0)
        self.assertEqual(T.position, (0.0, 0.0, -1.0), "Apply on target change.")

    def test_project(self):
        logic = MarkupConstraintsLogic()
        node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")

        A = ControlPoint.new(node, (-1.0, -1.0, 0.0))
        B = ControlPoint.new(node, (+1.0, +1.0, 0.0))
        T = ControlPoint.new(node, (+1.0, -1.0, 7.0))

        logic.setConstraint(T, "project", T, A, B)
        self.assertEqual(T.position, (0.0, 0.0, 0.0), "Apply on set.")

        B.position = (-1.0, +2.0, 0.0)
        self.assertEqual(T.position, (-1.0, 0.0, 0.0), "Apply on arg change.")

        T.position = (5.0, 1.5, 7.0)
        self.assertEqual(T.position, (-1.0, 1.5, 0.0), "Apply on target change.")
