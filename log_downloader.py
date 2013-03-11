import datetime
import time
import urllib2
import re
import sys
import tarfile
import os
import os.path

# File download code provided by:
# http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
def download_file(url, filename_download, filename):
    start = time.time()
    if filename == None:
        filename = os.path.basename(url)
    u = urllib2.urlopen(url)
    f = open(filename_download, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (filename, file_size)

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,

    f.close()
    os.rename(filename_download, filename)
    print 'Downloaded in {0} minutes'.format((time.time() - start) / 60.0)
    
def extract_file(extraction_dir, filename, finished_name):
    start = time.time()
    name = os.path.basename(filename)
    match = re.match(r'(?P<year>\d+)\-(?P<month>\d+)\-(?P<day>\d+)\.tar\.bz2', name)
    if match:
        year = int(match.group('year'))
        month = int(match.group('month'))
        day = int(match.group('day'))
    else:
        print 'Couldn\'t match regex! ' + name
        print 
        exit(1)
    file = tarfile.open(filename, 'r')
    print 'Extracting ' + filename
    dir = extraction_dir.format(year, month, day)
    if not os.path.exists(dir):
        os.makedirs(dir)
    file.extractall(dir)
    file.close()
    os.rename(filename, finished_name)
    print 'Extracted in {0} minutes'.format((time.time() - start) / 60.0)

if __name__ == '__main__':
    download = '-d' in sys.argv or '-de' in sys.argv or '-ed' in sys.argv
    extract = '-e' in sys.argv or '-de' in sys.argv or '-ed' in sys.argv
    if not download and not extract:
        print 'Specify either download (-d) or extract (-e) or both (-de)'
        exit(0)
    
    download_dir = 'gamelogs'
    extracted_dir = 'gamelogs/extracted'
    extraction_root_dir = 'games'
    extraction_dir = extraction_root_dir + '/{0:04}/{1:02}/{2:02}'
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    if not os.path.exists(extracted_dir):
        os.makedirs(extracted_dir)
    if not os.path.exists(extraction_root_dir):
        os.makedirs(extraction_root_dir)
    
    # Move all the files that were previously extracted to their new folders
    for file in os.listdir(extraction_root_dir):
        if os.path.isfile(os.path.join(extraction_root_dir, file)):
            match = re.match(r'game-(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})-\d{6}-[\d\w]{8}\.html', file)
            if match:
                year = int(match.group('year'))
                month = int(match.group('month'))
                day = int(match.group('day'))
                dir = extraction_dir.format(year, month, day)
                if not os.path.exists(dir):
                    os.makedirs(dir)
                old_path = os.path.join(extraction_root_dir, file)
                new_path = os.path.join(dir, file)
                os.rename(old_path, new_path)
    
    start_date = datetime.date(2013, 1, 1)
    end_date = datetime.date.today()
    time_delta = datetime.timedelta(days=-1)
    cur_date = end_date + time_delta
    while start_date <= cur_date:
        url = cur_date.strftime('http://dominion.isotropic.org/gamelog/%Y%m/%d/all.tar.bz2')
        filename = cur_date.strftime('{0}\%Y-%m-%d.tar.bz2'.format(download_dir))
        filename_download = filename + '.tmp'
        finished_name = cur_date.strftime('{0}\%Y-%m-%d.tar.bz2'.format(extracted_dir))
        # Skip downloading files that have already been downloaded
        if not os.path.exists(filename) and not os.path.exists(finished_name):
            if download:
                download_file(url, filename_download, filename)
        # Skip extracting files that have been moved to the extracted folder
        if os.path.exists(filename) and not os.path.exists(finished_name):
            if extract:
                extract_file(extraction_dir, filename, finished_name)
        cur_date = cur_date + time_delta