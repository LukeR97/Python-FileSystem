from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
import main


# Our Upload Handler.
# When a file is uploaded in the html form, we store the information
# in the blobstore and then call the addFile to also add this to the ndb
class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        uploads = self.get_uploads()
        for upload in uploads:
            fileName = blobstore.BlobInfo(upload.key()).filename
            fileSize = blobstore.BlobInfo(upload.key()).size
            createdAt = blobstore.BlobInfo(upload.key()).creation
            main.addFile(upload, fileName, fileSize, createdAt)

        self.redirect('/')
