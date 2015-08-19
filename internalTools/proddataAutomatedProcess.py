import argparse
import tarfile
import zipfile
import boto
import os
from filechunkio import FileChunkIO
from s3multipart import s3mpdownload
import py7zlib
import jabilHtmlProcessor
#7z

def parseArgs(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-t","--tag_file_out",          help="specify the output path of the tag file",
            default="/home/ubuntu/data/proddata/tagFile.txt")
    parser.add_argument("-a","--tag_file_in",           help="specify the s3 input for the tag file",
            default="s3://hello-manufacturing/sense-data/tagFile.txt")
    parser.add_argument("-p","--tbp_folder_out",        help="what folder to use for files that need to be processed",
            default="/home/ubuntu/data/toBeProcessed")
    parser.add_argument("-f","--tbp_folder_in",         help="specify the s3 input for the to be processed folder",
            default="sense-data-to-process")
    parser.add_argument("-b","--tbp_bucket_in",         help="specify the s3 bucket for the to be processed folder",
            default="hello-manufacturing")
    parser.add_argument("-s","--skip_s3",               help="skip the s3 pulldown, basically useful if there's an error and files are now local",
            action="store_true")
    parser.add_argument("-e","--skip_es",    help="skip the elasticsearch html processing",
            action="store_true")

    if args:
        arguments = parser.parse_args(args)
    else:
        arguments = parser.parse_args()

    return arguments

def extractArchive(destPath,outputFolder):
    if destPath.endswith("zip") and zipfile.is_zipfile(destPath):
        try:
            with zipfile.Zipfile(destPath) as zipF:
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
    return false

def callHtmlProcessor(tbpFolder,tagFile):
    parserOptions = (tbpFolder,#make this argument first to avoid confusion/issues
                     "-o","/home/ubuntu/data/proddata",
                     "-s","/home/ubuntu/data/s3SyncDir",
                     "-f",tagFile,
                     "-r","-v")

    jabilHtmlProcessor.main(*parserOptions)


def main(*args):
    arguments = parseArgs(args)

    try:
        try:
            os.makedirs(arguments.tbp_folder_out)
        except OSError:
            pass
        f = open(os.path.join(arguments.tbp_folder_out,".tmp"),'w')
        f.close()
    except:
        print "Must have permissions on folder. Try running as sudo as data folder has restricted permissions\n"
        raise

    if not arguments.skip_s3:
        conn = boto.connect_s3()
        try:
            os.makedirs(os.path.split(arguments.tag_file_out)[0])
        except OSError:
            pass

        s3mpdownload.main(arguments.tag_file_in,arguments.tag_file_out, force=True)

        try:
            os.makedirs(arguments.tbp_folder_out)
        except OSError:
            pass

        buck = conn.get_bucket(arguments.tbp_bucket_in)

        for fileName in buck.list(prefix=arguments.tbp_folder_in):
            destPath = os.path.join(arguments.tbp_folder_out,os.path.split(fileName.key)[1])
            s3mpdownload.main(os.path.join("s3://",arguments.tbp_bucket_in,fileName.key),destPath,force=True)
            if extractArchive(destPath,arguments.tbp_folder_out):
                #TODO: Test this shiz
                buck.delete_key(fileName.key)
                os.remove(destPath)
    else:#assume there was a problem last time and files are in the right spot
        for fileName in os.listdir(arguments.tbp_folder_out):
            destPath = os.path.join(arguments.tbp_folder_out,fileName)
            if extractArchive(destPath,arguments.tbp_folder_out):
                os.remove(destPath)

    if not arguments.skip_es:
        callHtmlProcessor(arguments.tbp_folder_out,arguments.tag_file_out)


if __name__ == "__main__":
    main()
