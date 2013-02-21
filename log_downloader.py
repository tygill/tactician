import datetime
import time
import urllib2
import tarfile
import sys
import os
import os.path

# File download code provided by:
# http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
def download_file(url, filename_download, filename):
    start = time.time()
    if filename == None:
        filename = url.split('/')[-1]
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
    
def extract_file(filename, finished_name):
    start = time.time()
    file = tarfile.open(filename, 'r')
    print 'Extracting ' + filename
    file.extractall(extraction_dir)
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
    extraction_dir = 'games'
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    if not os.path.exists(extracted_dir):
        os.makedirs(extracted_dir)
    if not os.path.exists(extraction_dir):
        os.makedirs(extraction_dir)
    
    start_date = datetime.date(2013, 2, 1)
    end_date = datetime.date.today()
    time_delta = datetime.timedelta(days=-1)
    cur_date = end_date + time_delta
    while start_date < cur_date:
        url = cur_date.strftime('http://dominion.isotropic.org/gamelog/%Y%m/%d/all.tar.bz2')
        filename = cur_date.strftime('{0}/%Y-%m-%d.tar.bz2'.format(download_dir))
        filename_download = filename + '.tmp'
        finished_name = cur_date.strftime('{0}/%Y-%m-%d.tar.bz2'.format(extracted_dir))
        # Skip downloading files that have already been downloaded
        if not os.path.exists(filename) and not os.path.exists(finished_name):
            if download:
                download_file(url, filename_download, filename)
        # Skip extracting files that have been moved to the extracted folder
        if not os.path.exists(finished_name):
            if extract:
                extract_file(filename, finished_name)
        cur_date = cur_date + time_delta