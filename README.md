# CIDS translation and comparison models
Translates indicator definition texts from the CIDS ontology into knowledge graphs and performs comparison against two knowledge graphs. 
## Translation model: converts CIDS indicator definition texts into .owl formats.
### Input:
A set of indicators text definitions(.csv). The format would be as follows:
`{Indicator Code,Indicator Definition}`

Example input (.csv):
```
OI1479,Amount of greenhouse gases (GHG) emitted through the organization's operations during the reporting period.
OI8825,Amount of purchased energy consumed by the organization during the reporting period.
OI6912,Area of land directly controlled by the organization and under sustainable cultivation or sustainable stewardship. Report directly controlled land area sustainably managed during the reporting period.
```

### Output
A CIDS .owl file updated with the translated indicators (in .owl format).

## Comparison model: runs a set of consistency checks between two indicators. 
**Note:** The consistency checks can be run on any two classes/individuals/class and individual in the CIDS ontology.

### Input:
Two items to be compared.

For each item, a message `Input the first/second thing (an individual or a class) from CIDS that you wish to compare: ` will appear prompting users to enter the RDF label of the item. Type in the labels corresponding to the items that you wish to compare.

Example input:
```
Input the first thing (an individual or a class) from CIDS that you wish to compare: PI9991
Input the second thing (an individual or a class) from CIDS that you wish to compare: PI9991
```
### Output:
Prints an analysis of whether the two items are consistent or inconsistent by each consistency check.

Example output:

TODO @Neevi
```
```

# Steps:
## Set up locally
1. Clone this repository to your local computer. `git clone https://github.com/CSSE-Capstone/Translation_Comparison.git`
2. On your computer, go to the cloned directory. 
3. Install package dependencies needed to run the code: `pip install -r requirements.txt` 
## Run the Translation model
To run the translation model, run `python3 run_translation.py`.
The .owl output file will be saved in the present directory TODO <- correct? @Sandy . But if you wish to save the command line outputs as well, run `python3 run_translation.py >> translation_output.txt"`
One of the features of the translation model is that it can plot knowledge graphs of each translated indicator. By default, this feature is disabled. To enable this feature, run `python3 run_translation.py -p`.
By default, the translation model runs on `{PATH_TO_LOCAL_REPO}/files/indicatortestset.csv`. However, if you have another indicator text definition csv file that you wish to run on, run `python3 run_translation.py -d {MY_INDICATOR_SET}.csv`
To enable both customizations, simply run the script wtih both options: `python3 run_translation.py -p -d {MY_INDICATOR_SET}.csv`

## Run the Comparison model
To run the comparison model, run `python3 run_comparison.py`.
If you wish to save the comparison command line output, run `python3 run_comparison.py >> comparison_output.txt"`.

