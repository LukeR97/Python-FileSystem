from google.appengine.ext import ndb


# Our file model
class File(ndb.Model):
    name = ndb.StringProperty()
    size = ndb.IntegerProperty()
    createdAt = ndb.DateTimeProperty()
    blob = ndb.BlobKeyProperty()
