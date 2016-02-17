import argparse
import re
import os
import xml.etree.ElementTree as ET
import shutil


def md5(fname):
    hash = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    return hash.hexdigest()


def create_filepath(filepath):
    if not os.path.exists(os.path.dirname(filepath)):
        try:
            os.makedirs(os.path.dirname(filepath))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

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

        
def get_track_info(track):
    track_info = {}
    i = 0
    while (i < len(track)):
        if track[i].tag == 'key' and track[i].text == 'Track ID':
            track_info['Track ID'] = track[i+1].text 
        if track[i].tag == 'key' and track[i].text == 'Name':
            track_info['Name'] = track[i+1].text 
        if track[i].tag == 'key' and track[i].text == 'Artist':
            track_info['Artist'] = track[i+1].text 
        if track[i].tag == 'key' and track[i].text == 'Total Time':
            track_info['Total Time'] = track[i+1].text 
        if track[i].tag == 'key' and track[i].text == 'Location':
            track_info['Location'] = track[i+1].text 
        if track[i].tag == 'key' and track[i].text == 'Year':
            track_info['Year'] = track[i+1].text
        if track[i].tag == 'key' and track[i].text == 'Album':
            track_info['Album'] = track[i+1].text
        i += 1
    return track_info


def get_playlist_info(playlist):
    playlist_info = {}
    i = 0
    while (i < len(playlist)):
        if playlist[i].tag == 'key' and playlist[i].text == 'Name':
            playlist_info['Name'] = playlist[i+1].text 
        i += 1

    song_ids = playlist.findall("./array/dict/integer")
    playlist_info['Song IDs'] = []
    for id in song_ids:
        playlist_info['Song IDs'].append(id.text)

    return playlist_info


def make_playlist(playlist, track_db):
    import urllib2

    playlist_folder = os.path.join('.', playlist['Name'])
    playlist_file = os.path.join(playlist_folder, '%s.m3u' % playlist['Name'])
    create_filepath(playlist_file)
    print 'Writing', playlist_file,

    f = open(playlist_file, 'w')
    f.write('#EXTM3U\n')
    
    for id in playlist['Song IDs']:
        if not id in track_db.keys():
            print 'Warning: song', id, 'not found in track_db. Skipping.'
            continue
        track = track_db[id]
        old_filepath = urllib2.url2pathname(track['Location']).replace('file://','')
        if not os.path.isfile(old_filepath):
            print 'Warning:', old_filepath, 'not found. Skipping.'
            continue;
        old_filesize = os.stat(old_filepath).st_size 
        _, file_extension = os.path.splitext(old_filepath)
        new_filename = '%s-%s-%s-%s%s' % (track['Year'],track['Album'],track['Artist'],track['Name'], file_extension) 
        new_filepath = os.path.join(playlist_folder,new_filename)

        if os.path.isfile(new_filepath) and os.stat(new_filepath).st_size == old_filesize:
            print '\nSkipping', old_filepath, 'already exists'
            f.write('#EXTINF:%d,%s - %s\n' % (int(track['Total Time'])/1000, track['Name'], track['Artist']))
            f.write('%s\n' % new_filepath)
        else:
            print '\nCopying\n', old_filepath, '\n->\n', os.path.join(playlist_folder,new_filepath)
            try:
                shutil.copyfile(old_filepath, new_filepath)
                f.write('#EXTINF:%d,%s - %s\n' % (int(track['Total Time'])/1000, track['Name'], track['Artist']))
                f.write('%s\n' % new_filepath)
            except:
                print 'Warning: copy failed.'
    f.close()

    
def process_xml( xml_file ):
    import xml.etree.ElementTree as ET
    tree = ET.parse(xml_file)
    root = tree.getroot()

    tracks = root.findall(".//dict/[key='Tracks']")
    playlists = root.findall(".//dict/[key='Playlists']")

    track_db = {}
    playlist_db = []
    
    print 'Processing tracks',
    track_list = tracks[0].findall("./dict/dict/[key='Track ID']")
    for track in track_list:
        track_info =  get_track_info( track )
        track_db[track_info['Track ID']] = track_info

    print '... found', len(track_db), 'tracks'
        
    print 'Processing playlists',        
    playlist_list = playlists[0].findall("./array/dict/[key='Playlist ID']")
    for playlist in playlist_list:
        playlist_info = get_playlist_info(playlist)
        playlist_db.append(playlist_info)

    print '... found', len(playlist_db), 'playlists'

    for playlist in playlist_db:
        make_playlist(playlist, track_db)
        
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copy .mp3 files specified in a .m3u playlist file (exported via iTunes playlist export feature) to a specified folder.  This can be used to, for example, copy .mp3 in a folder on an SD card to be used in a car audio system.')
    parser.add_argument('--xml', action='store_true', help='When specified, the program processes the iTunes xml file.')
    parser.add_argument('m3ufile', help='.m3u playlist file exported from iTunes via playlist export feature.')
    parser.add_argument('folderpath', help='Export folderpath where mp3 files will be copied')
    parser.add_argument('--copy', action='store_true', help='Specify --copy to perform the actualy copying action.  Otherwise it is just a dry-run.')
    args = parser.parse_args()
    # print args

    if not args.xml: 
        process_m3u( args.m3ufile, args.folderpath, args.copy )
    else:
        process_xml( args.m3ufile )
