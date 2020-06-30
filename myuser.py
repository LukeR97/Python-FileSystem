from google.appengine.ext import ndb


# Our User model
class MyUser(ndb.Model):
    root = ndb.KeyProperty()
    currentDir = ndb.KeyProperty()
