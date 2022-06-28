import unittest

import slicer

from MarkupConstraints import MarkupConstraintsLogic, ControlPoint


class TestConstraints(unittest.TestCase):
    def test_lock(self):
        logic = MarkupConstraintsLogic()
        node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")

        A = ControlPoint.new(node, (-1, 0, +1))
        T = ControlPoint.new(node)

        logic.setConstraint(T, "lock", A)
        self.assertEqual(T.position, (-1, 0, +1), "Apply on set")

        A.position = (-1, 0, -1)
        self.assertEqual(T.position, (-1, 0, -1), "Apply on arg change")

        T.position = (0, 0, 0)
        self.assertEqual(T.position, (1, 0, -1), "Apply on target change")

    def test_midpoint(self):
        logic = MarkupConstraintsLogic()
        node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")

        A = ControlPoint.new(node, (-1, 0, +1))
        B = ControlPoint.new(node, (+1, 0, +1))
        T = ControlPoint.new(node)

        logic.setConstraint(T, "midpoint", A, B)
        self.assertEqual(T.position, (0, 0, 1), "Apply on set.")

        A.position = (-1, 0, -1)
        self.assertEqual(T.position, (0, 0, 0), "Apply on arg change.")

        B.position = (+1, 0, -1)
        self.assertEqual(T.position, (0, 0, -1), "Apply on arg change.")

        T.position = (0, 0, 0)
        self.assertEqual(T.position, (0, 0, -1), "Apply on target change.")

    def test_project(self):
        logic = MarkupConstraintsLogic()
        node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")

        A = ControlPoint.new(node, (-1, -1, 0))
        B = ControlPoint.new(node, (+1, +1, 0))
        T = ControlPoint.new(node, (+1, -1, 7))

        logic.setConstraint(T, "project", A, B)
        self.assertEqual(T.position, (0, 0, 0), "Apply on set.")

        B.position = (-1, +2, 0)
        self.assertEqual(T.position, (-1, 0, 0), "Apply on arg change.")

        T.position = (5, 1.5, 7)
        self.assertEqual(T.position, (-1, 1.5, 0), "Apply on target change.")
