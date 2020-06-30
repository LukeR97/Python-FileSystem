from google.appengine.ext.webapp import blobstore_handlers
import main


# The Download Handler. filename will be the value from the html
# and getFile will retrieve that file from the ndb
class DownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self):
        fileName = self.request.get('fileName')
        file = main.getFile(fileName)
        self.send_blob(file.blob)
