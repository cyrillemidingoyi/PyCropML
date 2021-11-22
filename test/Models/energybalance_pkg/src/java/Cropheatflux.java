import  java.io.*;
import  java.util.*;
public class Cropheatflux
{
    
    public Cropheatflux()
    {
           
    }
    public void  Calculate_cropheatflux(EnergybalanceState s, EnergybalanceRate r, EnergybalanceAuxiliary a)
    {
        //- Description:
    //            - Model Name: CropHeatFlux Model
    //            - Author: Pierre Martre
    //            - Reference: abModelling energy balance in the wheat crop model SiriusQuality2:
    //            Evapotranspiration and canopy and soil temperature calculations
    //            - Institution: INRA/LEPSE Montpellier
    //            - Abstract: It is calculated from net Radiation, soil heat flux and potential transpiration 
        //- inputs:
    //            - name: netRadiationEquivalentEvaporation
    //                          - variablecategory : auxiliary
    //                          - description : net Radiation Equivalent Evaporation
    //                          - datatype : DOUBLE
    //                          - default : 638.142
    //                          - min : 0
    //                          - max : 10000
    //                          - unit : g m-2 d-1
    //                          - uri : http://www1.clermont.inra.fr/siriusquality/?page_id=547
    //                          - inputtype : variable
    //            - name: soilHeatFlux
    //                          - description : soil Heat Flux
    //                          - variablecategory : rate
    //                          - datatype : DOUBLE
    //                          - default : 188.817
    //                          - min : 0
    //                          - max : 1000
    //                          - unit : g m-2 d-1
    //                          - uri : http://www1.clermont.inra.fr/siriusquality/?page_id=547
    //                          - inputtype : variable
    //            - name: potentialTranspiration
    //                          - description : potential Transpiration
    //                          - variablecategory : rate
    //                          - datatype : DOUBLE
    //                          - default :  1.413
    //                          - min : 0
    //                          - max : 1000
    //                          - unit : g m-2 d-1
    //                          - uri : http://www1.clermont.inra.fr/siriusquality/?page_id=547
    //                          - inputtype : variable
        //- outputs:
    //            - name: cropHeatFlux
    //                          - description :  crop Heat Flux
    //                          - variablecategory : rate
    //                          - datatype : DOUBLE
    //                          - min : 0
    //                          - max : 10000
    //                          - unit : g m-2 d-1
    //                          - uri : http://www1.clermont.inra.fr/siriusquality/?page_id=547
        double netRadiationEquivalentEvaporation = a.getnetRadiationEquivalentEvaporation();
        double soilHeatFlux = r.getsoilHeatFlux();
        double potentialTranspiration = r.getpotentialTranspiration();
        double cropHeatFlux;
        cropHeatFlux = netRadiationEquivalentEvaporation - soilHeatFlux - potentialTranspiration;
        r.setcropHeatFlux(cropHeatFlux);
    }
}