# anaplan-api
API for uploading CSV data to Anaplan

### Software prerequisites
1. [Python 3 or later](https://www.python.org/downloads/)
2. [`filesplit` library](https://pypi.org/project/filesplit/)
3. [`requests` library](https://pypi.org/project/requests/)

### Anaplan prerequisites
1. File to import already uploaded via UI  (this only has to be done once)
2. A successful manual import of the CSV to have taken place. 

#### How to set up an initial successful manual CSV import
1. Format the module correctly
   1. the use of one column for each dimension, with column headers only representing one dimension
   2. have saved this view by going to `View > Save As`, then the necessary options to have Anaplan favour it
2. Export a test version
   1. after pressing `Data > Export`, use the `Tabular Multiple Column` format and `Include Empty Rows` option toggled
3. Run an import of that file and ensure it works

### Program prerequisites
1. Updated `config.json` parameters
2. Have set the username and password used for Anaplan as system environment variables
3. Have the CSV file in the same directory as the program
