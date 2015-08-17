import argparse
import tarfile
import zipfile
import boto
import os
from filechunkio import FileChunkIO
from s3multipart import s3mpdownload
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

    arguments = parser.parse_args()

    return arguments

def main():
    arguments = parseArgs()
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
        s3mpdownload.main(os.path.join("s3://",arguments.tbp_bucket_in,fileName.key),os.path.join(arguments.tbp_folder_out,os.path.split(fileName.key)[1]),force=True)


if __name__ == "__main__":
    main()
