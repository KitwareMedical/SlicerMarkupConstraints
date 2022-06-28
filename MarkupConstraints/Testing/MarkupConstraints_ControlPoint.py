import unittest

import slicer

from MarkupConstraints import ControlPoint


class TestControlPoints(unittest.TestCase):
    def test_new(self):
        node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")

        point = ControlPoint.new(node)
        self.assertEqual(node.GetNumberOfControlPoints(), 1)

        point = ControlPoint.new(node, (1.0, 2.0, 3.0))
        self.assertEqual(node.GetNumberOfControlPoints(), 2)
        self.assertEqual(point.position, (1.0, 2.0, 3.0))
        self.assertEqual(point.position, node.GetNthControlPointPosition(1))

    def test_move(self):
        node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLMarkupsFiducialNode")

        point = ControlPoint.new(node, (1.0, 2.0, 3.0))

        # change the position and verify updated
        point.position = (2.0, 3.0, 4.0)
        self.assertEqual(point.position, (2.0, 3.0, 4.0))

        # change the position via node and verify updated
        node.SetNthControlPointPosition(0, (3.0, 4.0, 5.0))
        self.assertEqual(point.position, (3.0, 4.0, 5.0))
