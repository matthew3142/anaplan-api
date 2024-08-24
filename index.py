import time
import warnings
import requests
import json
from filesplit.split import Split
import os
import glob
import logging
import csv

with open('config.json', 'r') as json_file:
    config = json.load(json_file)

# replace with just pure credentials if not using environment vars
# but only if using for personal use
user = os.getenv(config["user_credentials"]["environment_variable_storing_username"])
password = os.getenv(config["user_credentials"]["environment_variable_storing_password"]) 

if config["program_settings"]["verbose_mode"]:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

# set constants

CYCLE_LENGTH_MINUTES = config["constants"]["cycle_length_minutes"]
WORKSPACE_ID = config["constants"]["workspace_id"]
MODEL_ID = config["constants"]["model_id"]

# configure file constants
FILECHUNKDIR = config["file_configuration"]["file_chunk_dir_name"]
CHUNKSIZE_MB = config["file_configuration"]["chunksize_mb"]
UPLOAD_FILE = config["file_configuration"]["upload_file"]
UPLOAD_FILE_BASE, UPLOAD_FILE_EXTENSION = UPLOAD_FILE.rsplit('.', 1)

GREY = '\033[90m' 
BRIGHT_WHITE = '\033[97m'  
print(f"{GREY}")

class basic_functions:
    def current_milli_time():
        return round(time.time() * 1000)
    
    def create_filechunkdir(dir):
        if not os.path.isdir(dir):
            os.makedirs(dir, exist_ok=True)
            return True
        else:
            return False

    def count_chunk_files(dir):
        if not os.path.isdir(dir):
            warnings.warn("Directory does not exist")
            return 0
        return len([name for name in os.listdir(dir) if os.path.isfile(os.path.join(dir, name))])
    
    def num_bytes(inafile):
        with open(inafile, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
        return file_size
    
    def print_w(text):
        print(f"{BRIGHT_WHITE}{text}{GREY}")

class file_functions:
    def __init__(self, init_file, outputdir):
        self.init_file = init_file
        self.outputdir = outputdir

    def clear_outputdir(self):
        fulloutputdir = os.path.join(os.path.dirname(__file__), self.outputdir)
        files = glob.glob(os.path.join(fulloutputdir, '*'))
        for f in files:
            try:
                os.remove(f)
            except PermissionError as e:
                basic_functions.print_w("PermissionError: {e} - Could not delete the file {f}")
            except OSError as e:
                basic_functions.print_w("OSError: Could not delete file {f}")

    def chunk(self): # convert file into chunks
        try:
            split = Split(self.init_file, self.outputdir)
        except:
            return False
        split.bysize(CHUNKSIZE_MB*1024*1024) # default 50 MB
        return True

    def chunk_count(self):
        return basic_functions.count_chunk_files(self.outputdir) - 1 # -1 for manifest

    def upload(self): # directory for already chunked files
        pass

class anaplan_establish_connection:
    def __init__(self):
        pass

    def read_authtokeninfo(self):
        authtokeninfo = [config["auth_token_info"]["last_visited"], config["auth_token_info"]["token"]]
        return authtokeninfo

    def is_okay_timewise(self, last_call): # answers the question: is it okay to make a new request?
        # first line contains the time it was last received
        if last_call == "":
            return True

        try:
            last_call = int(last_call)

        except:
            return True

        current_time = basic_functions.current_milli_time()

        # find out of there's at least a 35 minute gap between now and last call
        gap = current_time - last_call
        gap = gap//60000 # convert to minutes

        if gap >= CYCLE_LENGTH_MINUTES: 
            return True
        else:
            return False

    def append_time_save_token(self, token):
        current_time = basic_functions.current_milli_time()
        config["auth_token_info"]["last_visited"] = str(current_time)
        config["auth_token_info"]["token"] = token
        try:
            with open('config.json', 'w') as file:
                json.dump(config, file, indent=4, ensure_ascii=False)
            basic_functions.print_w("-> Configuration file updated successfully.")
        except IOError as e:
            basic_functions.print_w(f"-> An error occurred while writing to the file: {e}")

    def refresh_token(self, current_token_value, autosave=True):
            headers = {
                'authorization': 'AnaplanAuthToken ' + current_token_value,
            }
            response = requests.post('https://auth.anaplan.com/token/refresh', headers=headers)
            if autosave:
                anaplan_establish_connection.save_token()

    def authenticate_user(self, user, password):
        response = requests.post('https://auth.anaplan.com/token/authenticate', auth=(user, password))
        data = response.json()
        status = data['status']
        if status == "SUCCESS":
            basic_functions.print_w("Authentication successful")
        else:
            raise Exception("Authentication failed: " + data['statusMessage'])
        return data
    
class anaplan_file_import:
    def __init__(self, current_token_value=None, workspaceID=None, modelID=None, fileID=None, filename=None, importID=None, taskID=None, chunksize=-1, first_data_row='2', content_type="application/json"):
        self.current_token_value = current_token_value
        self.workspaceID = workspaceID
        self.modelID = modelID
        self.fileID = fileID
        self.filename = filename
        self.chunksize = chunksize
        self.first_data_row = first_data_row
        self.content_type = content_type
        self.importID = importID
        self.taskID = taskID

    def list_models(self):
        headers = {
            'authorization': 'AnaplanAuthToken ' + self.current_token_value,
        }
        response = requests.get('https://api.anaplan.com/2/0/models', headers=headers)
        data = response.json()
        return data
    
    def list_import_actions(self):
        headers = {
            'Authorization': 'AnaplanAuthToken ' + self.current_token_value,
            'Content-Type': 'application/json',
        }

        response = requests.get(
            'https://api.anaplan.com/2/0/workspaces/' + self.workspaceID + '/models/' + self.modelID + '/imports',
            headers=headers,
        )

        data = response.json()
        return data
    
    def list_import_files(self):
        import requests

        headers = {
            'Authorization': 'AnaplanAuthToken ' + self.current_token_value,
        }

        response = requests.get(
            'https://api.anaplan.com/2/0/workspaces/' + self.workspaceID + '/models/' + self.modelID + '/files',
            headers=headers,
        )

        data = response.json()
        return data
    
    def set_chunk_count(self, chunk_count):
        headers = {
            'Authorization': 'AnaplanAuthToken ' + self.current_token_value,
            'Content-Type': self.content_type,
        }

        json_data = {
            'chunkCount': chunk_count,
        }

        response = requests.post(
            'https://api.anaplan.com/2/0/workspaces/' + self.workspaceID + '/models/' + self.modelID + '/files/' + self.fileID,
            headers=headers,
            json=json_data,
        )

        data = response.json()
        return data
    
    def load_import_file_chunks(self, chunkID, chunk_filename, content_length_bytes, content_type='application/octet-stream'):
        headers = {
            'Authorization': 'AnaplanAuthToken ' + self.current_token_value,
            'Content-Type': content_type,
        }

        with open(FILECHUNKDIR + "/" + chunk_filename, 'rb') as f:
            data = f.read()

        response = requests.put(
            'https://api.anaplan.com/2/0/workspaces/' + self.workspaceID +'/models/' + self.modelID + '/files/' + self.fileID +'/chunks/' + str(chunkID),
            headers=headers,
            data=data,
        )
        if response.status_code == 204:
            return True
        else:
            warnings.warn("Response has status code " + str(response.status_code))
            return False
    
    def mark_upload_as_complete(self):
        headers = {
            'Authorization': 'AnaplanAuthToken ' + self.current_token_value,
            'Content-Type': 'application/json',
        }

        json_data = {
            'id': self.fileID,
            'name': self.filename,
            'chunkCount': -1,
            'firstDataRow': 2,
            'headerRow': 1,
        }

        response = requests.post(
            'https://api.anaplan.com/2/0/workspaces/' + self.workspaceID + '/models/' + self.modelID + '/files/' + self.fileID + '/complete',
            headers=headers,
            json=json_data,
        )

        data = response.json()
        return data
    
    def get_status(self):
        headers = {
            'Authorization': 'AnaplanAuthToken ' + self.current_token_value,
            'Content-Type': 'application/json',
        }
        response = requests.get('https://api.anaplan.com/2/0/workspaces/' + self.workspaceID + '/models/' + self.modelID + '/imports/' + self.importID + '/tasks/' + self.taskID, headers=headers)
        return response

    def get_metadata(self):
        headers = {
            'Accept': '*/*',
            # 'Accept-Encoding': 'gzip, deflate',
            'Authorization': 'AnaplanAuthToken ' + self.current_token_value,
        }

        response = requests.get(
            'https://api.anaplan.com/2/0/workspaces/' + self.workspaceID + '/models/' + self.modelID + '/imports/' + self.importID,
            headers=headers,
        )

        return response
    
    def complete_import_task(self):
        data = self.get_status().json()
        task_state = data['task']['taskState']
        basic_functions.print_w("---> pinged")

        # keep pinging until the task is no longer ongoing
        while not ((task_state == "COMPLETE") or (task_state == "CANCELLED")):
            time.sleep(1)
            basic_functions.print_w("---> pinging again...")
            data = self.get_status().json()
            task_state = data['task']['taskState']

        successful = data['task']['result']['successful']

        if successful and task_state == "COMPLETE":
            return 0
        elif successful and task_state == "CANCELLED":
            return 1
        else:
            return -1
    
    def check_dump_file(self):        
        headers = {
            'Authorization': 'AnaplanAuthToken ' + self.current_token_value,  
            'Content-Type': 'application/json'  
        }
        response = requests.get(
        'https://api.anaplan.com/2/0/workspaces/' + self.workspaceID + '/models/' + self.modelID + '/imports/' + self.importID + '/tasks/' + self.taskID + '/dump',
        headers=headers
        )
        return response
    
    def create_new_task(self):
        json_data = {
            'localeName': 'en_GB',
        }
        headers = {
            'Authorization': 'AnaplanAuthToken ' + self.current_token_value,
            'Content-Type': 'application/json',
        }
        response = requests.post('https://api.anaplan.com/2/0/workspaces/' + self.workspaceID + '/models/' + self.modelID + '/imports/' + self.importID + '/tasks', headers=headers, json=json_data)
        return response

def main():
    basic_functions.print_w("\n\nDealing with input file...")
    basic_functions.print_w("-> Does a directory to store chunks exist?")
    if basic_functions.create_filechunkdir(FILECHUNKDIR):
        basic_functions.print_w("---> No")
        basic_functions.print_w("---> One has been created")
    else:
        basic_functions.print_w("---> Yes")
    f = file_functions(UPLOAD_FILE, FILECHUNKDIR)
    f.clear_outputdir()
    basic_functions.print_w("-> Cleared chunk directory")
    basic_functions.print_w("-> Does the upload file exist in this dir?")
    if not f.chunk():
        basic_functions.print_w("---> No")
        basic_functions.print_w("---> Filename: " + UPLOAD_FILE)
        basic_functions.print_w("---> Action needed: Go back and fix this, and then try again.")
        return
    basic_functions.print_w("---> Yes\n-> Successfully chunked.")

    basic_functions.print_w("\nIs Anaplan connection working?")
    anaplan_connect = anaplan_establish_connection()
    basic_functions.print_w("-> Yes")

    ati = anaplan_connect.read_authtokeninfo() # [0] is time, [1] is value

    basic_functions.print_w("\nHas it been " + str(CYCLE_LENGTH_MINUTES) + " minutes since last sign-on?")
    if anaplan_connect.is_okay_timewise(ati[0]): # new token
        basic_functions.print_w("-> Yes")
        data = anaplan_connect.authenticate_user(user, password)
        basic_functions.print_w("-> Authenticated user")
        basic_functions.print_w("---> u: " + str(user))
        pwdlength = "*"*len(password)
        basic_functions.print_w("---> p: " + str(pwdlength))
        token_value = data['tokenInfo']['tokenValue']
        anaplan_connect.append_time_save_token(token_value)
        basic_functions.print_w("-> Saved this access attempt")

    else: # old token
        basic_functions.print_w("-> No")
        token_value = ati[1]

    anaplan_import = anaplan_file_import(current_token_value=token_value, workspaceID=WORKSPACE_ID, modelID=MODEL_ID, filename=UPLOAD_FILE)

    basic_functions.print_w("\nDoes this file exist in the model already?")
    imported_files = anaplan_import.list_import_files()
    fileID = None
    for file in imported_files['files']:
        if file['name'] == UPLOAD_FILE:
            fileID = file['id']
            break
    anaplan_import.fileID = fileID
    if fileID == None:
        basic_functions.print_w("-> No")
        basic_functions.print_w("-> Help is needed here")
        basic_functions.print_w("-> Action needed: Upload the file to the model using the Anaplan UI")
        basic_functions.print_w("-> Come back after you have finished")
        return
    else:
        basic_functions.print_w("-> Yes")
        basic_functions.print_w("-> with ID: " + str(anaplan_import.fileID))

    x = anaplan_import.set_chunk_count(-1)

    basic_functions.print_w("\nUploading chunks...")
    for chunkID in range(f.chunk_count()):
        chunk_name = UPLOAD_FILE_BASE + "_" + str(int(chunkID) + 1) + "." + UPLOAD_FILE_EXTENSION # logic based on naming conventions of Split, ie filename__1 filename__2 etc
        importsuccess = anaplan_import.load_import_file_chunks(chunkID, chunk_name, basic_functions.num_bytes(FILECHUNKDIR + "/" + chunk_name))
        if importsuccess:
            basic_functions.print_w("-> Successful upload of chunk " + str(chunkID))
        else:
            raise Exception("Failed to upload chunk " + str(chunkID))
    basic_functions.print_w("-> Done.")
        
    anaplan_import.mark_upload_as_complete()

    # get a list of import actions
    basic_functions.print_w("\nDoing the import")

    data = anaplan_import.list_import_actions()
    basic_functions.print_w("-> Import ID obtained?")

    importID = None
    for item in data['imports']:
        if item['importDataSourceId'] == fileID:
            importID = item['id']
            break

    if importID != None:
        basic_functions.print_w("---> Yes")
        anaplan_import.importID = importID
        basic_functions.print_w("---> importID: " + str(importID))

    else:
        basic_functions.print_w("---> No. Help is needed here")
        raise Exception("Import not found")

    # create new task
    basic_functions.print_w("\n-> Creating new task on Anaplan")
    response = anaplan_import.create_new_task()
    data = response.json()
    if data['status']['code'] == 200:
        basic_functions.print_w("---> Task creation successful")
        taskID = response.json()['task']['taskId']
        basic_functions.print_w("---> taskID: " + str(taskID))
        anaplan_import.taskID = taskID
    else:
        basic_functions.print_w("---> Task creation failed")
        basic_functions.print_w("---> Help is needed here")
        raise Exception("Task creation failed")

    # check status of import
    basic_functions.print_w("\n-> Completing the import task...")
    match anaplan_import.complete_import_task():
        case 0:
            basic_functions.print_w("---> Import finished successfully.")
        case 1:
            basic_functions.print_w("---> Import cancelled successfully.")
        case -1:
            raise Exception("Task was unsuccessful")
        case _:
            pass

    # get the metadata for the import action
    basic_functions.print_w("\nGetting import metadata")
    md = anaplan_import.get_metadata()
    basic_functions.print_w("-> Done.")

    # check dump file
    basic_functions.print_w("\nReading dump file")
    r = anaplan_import.check_dump_file()
    basic_functions.print_w("-> Is JSON detected?")
    if 'application/json' in r.headers['Content-Type']:
        basic_functions.print_w("---> Yes")
        try:
            basic_functions.print_w("-> Can it be read? ")
            data = r.json()
            basic_functions.print_w("---> Yes")
            basic_functions.print_w("---> Here it is:")
            basic_functions.print_w(data)
            if data['status']['code'] == 404:
                basic_functions.print_w("-> Seems like a dump file wasn't created\n---> Here's the import metadata:")
                basic_functions.print_w(md)
        except requests.exceptions.JSONDecodeError as e:
            basic_functions.print_w("---> No")
            basic_functions.print_w("---> Error info here: {e}")
            basic_functions.print_w("---> Printing raw response anyway: \n")
            basic_functions.print_w(r.text)
    else:
        basic_functions.print_w("---> No")
        basic_functions.print_w("---> Here's the full text:\n")
        basic_functions.print_w(r.text)

if __name__ == '__main__':
    main()
    print(f"{BRIGHT_WHITE}")