import slicer
from MarkupConstraints import MarkupConstraintsLogic, ControlPoint

log = MarkupConstraintsLogic()

node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode')
node.GetDisplayNode().SetPropertiesLabelVisibility(False)
x = ControlPoint.new(node, (0, 0, 1))
y = ControlPoint.new(node)
log.setConstraint(y, 'idistance', x, 1)
C = y

for _ in range(5):
    node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode')
    node.GetDisplayNode().SetPropertiesLabelVisibility(False)
    x = ControlPoint.new(node)
    y = ControlPoint.new(node)
    log.setConstraint(x, 'lock', C)
    log.setConstraint(y, 'idistance', x, 1)
    C = y

# line = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode')
# proj = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode')
# pnts = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')
#
# a = ControlPoint.new(proj, (0, 0, +1))
# p = ControlPoint.new(proj)
#
# b = ControlPoint.new(line, (+1, 0, 0))
# c = ControlPoint.new(line, (-1, 0, 0))
#
# m = ControlPoint.new(pnts)
#
# log.setConstraint(p, 'project', a, b, c)
# log.setConstraint(m, 'idistance', p, 10)
