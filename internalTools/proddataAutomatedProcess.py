#Readme
#Primary dev: Brandon Clarke
#Notes: This is made to sit on top of the jabil html parser and pull down files from s3 so they are processed,
#either automatically via cron or something, or just from the command line to pull down a certain data set.
#If putting on a new machine, make sure bogo is setup with the keys correctly for AWS

import argparse
import tarfile
import zipfile
import boto
import os
from filechunkio import FileChunkIO
from s3multipart import s3mpdownload
import py7zlib
import jabilHtmlProcessor
import helloS3
import tempfile

def parseArgs(args=None):
    """Command line parser"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-t","--tag_file_out",          help="specify the output path of the tag file",
            default="/home/ubuntu/data/s3SyncDir/tagFile.txt")
    parser.add_argument("-a","--tag_file_in",           help="specify the s3 input for the tag file",
            default="s3://hello-manufacturing/sense-data/tagFile.txt")
    parser.add_argument("-l","--list_file_out",         help="specify the output path of the list file")
    parser.add_argument("-i","--list_file_in",          help="specify the input path of the list file")
    parser.add_argument("-o","--tbp_folder_out",        help="what folder to use for files that need to be processed",
            default="/home/ubuntu/data/toBeProcessed")
    parser.add_argument("-f","--tbp_folder_in",         help="specify the s3 input for the to be processed folder",
            default="sense-data-to-process")
    parser.add_argument("-b","--tbp_bucket_in",         help="specify the s3 bucket for the to be processed folder",
            default="hello-manufacturing")
    parser.add_argument("-p","--skip_pulldown",         help="skip the s3 pulldown, basically useful if there's an error and files are now local",
            action="store_true")
    parser.add_argument("-e","--skip_es",               help="skip the elasticsearch html processing",
            action="store_true")
    parser.add_argument("-s","--skip_sync",             help="skip the s3 tar sync",
            action="store_true")
    parser.add_argument("-d","--delete_s3_src",         help="delete the s3 src (zip) files (DO NOT DO THIS ON hello-jabil BUCKET)",
            action="store_true")
    parser.add_argument("-v","--verbose",               help="lots of words, potentially",
            action="store_true")

    if args:
        arguments = parser.parse_args(args)
    else:
        arguments = parser.parse_args()

    return arguments

def extractArchive(destPath,outputFolder):
    """Supports different archive types"""
    if destPath.endswith("zip") and zipfile.is_zipfile(destPath):
        try:
            with zipfile.ZipFile(destPath) as zipF:
                zipF.extractall(outputFolder)
            return True
        except:
            return False
    elif destPath.endswith("tar.gz") and tarfile.is_tarfile(destPath):
        try:
            tar = tarfile.open(destPath)
            tar.extractall(outputFolder)
            tar.close()
            return True
        except:
            return False
    elif destPath.endswith("7z"):
        try:
            f = open(destPath,'rb')
            arc = py7zlib.Archive7z(f)
            for fileName in arc.getnames():
                outPath = os.path.join(outputFolder,fileName)
                try:
                    os.makedirs(os.path.dirname(outPath))
                except OSError:
                    pass
                outFP = open(outPath,'wb')
                outFP.write(arc.getmember(fileName).read())
                outFP.close()
            return True
        except:
            return False
        finally:
            f.close()
    return False

def callHtmlProcessor(tbpFolder,tagFile):
    """See the documentation in the jabilHtmlProcessor file"""
    parserOptions = (tbpFolder,
                     "-o","/home/ubuntu/data/proddata",
                     "-s","/home/ubuntu/data/s3SyncDir",
                     "-f",tagFile,
                     "-r","-v")

    jabilHtmlProcessor.main(*parserOptions)


def main(*args):
    arguments = parseArgs(args)

    try:#the instance this was originally installed on required sudo to access the data drive
        with tempfile.TemporaryFile(dir=arguments.tbp_folder_out) as f:
            pass
    except:
        print "\nMust have permissions on folder. Try running as sudo as data folder has restricted permissions\n"
        raise

    conn = boto.connect_s3()
    if not arguments.skip_pulldown:
        try:
            os.makedirs(os.path.split(arguments.tag_file_out)[0])
        except OSError:
            pass

        s3mpdownload.main(arguments.tag_file_in,arguments.tag_file_out, force=True)

        try:
            os.makedirs(arguments.tbp_folder_out)
        except OSError:
            pass

        filesProcessed = []
        if arguments.list_file_in:#ignore already processed archives (don't re-download all jabil uploaded data, or delete it)
            try:
                with open(arguments.list_file_in) as f:
                    filesProcessed = f.read().splitlines()
            except IOError:
                print "\nList file must exist if input is specified\n"
                raise

        buck = conn.get_bucket(arguments.tbp_bucket_in, validate=False)

        test = buck.list(prefix=arguments.tbp_folder_in)
        for fileName in test:
            if fileName.key in filesProcessed or fileName.key.endswith('/'):
                continue
            destPath = os.path.join(arguments.tbp_folder_out,os.path.split(fileName.key)[1])
            s3mpdownload.main(os.path.join("s3://",arguments.tbp_bucket_in,fileName.key),destPath,force=True)
            if arguments.verbose:
                print "Downloaded from S3: %s/%s" % (fileName.bucket, fileName.key)
            if extractArchive(destPath,arguments.tbp_folder_out):
                os.remove(destPath)
                if arguments.delete_s3_src:
                    buck.delete_key(fileName.key)
                    if arguments.verbose:
                        print "Deleted from s3: %s/%s" % (fileName.bucket, fileName.key)
                if arguments.list_file_out:
                    with open(arguments.list_file_out,'a') as f:
                        f.write(fileName.key+'\n')
    else:#assume there was a problem last time and files are in the right spot, or just don't need to be pulled down
        for fileName in os.listdir(arguments.tbp_folder_out):
            destPath = os.path.join(arguments.tbp_folder_out,fileName)
            if extractArchive(destPath,arguments.tbp_folder_out):
                os.remove(destPath)

    if not arguments.skip_es:
        callHtmlProcessor(arguments.tbp_folder_out,arguments.tag_file_out)

    if not arguments.skip_sync:#push compiled archives to S3
        print "Syncing..."
        helloS3.sync(conn,"/home/ubuntu/data/s3SyncDir/","s3://hello-manufacturing/sense-data/",dryRun=False,verbose=True, individualQuery=False)


if __name__ == "__main__":
    main()
