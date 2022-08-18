cmake_minimum_required(VERSION 2.8.9)

project(SlicerMarkupConstraints)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/KitwareMedical/SlicerMarkupConstraints")
set(EXTENSION_CATEGORY "Developer Tools")
set(EXTENSION_CONTRIBUTORS "David Allemang (Kitware)")
set(EXTENSION_DESCRIPTION "This extension contains one module of the same name. It allows Slicer extension developers to constrain
and synchronize markups and control points of different nodes. The extension was created during Slicer Project Week 37 for the Q3DCExtension project.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/KitwareMedical/SlicerMarkupConstraints/master/SlicerMarkupConstraints.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/KitwareMedical/SlicerMarkupConstraints/master/Docs/Sample.gif")
set(EXTENSION_ENABLED 1)

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(MarkupConstraints)

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
