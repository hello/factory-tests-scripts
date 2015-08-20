from s3multipart import s3mpdownload
from s3multipart import s3mpupload
import boto
import re
import os
import hashlib

def sync(connection, source, dest, queryIndividually=True):
    if os.path.exists(dest) and os.path.isfile(dest):
        raise TypeError("dest must be a folder path")
    if source.lower().startswith("s3://") and not dest.lower().startswith("s3://"):
        s3SourcePath = splitTotalKeyIntoParts(source)
        buck = conn.get_bucket(s3SourcePath[0])
        if s3SourcePath[2] == "":#source is directory
            for fileName in buck.list(prefix=s3SourcePath[1]+"/"):#without a slash, might request other keys
                leftover = fileName.name.lstrip(source)
                destPath = os.path.join(dest,leftover)
                if os.path.exists(destPath):
                    localHash = hashlib.md5(open(destPath, "rb").read()).hexdigest()
                    sourceHash = fileName.etag.strip('"')
                    if localHash == sourceHash:
                        continue
                try:
                    os.makedirs(os.path.split(destPath)[0])
                except OSError:
                    pass
                s3mpdownload.main(os.path.join(source,leftover), destPath, force=True)
        else:
            key = buck.get_key(source)
            if not key:
                raise IOError("Source file not found: %s" % source)
            leftover = key.name.lstrip(source)
            destPath = os.path.join(dest,leftover)
            localHash = "not"
            sourceHash = "equal"
            if os.path.exists(destPath):
                localHash = hashlib.md5(open(destPath, "rb").read()).hexdigest()
                sourceHash = fileName.etag.strip('"')
            if localHash != sourceHash:
                try:
                    os.makedirs(os.path.split(destPath)[0])
                except OSError:
                    pass
                s3mpdownload.main(os.path.join(source,leftover), destPath, force=True)
    elif not source.lower().startswith("s3://") and dest.lower().startswith("s3://"):
        s3DestPath = splitTotalKeyIntoParts(dest)






def splitTotalKeyIntoParts(totalKey):
    rePattern = "(?:[sS]3\:\/\/)?(.+?)?((/.*)?(/.*?))?$"
#group 0 = whole match
#group 1 = bucket
#group 2 = key without bucket
#group 3 = prefix (folders after bucket)
#group 4 = file name (or / if directory)
    reObj = re.search(rePattern,totalKey)
    if not reObj:
        return None
    else:
        return (reObj.group(1),reObj.group(3)[1:],reObj.group(4)[1:])

if __name__ == "__main__":
    conn = boto.connect_s3()
    sync(conn, "s3://hello-manufacturing/sense-data/","tmp")
