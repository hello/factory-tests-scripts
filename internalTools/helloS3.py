from s3multipart import s3mpdownload
from s3multipart import s3mpupload
import boto
import re
import os
import hashlib

def sync(conn, source, dest, verbose = False, dryRun=False, individualQuery=True):
    if source.lower().startswith("s3://") and not dest.lower().startswith("s3://"):
        if os.path.exists(dest) and os.path.isfile(dest):
            raise TypeError("dest must be a folder path")
        s3SourcePath = splitTotalKeyIntoParts(source)
        buck = conn.get_bucket(s3SourcePath[0])
        if s3SourcePath[2] == "":#source is directory
            for key in buck.list(prefix=s3SourcePath[1]+"/"):#without a slash, might request other keys
                fullKeyPath = "s3://" + s3SourcePath[0] + '/' + key.name
                leftover = key.name.replace(s3SourcePath[1],"")
                leftover = leftover.lstrip('/')
                leftover = leftover.replace('/',os.pathsep)
                destPath = os.path.join(dest,leftover)
                if os.path.exists(destPath):
                    localHash = hashlib.md5(open(destPath, "rb").read()).hexdigest()
                    sourceHash = key.etag.strip('"')
                    if localHash == sourceHash:
                        continue
                try:
                    os.makedirs(os.path.split(destPath)[0])
                except OSError:
                    pass
                if dryRun or verbose:
                    print "%s --> %s" % (fullKeyPath,destPath)
                if not dryRun:
                    s3mpdownload.main(fullKeyPath, destPath, force=True)
        else:
            key = buck.get_key(s3SourcePath[1]+'/'+s3SourcePath[2])
            if not key:
                raise IOError("Source file not found: %s" % source)
            destPath = os.path.join(dest,os.path.split(source)[1])
            sourceHash = "not"
            destHash = "equal"
            if os.path.exists(destPath):
                sourceHash = key.etag.strip('"')
                destHash = hashlib.md5(open(destPath, "rb").read()).hexdigest()
            if sourceHash != destHash:
                try:
                    os.makedirs(dest)
                except OSError:
                    pass
                if dryRun or verbose:
                    print "%s --> %s" % (source,destPath)
                if not dryRun:
                    s3mpdownload.main(source, destPath, force=True)
    elif not source.lower().startswith("s3://") and dest.lower().startswith("s3://"):
        if not os.path.exists(source):
            raise IOError("Source path not found")
        if not dest.endswith('/'):#more forgiving than throwing an error
            dest = dest + '/'
        s3DestPath = splitTotalKeyIntoParts(dest)
        buck = conn.get_bucket(s3DestPath[0])
        if os.path.isfile(source):#individual file
            fileName = os.path.split(source)[1]
            key = buck.get_key(s3DestPath[1]+'/'+fileName)
            sourceHash = "not"
            destHash = "equal"
            if key:
                sourceHash = hashlib.md5(open(source, "rb").read()).hexdigest()
                destHash = key.etag.strip('"')
            if sourceHash != destHash:
                if dryRun or verbose:
                    print "%s --> %s" % (source,dest+fileName)
                if not dryRun:
                    s3mpupload.main(open(source),dest+fileName,force=True)
        else:
            if individualQuery:
                for root, dirs, fileNames in os.walk(source):
                    for fileName in fileNames:
                        filePath = os.path.join(root,fileName)
                        leftover = filePath.replace(source,"")
                        leftover = leftover.replace('\\','/')
                        leftover = leftover.lstrip('/')
                        key = buck.get_key(s3DestPath[1]+'/'+leftover)
                        sourceHash = "not"
                        destHash = "equal"
                        if key:
                            sourceHash = hashlib.md5(open(filePath, "rb").read()).hexdigest()
                            destHash = key.etag.strip('"')
                        if sourceHash != destHash:
                            if dryRun or verbose:
                                print "%s --> %s" % (filePath,dest.rstrip('/')+'/'+leftover)
                            if not dryRun:
                                s3mpupload.main(open(filePath),dest.rstrip('/')+'/'+leftover,force=True)
            else:
                hashes = {}
                for key in buck.list(prefix=s3DestPath[1]+"/"):#without a slash, might request other keys
                    hashes[key.name] = key.etag.strip('"')
                for root, dirs, fileNames in os.walk(source):
                    for fileName in fileNames:
                        filePath = os.path.join(root,fileName)
                        leftover = filePath.replace(source,"")
                        leftover = leftover.replace('\\','/')
                        leftover = leftover.lstrip('/')
                        sourceHash = "not"
                        destHash = "equal"
                        try:
                            destHash = hashes[s3DestPath[1]+'/'+leftover]
                            sourceHash = hashlib.md5(open(filePath, "rb").read()).hexdigest()
                        except KeyError:
                            pass
                        if sourceHash != destHash:
                            if dryRun or verbose:
                                print "%s --> %s" % (filePath,dest.rstrip('/')+'/'+leftover)
                            if not dryRun:
                                s3mpupload.main(open(filePath),dest.rstrip('/')+'/'+leftover,force=True)




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
    sync(conn, "tmp", "s3://hello-manufacturing/sense-data-to-process/", individualQuery=True)
