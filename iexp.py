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

            
    # l = '#EXTINF:356,Meri Hamjoliyaan   - Atif Aslam'
    # m = re.match('^#EXTINF:[0-9]{3,4},', l)
    # s= l[len(m.group()):] + '.mp3'

    # print os.path.join('.',' '.join(s.split()))
    
    # with open(m3u_file, 'rU') as fp:
    #     contents = fp.readlines()
    #     print contents
    #     for l in contents:
    #         print l

        # line = contents[0]
        # line2 = line.replace('\r','\n')
        # print line2
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export itunes an playlist to a user specified folder.')
    parser.add_argument('m3ufile', help='iTunes library file')
    parser.add_argument('folderpath', help='Export folder name')
    parser.add_argument('--copy', action='store_true')
    args = parser.parse_args()
    # print args
    
    process_m3u( args.m3ufile, args.folderpath, args.copy )