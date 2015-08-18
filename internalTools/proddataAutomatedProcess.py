import argparse
import tarfile
import zipfile
import boto
import os
from filechunkio import FileChunkIO
from s3multipart import s3mpdownload
from pylzma import py7zlib
#7z

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t","--tag_file_out",          help="specify the output path of the tag file",
            default="/home/ubuntu/proddata/tagFile.txt")
    parser.add_argument("-a","--tag_file_in",           help="specify the s3 input for the tag file",
            default="s3://hello-manufacturing/sense-data/tagFile.txt")
    parser.add_argument("-p","--tbp_folder_out",        help="what folder to use for files that need to be processed",
            default="/home/ubuntu/toBeProcessed")
    parser.add_argument("-f","--tbp_folder_in",         help="specify the s3 input for the to be processed folder",
            default="sense-data-to-process")
    parser.add_argument("-b","--tbp_bucket_in",         help="specify the s3 bucket for the to be processed folder",
            default="hello-manufacturing")
    parser.add_argument("-s","--skip_s3",               help="skip the s3 pulldown, basically useful if there's an error and files are now local",
            action="store_true")

    arguments = parser.parse_args()

    return arguments

def extractArchive(destPath,outputFolder):
    if destPath.endswith("zip") and zipfile.is_zipfile(destPath):
        with zipfile.Zipfile(destPath) as zipF:
            zipF.extractall(outputFolder)
        return true
    elif destPath.endswith("tar.gz") and tarfile.is_tarfile(destPath):
        tar = tarfile.open(destPath)
        tar.extractall(outputFolder)
        tar.close()
        return true
    elif destPath.endswith("7z"):
        try:
            f = open(destPath,'rb')
            arc = py7zlib.Archive7z(f)
            for fileName in arc.getnames():
                outPath = os.path.join(arguments.tbp_folder_out,fileName)
                try:
                    os.makedirs(os.path.dirname(outPath))
                except OSError:
                    pass
                outFP = open(outPath,'wb')
                outFP.write(arc.getmember(fileName).read())
                outFP.close()
            return true
        finally:
            f.close()
    return false

def main():
    arguments = parseArgs()

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
            extractArchive(destPath,arguments.tbp_folder_out)
    else:#assume there was a problem last time and files are in the right spot
        for fileName in os.listdir(arguments.tbp_folder_out):
            destPath = os.path.join(arguments.tbp_folder_out,fileName)
            extractArchive(destPath,arguments.tbp_folder_out)



if __name__ == "__main__":
    main()
