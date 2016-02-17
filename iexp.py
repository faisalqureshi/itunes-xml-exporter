import argparse
import re
import os
import xml.etree.ElementTree as ET
import shutil

def process_m3u(m3u_file, folder, copy):

    p = re.compile('^#EXTINF:[0-9]{3,7},')

    with open(m3u_file, 'rU') as fp:
        debug = False

        contents = fp.read()
        contents.replace('\r', '\n')
        lines = contents.split('\n')

        filename = None
        i = 0
        for line in lines:
            i += 1
            if debug:
                print 'Processing:', i, line
            m = p.search(line)
            if m == None:
                if not filename == None:
                    filepath = os.path.join(folder,' '.join(filename.split()))
                    print '\nMoving:', line
                    print '\t->', filepath
                    if copy:
                        # shutil.copy(line, filepath)
                        print '\t... Done\n'
                    filename = None                    
            else:
                filename = line[len(m.group()):] + '.mp3'
        fp.close()

        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copy .mp3 files specified in a .m3u playlist file (exported via iTunes playlist export feature) to a specified folder.  This can be used to, for example, copy .mp3 in a folder on an SD card to be used in a car audio system.')
    parser.add_argument('m3ufile', help='.m3u playlist file exported from iTunes via playlist export feature.')
    parser.add_argument('folderpath', help='Export folderpath where mp3 files will be copied')
    parser.add_argument('--copy', action='store_true', help='Specify --copy to perform the actualy copying action.  Otherwise it is just a dry-run.')
    args = parser.parse_args()
    # print args
    
    process_m3u( args.m3ufile, args.folderpath, args.copy )
