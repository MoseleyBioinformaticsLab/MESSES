Common Conventions
==================
This page is intended to serve as the place to put informaiton about depositing information in general, 
and extends to more than simply using the MESSES package. Some of the information will be highly specific 
to certain repositories or certain fields, but it's important to get this information somewhere.

Metabolomics Standards Initiative (MSI)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The Metabolomics Standards Initiative (MSI) is an international community effort launched in 2005 
by the Metabolomics Society to establish consensus-based reporting standards for metabolomics data, 
ensuring that experimental results are transparent, reproducible, and reusable. One of the most 
significant products they have produced is the minimimum reporting standards for chemical analysis. 
It has evolved over the years, but is mainly assigning a numerical level to an identified chemical 
to give it a level of confidence in its assignment. For example, a level 1 designation would be the 
highest confidence that the identified chemical is assigned to the correct name, and higher numbers 
would be less confidence. At the time of writing (April 10, 2026) there are currently 4 significant 
papers describing the confidence levels:

Sumner:
Original guidelines from Cheimcal Analysis Working Group (CAWG), MSI.
https://rdcu.be/e6DKX
2007
4 levels

Jeon:
https://doi.org/10.1021/tx300457f
2013
4 levels, but is more concrete than the original paper.

Schymanski:
https://doi.org/10.1021/es5002105
2014
5 levels, has level 2a and 2b

Schrimpe-Rutledge:
https://doi.org/10.1007/s13361-016-1469-y
2016
5 levels

The Schymanski paper in 2014 is the most widely cited and used version of this system. The reason 
this system is being mentioned here is because these levels are very good information to deposit 
with any data it is relevant for (mass spec and NMR), but there are some issues in trying to do 
that deposition well. Since there are multiple versions of the system, simply depositing the numeric 
level associated with any chemical assignments in a dataset would be ambiguous. You also need to 
include which version of the system is being used. To do this we propose identifying the version 
by the publication year. So for example if you have something like "msi_level" in a data table you 
could add the column "msi_level_type" and give it the value "MSI_2014" or "MSI_2016", whichever is 
the correct year being used. Since this value is unlikely to change for assignments in a given dataset, 
it is unlikely that multiple MSI confidence level systems are being used in one dataset unless it 
is combining many datasets together, a column in a table might be overkill. If there is somewhere 
more appropriate to indicate this within the deposition format, then it can be indicated there instead 
since this is more metadata than data.