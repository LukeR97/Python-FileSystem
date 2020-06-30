from google.appengine.ext import ndb


# Our directory model
class Directory(ndb.Model):
    name = ndb.StringProperty()
    parent = ndb.KeyProperty()
    path = ndb.StringProperty()
    directories = ndb.KeyProperty(repeated=True)
    files = ndb.KeyProperty(repeated=True)
