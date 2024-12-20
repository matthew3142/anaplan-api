# anaplan-api
API for uploading CSV data to Anaplan

### Software prerequisites
1. [Python 3 or later](https://www.python.org/downloads/)
2. [Google Chrome v114](https://www.filepuma.com/download/google_chrome_64bit_114.0.5735.199-35569)
3. [`filesplit` library](https://pypi.org/project/filesplit/)
4. [`requests` library](https://pypi.org/project/requests/)
5. [`Flask` library](https://pypi.org/project/Flask/)
6. [`ngrok` proxy](https://ngrok.com/download/)
7. [`Selenium` webdriver](https://pypi.org/project/selenium/)
8. [`ChromeDriver` v114](https://chromedriver.storage.googleapis.com/index.html?path=114.0.5735.90%2F)

### How to use (after all prerequisites are met)
1. Run the `cmd` window and type `ngrok start my-app`
2. Run the Python program called `flask_to_help.py`
3. Open a new browser window and go to `localhost:5000`
4. Sign in and authenticate with Xero
5. On the success message, exit all the programs you started
6. Run the remaining programs in sequential order

### Ngrok prerequisites
1. Account created
2. Downloaded, with the `exe` saved into `System32`
3. Configured according to providers
4. Reserved a domain (done [here](https://dashboard.ngrok.com/cloud-edge/domains))
5. Added this domain to `ngrok.yml` (usually located within `%appdata%\..\Local\ngrok\`) as the following:
```
tunnels:
    my-app:
        addr: 5000
        proto: http
        hostname: YOUR-HOSTNAME-HERE.ngrok-free.app
```

### Xero prerequisites
1. Developer account with the right permissions
2. App set up from [here](https://developer.xero.com/app/manage)
3. Correct redirect URI in your app's configuration (this is the ngrok domain plus `/callback` at the end)
4. No more than 2 uncertified apps connected at once
5. Put required [scopes](https://developer.xero.com/documentation/guides/oauth2/scopes/) in `config.json`. For example, `accounting.transactions.read`.

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
1. Updated `config.json` parameters - this requires keys and info from both Xero and Anaplan
2. Have set your username and password used for Anaplan as system environment variables
3. Have the CSV file in the same directory as the program
4. `ChromeDriver` executable added to `PATH` (the easiest way to do this is as follows)

#### How to add `ChromeDriver` to `PATH`
1. Create a new directory `C:\Webdrivers` and put the `exe` inside it
2. Search Start for `environment variables`
3. Under "System variables", open "Path"
4. Add `C:\webdrivers`
5. Save and exit everything
