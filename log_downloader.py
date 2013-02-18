import datetime
import urllib2
import tarfile
import os
import os.path

# File download code provided by:
# http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
def download_file(url, filename):
    if filename == None:
        filename = url.split('/')[-1]
    u = urllib2.urlopen(url)
    f = open(filename, 'wb')
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

if __name__ == '__main__':
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
    time_delta = datetime.timedelta(days=1)
    while start_date < end_date:
        url = start_date.strftime('http://dominion.isotropic.org/gamelog/%Y%m/%d/all.tar.bz2')
        filename = start_date.strftime('{0}/%Y-%m-%d.tar.bz2'.format(download_dir))
        finished_name = start_date.strftime('{0}/%Y-%m-%d.tar.bz2'.format(extracted_dir))
        # Skip downloading files that have already been downloaded
        if not os.path.exists(filename) and not os.path.exists(finished_name):
            download_file(url, filename)
        # Skip extracting files that have been moved to the extracted folder
        if not os.path.exists(finished_name):
            file = tarfile.open(filename, 'r')
            print 'Extracting ' + filename
            file.extractall(extraction_dir)
            file.close()
            os.rename(filename, finished_name)
        start_date = start_date + time_delta