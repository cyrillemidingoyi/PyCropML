
<u> **From crop DSSAT modeling platform to Crop2ML framework** </u>

DSST modelers provide an autonomous crop model component.
It includes the CMakeLists file that contains the source files.

For the transformation, we need to identify:
    * the subroutines that correspond to the Crop2ML ModelUnits. 
    * The parts of these subroutines that represent initialization, rate calculation, state calculation. If rate and state  calculations are not separated, algorithm part must be identified 
    * Given that some parts could be specific to DSSAT environment such as I/O operations, data formatting, and variables declarations statements for these constructions, it is necessary to skip these parts. Then these subroutines that are called inside the code must be specified.

For that, we defined some tags (opened and closed) that will be introduced in the source files to distinguish each parts

                             
|Tags  |Parts of source file|
|-----|--------|
|!%%CyML Model Begin%% / !%%CyML Model End%% | Model    |
|!%%CyML Init Begin%% / !%%CyML Init End%%  | Initialization part      |
|!%%CyML Rate Begin%% / !%%CyML Rate End%% | Rate Calculation part
|!%%CyML State Begin%% / !%%CyML State End%% | State Calculation part 
|!%%CyML Compute Begin%% / !%%CyML Compute End%%| Algorithm part  
|!%%CyML Ignore Begin%% / !%%CyML Ignore End%%| Ignored Statement

For the not required subroutines, a tag "!%%NotRequired%%" is placed before these subroutines

Transformation process
======================
The transformation process involves these steps:

1. A parser of CMake file is used to extract the different source files


2. These files are merged in one temporal file and parsed to generate a Fortran ASG (asgT)

3. For each file of the source files:

3.1. We identify and extract the subroutines that are tagged with ModelUnit tags.

3.2. For each 


