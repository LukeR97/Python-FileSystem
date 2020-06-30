import webapp2
import jinja2
import os
from myuser import MyUser
from directory import Directory
from file import File
from uploadhandler import UploadHandler
from downloadhandler import DownloadHandler
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True
)


# This will return the current user
def getUser():
    return users.get_current_user()


# This will return the key of a stored user from the ndb.
# If no user exists, then nothing is returned
def getStoredUser():
    user = getUser()
    if user:
        my_user_key = ndb.Key(MyUser, user.user_id())
        return my_user_key.get()


# This will add a new user. It takes the current user as an argument
# We then call the addRoot function, which will assign a root directory
# to this user. We then set the users current directory to the root
# this new user is then added to the ndb
def addUser(user):
    my_user = MyUser(id=user.user_id())
    addRoot(my_user)
    my_user.currentDir = ndb.Key(Directory, my_user.key.id() + '/')
    my_user.put()


# This function will add a root directory to a given user. We only pass new users here.
# It will assign the required parameters which the Directory model requires.
# we then add this to the ndb
def addRoot(my_user):
    directory_id = my_user.key.id() + '/'
    directory = Directory(id=directory_id)
    directory.name = 'root'
    directory.parent = None
    directory.path = '/'
    directory.put()
    my_user.root = directory.key
    my_user.put()


# This function will simply check if there is a current user.
# This tells us if there is a user logged in currently or not
def checkLogin():
    return True if getUser() else False


# This function will take a user, a directory name and a parent directory
# We then find the current path, using the parent. We then assign a new
# entry to the ndb and populate the required directory model attributes
def addDirectory(my_user, name, parentKey):
    parent = parentKey.get()
    path = getPath(name, parent)
    directory_id = my_user.key.id() + path
    directory = Directory(id=directory_id)
    if exists(directory.key, parent.directories):
        parent.directories.append(directory.key)
        parent.put()
        directory.parent = parentKey
        directory.name = name
        directory.path = path
        directory.put()


# This function takes a file, a name, a size and a date
# It is called from within the upload handler, so we need to
# find what user we are uploading to. We find the current directory
# we are adding to and then create an entry in the ndb for that file
# To avoid duplicates, we check if it already exists and just replcace
# it if it does. We then populate with the file models attributes
def addFile(upload, fileName, fileSize, createdAt):
    my_user = getStoredUser()
    current_Directory = currentDirectory()
    file_id = my_user.key.id() + getPath(fileName, current_Directory)
    file_key = ndb.Key(File, file_id)

    if exists(file_key, current_Directory.files):
        filetoUpload = File(id=file_id)
        filetoUpload.name = fileName
        filetoUpload.size = fileSize
        filetoUpload.createdAt = createdAt
        filetoUpload.blob = upload.key()
        filetoUpload.put()
        current_Directory.files.append(file_key)
        current_Directory.put()

    else:
        blobstore.delete(upload.key())


# This function simply checks if a given key already exists in a given list of keys
# It returns a boolean
def exists(key, key_list):
    return key not in key_list


# This function takes a user and a directory name to delete. In order to delete a directory
# We need to set the new current directory as the parent of the one we are deleting.
# We then replace the current directory with the parent and delete the directory passed
# through
def directoryDelete(my_user, name):
    parentDirectory = currentDirectory()
    directory_id = my_user.key.id() + getPath(name, parentDirectory)
    directory_key = ndb.Key(Directory, directory_id)
    directory = directory_key.get()
    if checkDirContents(directory):
        parentDirectory.directories.remove(directory_key)
        parentDirectory.put()
        directory_key.delete()


# This function takes a user and a file name
# We perform the same steps as the above function, however we also need the extra
# step of removing the file from the blobstore
def fileDelete(my_user, name):
    parentDirectory = currentDirectory()
    filePath = getPath(name, parentDirectory)
    file_id = my_user.key.id() + filePath
    file_key = ndb.Key(File, file_id)
    parentDirectory.files.remove(file_key)
    parentDirectory.put()
    blobstore.delete(file_key.get().blob)
    file_key.delete()


# This function takes a directory as an argument and returns True or False
# if there are any contents (files or directories) in the current directory
def checkDirContents(directory):
    return not directory.files and not directory.directories


# This function is used by the download handler. It simply retrieves a file
# using the current user, the directory and the name provided.
# The key of this file is then passed back to the download handler
def getFile(fileName):
    my_user = getStoredUser()
    parentDir = currentDirectory()
    filePath = getPath(fileName, parentDir)
    file_id = my_user.key.id() + filePath
    file_key = ndb.Key(File, file_id)
    return file_key.get()


# This function will provide the full path.
# We take the name of a directory and its parent.
# If we are in the root directory, then we do not append a / to the beggining
# The root won't have a parent so it will simply have a "/" as the path
def getPath(name, parentDir):
    if isRoot():
        return parentDir.path + name
    else:
        return parentDir.path + '/' + name


# This function will check to see if the current directory is equal to root
# Only the root will have no parent, we check to see if the parent attribute is empty
def isRoot():
    currentDir = currentDirectory()
    return True if currentDir.parent is None else False


# This function will return a key for the current directory.
# We need to take in the current user here as this function is required by other functions
def currentDirKey():
    my_user = getStoredUser()
    return my_user.currentDir


# This function will perform a get request and return the key of the current directory for a user
def currentDirectory():
    return currentDirKey().get()


# This function will return the the parent of the current directory
# We first need to get the current directory key and then we return it's parent
def parentDir():
    currentDir = currentDirKey()
    return currentDir.get().parent


# This function will take a given user and set the current directory it that directories parent
# We need to check if the user is already in the root directory and if they are not
# we can then change the current directory to the parent
def gotoParent(my_user):
    if not isRoot():
        parentDirectory_key = parentDir()
        my_user.currentDir = parentDirectory_key
        my_user.put()


# This function will navigate the user to the home directory.
# We simply take a user and set their current directory to "/" which is root
def gotoHome(my_user):
    my_user.currentDir = ndb.Key(Directory, my_user.key.id() + '/')
    my_user.put()


# This function is used when a user is navigating to a normal directory
# We take a user and the directory we wish to go to's name.
# We then find that directory's key using the name and then set the current
# directory to the key we found
def gotoDir(my_user, name):
    parentDirectory = currentDirectory()
    directory_id = my_user.key.id() + getPath(name, parentDirectory)
    directory_key = ndb.Key(Directory, directory_id)
    my_user.currentDir = directory_key
    my_user.put()


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        # Check to see if a user is already logged in or if a user already exists
        if checkLogin() or getStoredUser() is True:
            if not getStoredUser():
                # add a new user using the current user
                addUser(getUser())
            # Bring the user to the root directory
            self.navigate()
            # Get all the available directories in the current path
            # Then populate a list with the directory names
            currentPath = currentDirectory().directories
            pathNames = list()
            for path in currentPath:
                pathNames.append(path.get().name)
            # get all the available files in the current directory path
            # Then populate 3 lists with their names, sizes and creation dates
            currentFiles = currentDirectory().files
            fileNames = list()
            for file in currentFiles:
                fileNames.append(file.get().name)
            fileSizes = list()
            for file in currentFiles:
                fileSizes.append(file.get().size)
            fileCreation = list()
            for file in currentFiles:
                fileCreation.append(file.get().createdAt)

            # Values to populate the html for logged in
            template_values = {
                'logoutUrl': users.create_logout_url(self.request.uri),
                'user': getUser(),
                'directories': pathNames,
                'files': fileNames,
                'fileSize': fileSizes,
                'createdAt': fileCreation,
                'currentPath': currentDirectory().path,
                'isRootFalse': not isRoot(),
                'uploadUrl': blobstore.create_upload_url('/upload')
            }
            template = JINJA_ENVIRONMENT.get_template('main.html')
            self.response.write(template.render(template_values))

        else:
            # If we are not logged in, then populate the login url
            template_values = {
                'loginUrl': users.create_login_url(self.request.uri)
            }
            template = JINJA_ENVIRONMENT.get_template('login.html')
            self.response.write(template.render(template_values))

    def post(self):
        self.response.headers['Content-Type'] = 'text/html'
        # When a button is interacted with in the html
        request = self.request.get('button')
        # Each button has a value and we determine the behaviour
        # depending on the button that was clicked
        if request == 'add':
            self.add()
            self.redirect('/')

        elif request == 'delete':
            self.delete()
            self.redirect('/')

        elif request == 'parent':
            gotoParent(getStoredUser())
            self.redirect('/')

        elif request == 'home':
            gotoHome(getStoredUser())
            self.redirect('/')

    # When the add a directory textbox submit button is pressed
    # We take the value that was entered and check to see if it was
    # blank or if it already exists. We then pass the value to the
    # addDirectory function
    def add(self):
        dirName = self.request.get('dirname')
        if not (dirName is None or dirName == ''):
            addDirectory(getStoredUser(), dirName, currentDirKey())

    # Here we are checking to see if the user wants to delete a file
    # or a directory. Once this is determined, we then pass the user
    # and the value to the appropriate delete function
    def delete(self):
        name = self.request.get('name')
        type = self.request.get('type')
        if type == 'file':
            fileDelete(getStoredUser(), name)

        else:
            directoryDelete(getStoredUser(), name)

    # Here we take the value from the html and pass this to
    # the gotoDir function, we will then redirect the user
    # to that directory
    def navigate(self):
        dirName = self.request.get('dirname')
        if dirName != '':
            gotoDir(getStoredUser(), dirName)
            self.redirect('/')


app = webapp2.WSGIApplication(
    [
        ('/', MainPage),
        ('/upload', UploadHandler),
        ('/download', DownloadHandler)
    ], debug=True)
