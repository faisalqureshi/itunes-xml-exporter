import argparse
import re
import os
import xml.etree.ElementTree as ET
import shutil
import sys
import errno


def make_a_nicer_filename(old_filepath, track, filename_length):
    # print filename_length
    
    old_filename = os.path.basename(old_filepath)
    _, file_extension = os.path.splitext(old_filepath)

    year = track['Year'].encode('utf-8')
    album = track['Album'].encode('utf-8')
    artist = track['Artist'].encode('utf-8')
    name = track['Name'].encode('utf-8')

    new_filename = ''
    if len(name) > 0:
        new_filename = name
    if len(artist) > 0 and len(artist)+len(new_filename)+4 < filename_length:
        new_filename += (' - ' + artist)
    if len(album) > 0 and len(album)+len(new_filename)+4 < filename_length:
        new_filename += (' - ' + album)
    if len(year) > 0 and len(year)+len(new_filename)+4 < filename_length:
        new_filename += (' - ' + year)

    if len(new_filename) > 0:
        new_filename += file_extension
    else:
        new_filename = old_filename
        
    return sanitize_filename(new_filename)

def make_a_nice_filename(old_filepath, track, filename_length):
    # print filename_length
    
    old_filename = os.path.basename(old_filepath)
    _, file_extension = os.path.splitext(old_filepath)

    year = track['Year'].encode('utf-8')
    album = track['Album'].encode('utf-8')
    artist = track['Artist'].encode('utf-8')
    name = track['Name'].encode('utf-8')

    yaan = len(year)+len(album)+len(artist)+len(name)
    aan = len(album)+len(artist)+len(name)
    
    new_filename = ''
    if len(year) > 0 and yaan < (filename_length-4):
        new_filename += (year + ' - ')
    if aan <= (filename_length-4):
        if len(album) > 0: new_filename += (album + ' - ')
        if len(artist) > 0: new_filename += (artist + ' - ')
    else:
        if len(album) + len(name) < (filename_length-4):
            new_filename += (album + ' - ')
        elif len(artist) + len(name) < (filename_length-4):
            new_filename += (artist + ' - ')
    if len(name) > 0:
        new_filename += (name + file_extension)
    else:
        new_filename += old_filename
        
    return sanitize_filename(new_filename)

    
def is_valid_filename(filename):
    bad_filenames = ['com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9', 'con', 'nul', 'prn']
    bad_chars = set('/?<>\*,|^:"')
    if filename in bad_filenames:
        return False
    
    return len(bad_chars & set(filename)) == 0


def sanitize_filename(filename):
    bad_chars = set('/?<>\*,|^:"')
    r = ''
    for c in filename:
        if c in bad_chars:
            r += '_'
        else:
            r += c
    return r


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


def make_playlist(playlist, track_db, rootfolder, share_music_files, verbose, dry_run, fname_len, nicer_names):
    import urllib2
    
    playlist_folder = os.path.join(rootfolder, sanitize_filename(playlist['Name']))
    if verbose: print 'playlist folder:', playlist['Name']
    
    playlist_filename = '%s.m3u' % sanitize_filename(playlist['Name'])
    if verbose: print 'playlist file:', playlist_filename
    playlist_file = os.path.join(playlist_folder, playlist_filename)

    f = None
    if dry_run:
        print 'Dry run: creating playlist file', playlist_file
    else:   
        if verbose: print 'Creating playlist file', playlist_file
        create_filepath(playlist_file)
        try:
            f = open(playlist_file, 'wb')
            s = '#EXTM3U\n'    
            f.write(s.encode('UTF-8'))
        except:
            print 'Warning: error opening', playlist_file, 'skipping this playlist'
            if f: f.close()
            return

    for id in playlist['Song IDs']:
        if not id in track_db.keys():
            print '\tWarning: song', id, 'not found in track_db. Skipping.'
            continue
        track = track_db[id]

        old_filepath = urllib2.url2pathname(track['Location']).replace('file://','')
        if not os.path.isfile(old_filepath):
            print '\tWarning:', old_filepath, 'not found. Skipping.'
            continue;
        old_filesize = os.stat(old_filepath).st_size 
        
        _, file_extension = os.path.splitext(old_filepath)
        if nicer_names:
            new_filename = make_a_nicer_filename(old_filepath, track, fname_len)
        else:
            new_filename = make_a_nice_filename(old_filepath, track, fname_len)
        new_filepath = os.path.join(playlist_folder, new_filename.decode('utf-8'))
        
        if os.path.isfile(new_filepath) and os.stat(new_filepath).st_size == old_filesize:
            print '\tSkipping:', new_filepath, 'already exists'
        else:
            if dry_run:
                print '\tDry run: copying', old_filepath, ' to ', new_filepath
            else:
                print '\tCopying', old_filepath, ' to ', new_filepath
                try:
                    shutil.copyfile(old_filepath.decode('utf-8'), new_filepath)
                except:                
                    print '\tWarning: ', new_filepath, ' copy failed.'
                    continue
                    
        if f:
            try:
                s = u'#EXTINF:%d,%s - %s\n' % (int(track['Total Time'])/1000, track['Name'], track['Artist'])
                f.write(s.encode('UTF-8'))
                s = '%s\n' % new_filename.decode('utf-8')
                f.write(s.encode('utf-8'))
            except:
                print '\tWarning: error writing to playlist file, skipping this playlist'
                if f: f.close()
                return

    if f: f.close()


def save_playlist_list_to_file(playlist_list_export_filename, playlist_db):
    f = None
    try:
        with open(playlist_list_export_filename, 'w') as f:
            for playlist in playlist_db:
                print 'playlist:', playlist['Name']
                f.write('%s\n' % playlist['Name'].encode('utf8'))
    except:
        print 'Error export playlists to', playlist_list_export_filename
    if f: f.close()    

    
def process_xml(xml_file, root_folder, exclude_playlists, share_music_files, verbose, dry_run, export_playlist_name, fname_len, playlist_list_export, include_playlists, nicer_names):
    import xml.etree.ElementTree as ET
    root = None
    print 'Reading', xml_file,
    sys.stdout.flush()
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        print '... success.'
    except:
        print '... failure.'
        return
        
    
    print 'Finding tracks',
    sys.stdout.flush()
    tracks = root.findall(".//dict/[key='Tracks']")
    track_db = {}    
    track_list = tracks[0].findall("./dict/dict/[key='Track ID']")
    for track in track_list:
        track_info =  get_track_info( track )
        track_db[track_info['Track ID']] = track_info
    print '... found', len(track_db), 'tracks'
        
    print 'Finding playlists',
    sys.stdout.flush()
    playlists = root.findall(".//dict/[key='Playlists']")
    playlist_db = []
    num_playlists_found = 0
    num_playlists_skipped = 0
    playlist_list = playlists[0].findall("./array/dict/[key='Playlist ID']")
    for playlist in playlist_list:
        num_playlists_found += 1
        playlist_name = get_playlist_name(playlist)
        if verbose: print '\nplaylist found:', playlist_name,
        if playlist_in_the_list(playlist_name, exclude_playlists):
            num_playlists_skipped += 1
            if verbose: print '.. skipped',
            continue
        # Option 1: users wants a single playlist to be exported
        if export_playlist_name != None:
            if export_playlist_name == playlist_name: 
                playlist_info = get_playlist_info(playlist)
                playlist_db.append(playlist_info)
            else:
                num_playlists_skipped += 1
                if verbose: print '.. skipped',
            continue
        # Option 2: user has provided an include-from file
        if len(include_playlists) > 0:
            if not playlist_in_the_list(playlist_name, include_playlists):
                num_playlists_skipped += 1
                if verbose: print '.. skipped',
                continue
        # Option 3: user wants to incude every playlist found (that is not excluded)
        playlist_info = get_playlist_info(playlist)
        playlist_db.append(playlist_info)
        print '.. added',
    if verbose: print ''
        
    print '... found', num_playlists_found, 'playlists, skipped', num_playlists_skipped

    if len(playlist_db) <= 0:
        print 'Nothing to process.'
        return
    else:
        print 'Processing', len(playlist_db), 'playlists'
        
    if playlist_list_export != None:
        return save_playlist_list_to_file(playlist_list_export, playlist_db)

    print 'Creating playlists'
    if verbose: print 'root folder:', root_folder
    for playlist in playlist_db:
        make_playlist(playlist, track_db, root_folder, share_music_files, verbose, dry_run, fname_len, nicer_names)

        
def playlist_in_the_list(playlist, playlist_list):
    if playlist in playlist_list:
        return True
    return False


def validate_commandline_args(args):
    if args.share_music_files:
        print 'Error parsing command line arguments'
        print '--share-music-file not supported.'
        exit(0)

    if args.playlist and args.playlist_list_export != None:
        print 'Error parsing command line arguments'
        print '--playlist and --playlist-list-export cannot be used together'
        exit(0)

    if args.include_from and args.playlist_list_export != None:
        print 'Error parsing command line arguments'
        print '--include-from and --playlist-list-export cannot be used together'
        exit(0)
        

def process_exclude_from_file(exclude_file, verbose):
    print 'Processing exclude-from file', exclude_file, '...',
    if verbose: print ' '
    lines = []
    try:
        with open(exclude_file,'r') as f:
            for l in f:
                s = l.decode('utf8').strip()
                if verbose: print '\tExcluding: ', s
                lines.append(s)
        print 'excluding', len(lines), 'playlists'
        return lines
    except:
        print '\tWarning: cannot open', exclude_file, 'ignoring.'
        print 'done'
        return lines

    
def process_include_from_file(include_file, verbose):
    print 'Processing include-from file', include_file, '...',
    if verbose: print ' '
    lines = []
    try:
        with open(include_file,'r') as f:
            for l in f:
                s = l.decode('utf8').strip()
                if verbose: print '\tIncluding: ', s
                lines.append(s)
        print 'including', len(lines), 'playlists'
        return lines
    except:
        print 'Warning: cannot open', include_file, 'ignoring.'
        print 'done'
        return lines

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Processes an iTunes.xml file and creates stand-alone playlist specific folders, which can be copied over to an SD card and played in car audio systems.')
    parser.add_argument('xmlfile', help='iTunes.xml file to be processed.')
    parser.add_argument('--root-folder', default='.', help='Root folder where playlists folders will be generated.')
    parser.add_argument('--dry-run', action='store_true', default=False, help='If specified, no changes are made to the destination.')
    parser.add_argument('--verbose', action='store_true', default=False, help='If specified, programs spits out lots of messages.')
    parser.add_argument('--exclude-from', type=str, action='store', default=None, help='Specify a file that contains playlist names (one per line) to be excluded during copying.')
    parser.add_argument('--include-from', type=str, action='store', default=None, help='Specify a file that contains playlist names (one per line) to be included during copying.')
    parser.add_argument('--share-music-files', action='store_true', default=False, help='If specified, music files that are shared between playlists will be copied only once. Currently NOT SUPPORTED.')
    parser.add_argument('--playlist', type=str, action='store', default=None, help='Specify a particular playlist that you want to export.')
    parser.add_argument('--fname-len', type=int, action='store', default=256, help='Specify the length of music filenames to be created during copying.  The minimum value should be 32.')
    parser.add_argument('--playlist-list-export', type=str, action='store', default=None, help='If specified, export playlist names.')
    parser.add_argument('--legacy-names', action='store_true', default=False, help='If specified, uses old style names that begin with year.  See make_a_nice_name(). Default is fault.')
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
        exclude_playlists = process_exclude_from_file(args.exclude_from, args.verbose)
    exclude_playlists.extend(itunes_default_playlists)

    include_playlists = []
    if args.include_from:
        include_playlists = process_include_from_file(args.include_from, args.verbose)
    
    validate_commandline_args(args)
    
    process_xml(args.xmlfile,
                args.root_folder,
                exclude_playlists,
                args.share_music_files,
                args.verbose,
                args.dry_run,
                args.playlist,
                args.fname_len,
                args.playlist_list_export,
                include_playlists,
                not args.legacy_names)
