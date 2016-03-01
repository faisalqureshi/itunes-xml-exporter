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
    track_info['Track ID'] = '_'
    track_info['Name'] = '_'
    track_info['Artist'] = '_'
    track_info['Total Time'] = '_'
    track_info['Location'] = '_'
    track_info['Year'] = '_'
    track_info['Album'] = '_'
    
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



def get_playlist_name(playlist):
    i = 0
    while (i < len(playlist)):
        if playlist[i].tag == 'key' and playlist[i].text == 'Name':
            return playlist[i+1].text
        i += 1
    return ''


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


def make_playlist(playlist, track_db, rootfolder, share_music_files):
    import urllib2

    playlist_folder = os.path.join(rootfolder, playlist['Name'])
    playlist_file = os.path.join(playlist_folder, '%s.m3u' % playlist['Name'])
    create_filepath(playlist_file)
    print 'Writing', playlist_file,

    f = open(playlist_file, 'wb')
    s = '#EXTM3U\n'    
    f.write(s.encode('UTF-8'))
    
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
        new_filepath = os.path.join(playlist_folder, new_filename)
        
        if share_music_files:
            if not 'Copied Location' in track.keys():
                track['Copied Location'] = new_filepath
            else:
                new_filepath = track['Copied Location']
        
        if os.path.isfile(new_filepath) and os.stat(new_filepath).st_size == old_filesize:
            print '\nSkipping:', new_filepath, 'already exists'
        else:
            print '\nCopying\n', old_filepath, '\n->\n', new_filepath
            try:
                shutil.copyfile(old_filepath.encode('UTF-8'), new_filepath.encode('UTF-8'))
            except OSError as exc:                
                print 'Warning:', new_filepath, 'copy failed.'
                print exc
                continue

        s = '#EXTINF:%d,%s - %s\n' % (int(track['Total Time'])/1000, track['Name'], track['Artist'])
        f.write(s.encode('UTF-8'))
        s = '%s\n' % new_filename
        f.write(s.encode('UTF-8'))
        
    f.close()

    
def process_xml(xml_file, root_folder, exclude_playlists, share_music_files):
    import xml.etree.ElementTree as ET
    root = None
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except:
        print 'Error: cannot read', xml_file, 'quitting.'
        return
        
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
        playlist_name = get_playlist_name(playlist)
        if playlist_excluded(playlist_name, exclude_playlists):
            print 'Skipping playlist', playlist_name
            continue        
        playlist_info = get_playlist_info(playlist)
        playlist_db.append(playlist_info)

    print '... found', len(playlist_db), 'playlists'

    for playlist in playlist_db:
        make_playlist(playlist, track_db, root_folder, share_music_files)


def playlist_excluded(playlist, exclude_playlists):
    if playlist in exclude_playlists:
        return True
    return False

    
def process_exclude_from_file( exclude_file ):
    lines = []
    try:
        with open(exclude_file,'r') as f:
            for l in f:
                lines.append(l.strip())
        return lines
    except:
        print 'Warning: cannot open', exclude_file, 'ignoring.'
        return lines

        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Processes an iTunes.xml file and creates stand-alone playlist specific folders, which can be copied over to an SD card and played in car audio systems.')
    parser.add_argument('xmlfile', help='iTunes.xml file to be processed.')
    parser.add_argument('--root-folder', default='.', help='Root folder where playlists folders will be generated.')
    #parser.add_argument('--copy', action='store_true', help='Specify --copy to perform the actualy copying action.  Otherwise it is just a dry-run.')
    parser.add_argument('--exclude-from', type=str, action='store', help='Specify a file that contains playlist names (one per line) to be excluded during copying.')
    parser.add_argument('--donot-share-music-files', action='store_true', default=False, help='If not specified, the music files (mp3, ma4, etc.) will be copied once for each playlist.')
    args = parser.parse_args()
    # print args

    itunes_default_playlists = [
        'Ringtones',
        'Library',
        'Music',
        'Movies',
        'TV Shows',
        'Podcasts',
        'iTunes U',
        'iTunes_U',
        'Tones',
        'Audiobooks',
        'Music Videos',
        'Voice Memos',
        'Purchased'
    ]
    
    exclude_playlists = []
    if args.exclude_from:
        exclude_playlists = process_exclude_from_file( args.exclude_from )
    exclude_playlists.extend(itunes_default_playlists)
    
    process_xml( args.xmlfile, args.root_folder, exclude_playlists, not args.donot_share_music_files)
