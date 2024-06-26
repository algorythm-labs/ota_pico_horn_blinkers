import network
import urequests
import os
import json
import machine
from time import sleep

class OTAUpdater:
    """ This class handles OTA updates. It connects to the Wi-Fi, checks for updates, downloads and installs them."""
    def __init__(self, repo_url, filename):
        self.filename = filename
        self.repo_url = repo_url
        
        self.version_url = self.process_version_url(repo_url, filename)     # Process the new version url
        self.firmware_url = repo_url + filename                             # Removal of the 'main' branch to allow different sources

        if 'latest_code.py' in os.listdir():
            print(f'upgrade file exists')
            self.upgrade()

        # get the current version (stored in version.json)
        if 'version.json' in os.listdir():    
            with open('version.json') as f:
                self.current_version = json.load(f)['version']
            print(f"Current device firmware version is '{self.current_version}'")

        else:
            self.current_version = "0"
            # save the current version
            with open('version.json', 'w') as f:
                json.dump({'version': self.current_version}, f)
            
    def process_version_url(self, repo_url, filename):
        """ Convert the file's url to its assoicatied version based on Github's oid management."""

        # Necessary URL manipulations
        version_url = repo_url.replace("raw.githubusercontent.com", "github.com")  # Change the domain
        version_url = version_url.replace("/", "§", 4)                             # Temporary change for upcoming replace
        version_url = version_url.replace("/", "/latest-commit/", 1)                # Replacing for latest commit
        version_url = version_url.replace("§", "/", 4)                             # Rollback Temporary change
        version_url = version_url + filename                                       # Add the targeted filename
        
        return version_url

    def fetch_latest_code(self)->bool:
        """ Fetch the latest code from the repo, returns False if not found."""
        
        # Fetch the latest code from the repo.
        response = urequests.get(self.firmware_url)
        if response.status_code == 200:
            print(f'Fetched latest firmware code, status: {response.status_code}, -  {response.text}')
    
            # Save the fetched code to memory
            self.latest_code = response.text
            return True
        
        elif response.status_code == 404:
            print('Firmware not found.')
            return False

    def update_no_reset(self):
        """ Update the code without resetting the device."""

        # delete existing latest_code.py        
        try:
            os.remove('latest_code.py')
        except OSError:
            pass

        # Save the fetched code and update the version file to latest version.
        with open('latest_code.py', 'w') as f:
            f.write(self.latest_code)

        print(f'Current version & latest version: {self.current_version}, -  {self.latest_version}')
        
        # update the version in memory
        self.current_version = self.latest_version        

        print(f'Current version & latest version: {self.current_version}, -  {self.latest_version}')

        # save the current version
        with open('version.json', 'w') as f:
            json.dump({'version': self.current_version}, f)
        
        # free up some memory
        self.latest_code = None

    def upgrade(self):
        # Overwrite the old code.
        print("Upgrade to latest code")
        os.rename('latest_code.py', self.filename)
        self.restart()
    
    def restart(self):
        # Restart the device to run the new code.
        print("Restarting device... (don't worry about an error message after this")
        sleep(0.25)
        machine.reset()  # Reset the device to run the new code.
    
    def check_for_updates(self):
        """ Check if updates are available."""        

        print('Checking for latest version...')
        headers = {"accept": "application/json"} 
        response = urequests.get(self.version_url, headers=headers)
        
        data = json.loads(response.text)
       
        self.latest_version = data['oid']                   # Access directly the id managed by GitHub        
        print(f'Current version & latest version: {self.current_version}, -  {self.latest_version}')
        
        # compare versions
        newer_version_available = True if self.current_version != self.latest_version else False
        
        print(f'Newer version available: {newer_version_available}')    
        return newer_version_available    

    def list_software(self):
        if 'latest_code.py' in os.listdir():
            returner = "Upgrade exists"
        else:
            returner = "None"
        return returner
    
    def delete_temp(self):
        # delete existing latest_code.py        
        try:
            os.remove('latest_code.py')
        except OSError:
            pass
        # delete existing version.json
        try:
            os.remove('version.json')
        except OSError:
            pass