import argparse
import tarfile
import zipfile
import boto
from filechunkio import FileChunkIO
from 3smultipart import s3mpdownload
#7z

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t","--tag_file_out",          help="specify the output path of the tag file",
            default="/home/ubuntu/toBeProcessed/tagFile.txt")
    parser.add_argument("-a","--tag_file_in",           help="specify the s3 input for the tag file",
            default="s3://hello-manufacturing/sense-data/tagFile.txt")
    parser.add_argument("-p","--tbp_folder_out",        help="what folder to use for files that need to be processed",
            default="/home/ubuntu/toBeProcessed")
    parser.add_argument("-b","--tbp_folder_in",         help="specify the s3 input for the to be processed folder",
            default="s3://hello-manufacturing/sense-data-to-process/")

    arguments = parser.parse_args()

    return arguments

def main():
    arguments = parseArgs()

    try:
        os.makedirs(os.path.split(arguments.tag_file_out)[0])
    except OSError:
        pass

    s3mpdownload.main(arguments.tag_file_in,arguments.tag_file_out)

    try:
        os.makedirs(arguments.tbp_folder_out)
    except OSError:
        pass

    s3mpdownload.main(arguments.tbp_folder_in,arguments.tbp_folder_out)




if __name__ == "__main__":
    main()
