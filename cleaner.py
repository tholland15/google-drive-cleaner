#!/usr/bin/python

import httplib2
from pprint import pprint
import sys

import apiclient.discovery
from apiclient import errors
import oauth2client
from oauth2client import client
from oauth2client import tools
import os


# If modifying these scopes, delete your previously saved credentials
# at ./.credentials/GdriveOrphans-Creds.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'GDriveOrphans'

class DriveCleaner():
    def __init__(self, drive_service):
        self.drive = drive_service
        self.requests = 0
        self.total = 0
        self.moved = 0
        self.trashed = 0
        self.errors = 0
        self.orphans = []

    def __str__(self):
        return 'This session, ' + str(self.moved) + ' moved, ' + str(self.trashed) + ' trashed, ' + str(
            self.errors) + ' errors, with ' + str(self.total) + ' files currently listed'

    def findOrphans(self):
        keep_going = True
        next_token = None
        self.orphans = []
        self.requests = 0
        self.total = 0
        
        while keep_going:
            self.requests += 1
            print 'Making request ' + str(self.requests) + ' total files ' + str(self.total)
            f = None
            try:
                f = self.drive.files().list(maxResults=1000, pageToken=next_token).execute()
            except errors.HttpError, error:
                print 'HTTP Error Code %s Retrying...' % error.resp.status
                continue
            try:
                next_token = f['nextPageToken']
            except KeyError:
                next_token = None
                keep_going = False
            self.total += len(f['items'])
            
            # look for no parents
            self.orphans = self.orphans + self.noParentsMine(f['items'])
            
            # look for dead parents
            self.orphans = self.orphans + self.deadParentsMine(f['items'])
            
            print 'Orphan Count: ' + str(len(self.orphans))

    def noParents(self, file_list):
        return [x for x in file_list if len(x['parents']) == 0];

    def noParentsMine(self, file_list):
        return [x for x in self.noParents(file_list) if
                len(x['owners']) == 1 and x['owners'][0]['isAuthenticatedUser']]
                
    def deadParentsMine (self, file_list):
        # look for files whose parents return a 404
        dead_parents = []
        for file in file_list: 
            if len(file['owners']) == 1 and file['owners'][0]['isAuthenticatedUser']:
                dead_parent_count = 0
                for parent in file['parents']:
                    try:
                        self.drive.files().get(fileId=parent['id']).execute()
                    except errors.HttpError, error:
                        if error.resp.status == 404:
                            if file['labels'] and file['labels']['trashed']:
                                pass
                            else:
                                dead_parent_count += 1
                # if the parent count matches dead_parent_count, all parents are dead
                if len(file['parents']) == dead_parent_count:
                    dead_parents.append(file)
                    print 'File %s has dead parents' % file['title']
        return dead_parents             

    def trashItems(self, reload_files=False):
        if len(self.orphans) == 0 or reload_files:
            self.findOrphans()
        # find items we want to trash
        for item in self.orphans:
            # ... check to see if already trashed
            if item['labels'] and item['labels']['trashed']:
                # print '\tAlready in trash: ' + item['title'] + ' - ' + item['id']
                pass
            else:
                print '\tTrashing: ' + item['title'] + ' - ' + item['id'] + ' - ' + str(len(self.orphans) - self.trashed) + ' orphans left'
                try:
                    self.drive.files().trash(fileId=item['id']).execute()
                    self.trashed += 1
                except:
                    print '\t\t>>> ERROR TRASHING THIS FILE <<<'
                    self.errors += 1
        print str(self)

    def moveItems(self, folder, reload_files=False):
        """
        MoveItems will move all orphaned files into a particular folder.  Unlike trashItems,
        this function does not care whether the files are shared so long as they are owned
        by the current user.  Restricting the search to the current user avoids moving files
        owned by others that are "orphaned" because they are still in the "Shared with me"
        or "Incoming" folder).

        Arguments:
            folder (string): the id of the target folder
            reload_files (bool): optional, findOrphans before running the move
        """
        if len(self.orphans) == 0 or reload_files:
            self.findOrphans()
        #find items we want to move
        for item in self.orphans:
            # ... check to see if already trashed
            if item['labels'] and item['labels']['trashed']:
                # print '\tAlready in trash: ' + item['title'] + ' - ' + item['id']
                pass
            else:
                print '\tMoving: ' + item['title'] + ' - ' + item['id'] + ' - ' + str(len(self.orphans) - self.moved) + ' orphans left'
                try:
                    self.drive.parents().insert(fileId=item['id'], body={'id': folder}).execute()
                    self.moved += 1
                except errors.HttpError, error:
                    print '\t\t>>> ERROR MOVING THIS FILE <<<'
                    print '%s' % error
                    self.errors += 1
        print str(self)
        
    def countFiles(self, folder):
        keep_going = True
        next_token = None

        requests = 0
        total = 0
        while keep_going:
            self.requests += 1
            print 'Making request ' + str(requests) + ' total files so far ' + str(total)
            f = children = self.drive.children().list(folderId=folder, maxResults=1000, pageToken=next_token).execute()
            try:
                next_token = f['nextPageToken']
            except KeyError:
                next_token = None
                keep_going = False
            except:
                print "Unexpected error:", sys.exc_info()[0]
            total += len(f['items'])
            print 'Total Files: ' + str(total)

def get_credentials():
    try:
        import argparse
        flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
    except ImportError:
        flags = None

    home_dir = None
    path = os.path.realpath(sys.argv[0])
    if os.path.isdir(path):
        home_dir = path
    else:
        home_dir = os.path.dirname(path)
    #print 'dir: ' + str(home_dir)
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'GdriveOrphans-Creds.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def build_connection():
    
    credentials = get_credentials()

    # Create an httplib2.Http object and authorize it with our credentials
    http = httplib2.Http()
    http = credentials.authorize(http)
    drive_service = apiclient.discovery.build('drive', 'v2', http=http)

    # Create drivecleaner and run it
    dc = DriveCleaner(drive_service)
    print 'Connection Successful'
    return dc