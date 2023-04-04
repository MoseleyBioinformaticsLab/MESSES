This is an example using real data that has been uploaded to the Metabolomics Workbench. It has been cleaned up a little bit, but some 
messiness remains to illustrate how tags can be added on top of existing data. The mouse_experiment_metadata.xlsx file is data collected 
for a PDX mouse experiment (summary below). The "Master sheet" sheet is the mostly original sheet used by the lab during the experiment 
to tabulate the data, while the "#export" is a copy by values of the "Master sheet". This file is where most of the data for the factor, 
project, study, and entity tables will come from. An important thing to note is that only the NMR data is pulled out for this NMR example. 
The --delete option is used to filter out data not relevant for the submission. In general you do not want to pull in more than is necessary 
because it can cause conflicts and may be unecessary for the repository depositon. 

The NMR_colon_measurements.xlsx are nuclear magnetic resonance spectroscopy measurements done on the colons of the harvested mice 
in the experiment. Metabolites are identified from the raw NMR results and that data is what is presented here. 
Tags are added directly to the metadata file, but automation and modification tags are used heavily for the NMR data. To reproduce the 
result run the Run Command given below. Note that --silent can be left out to see warnings, but there are several "never matched" warnings 
that can be safely ignored. If you cannot reproduce extracted_result.json then don't use the --silent option and troubleshoot the errors 
and warnings.

Study Summary:
Allogeneic hematopoietic cell transplantation (allo-HCT) is a potentially curative treatment option for a variety of 
hematological malignancies. Interactions between the donor immune system and the patient tissue result in a disease, 
called GVHD. The pathophysiology of acute GVHD can be hypothesized in three sequential phases: cytokine storm and 
activation of the antigen-presenting cells (APC), donor T cell activation and effector cell phase. Idiopathic pneumonia 
syndrome (IPS) is one of the most deleterious complications after allogeneic HCT and is considered not only to be 
related to conditioning regimen toxicity but also represents an end organ damage caused by allo-reactive T cells, 
therefore making the lung susceptible to a two-pronged attack, one of which overlaps with GVHD causing other target organ 
injury. IPS results in mortality of up to 90% of patients. We will use a murine model of IPS and GVHD which is well 
established in our group, and in which disease evolves either across disparities in major histocompatibility complex 
(MCH) class I and II, minor histocompatibility antigens (miHags) or both. Metabolomics changes following syngeneic and 
allogeneic HCT at post-transplantation Days +7 (cytokine storm phase) and Days +42 (cellular effector phase) are compared 
to baseline wild-type (naive) controls. Prior to analysis, naïve - and experimental mice (N=3 from each group) were fed 
with semi-liquid diet supplemented with tracers (13C6-glucose ) over 24 hours. At the end of 7 days or 42 days, respectively, 
feces and aGVHD target organs (colon, liver and lung) were collected from all groups and further processed and / or analyzed. 
We expect to reveal metabolic pathways affected after allo-HCT which contribute to immune cell mediated lung injury (IPS) 
and will potentially identify different metabolic pathways in other GVHD target organs.

Input Files:
mouse_experiment_metadata.xlsx
NMR_measurements.xlsx

Output Files:
extracted_result.json

Run Command:
messes extract mouse_experiment_metadata.xlsx NMR_colon_measurements.xlsx --end-modify #endmodify --output extracted_result --silent --delete "entity,r'^(?!.*(-NMR_A|-protein|\d$))|.*Plasma|Lung|Spleen|SI|Liver.*'" --delete "protocol,acetone_extraction" --delete "protocol,lipid_extraction" --delete "protocol,IC-FTMS_preparation"