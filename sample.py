from MarkupConstraints import MarkupConstraintsLogic, ControlPoint

l = MarkupConstraintsLogic()

n = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')

a = ControlPoint.new(n)
b = ControlPoint.new(n)
c = ControlPoint.new(n)
d = ControlPoint.new(n)

l.setConstraint(c, 'distance', a, 5)  # c is 5 units from a

l.setConstraint(d, 'midpoint', b, c)  # d is the midpoint of b and c
