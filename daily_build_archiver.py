# This tool is designed to create archive of daily alpha builds
# Run archive_loop() in loop or call it periodically
# Builds are downloaded to cache_path/YYYY-MM-DD__H__<hash>
# Downloaded builds are asynchronously extracted to 
# storage_path/YYYY-MM-DD__H__<hash>
# This date format is used mainly for ordering and to ensure unique name.
# build_stamp_filename is used to check if all files are written correctly.

import os
import sys
import re
import time
import shutil
import zipfile
import datetime
import urllib.request
from urllib.parse import urlparse
import lxml.html

url = 'https://builder.blender.org/download/'
# 'os windows', 'os linux' or 'os macos'
container_html_element_class = 'os windows'
# Smaller storage on machine running this script
cache_path = 'D:\\cache\\'
max_builds_in_cache = 250
# Directly connected to testing machine. Doesn't have to be online all the time
storage_path = '\\\\DESKTOP-JVQ3T9B\\builds\\'
build_stamp_filename = 'archive_build_info.txt'
log_file_path = 'log.txt'

def log(message):
    date = datetime.datetime.now()
    date_str = date.strftime('[%Y-%m-%d %H:%M:%S]')
    print (date_str, message)
    f = open(log_file_path, "a")
    f.write(date_str + message + '\n')
    f.close()

def extract_hash_from_filename(filename):
    return re.findall("[0-9a-f]{12}", str(filename))[0]

def get_cached_build_filename(date):
    return os.listdir(os.path.join(cache_path, date))[1]

def get_cached_builds():
    return sorted(os.listdir(cache_path))

def get_stored_builds():
    return sorted(os.listdir(storage_path))

def get_last_cached_hash():
    dirs =  get_cached_builds()
    if len(dirs) < 1:
        return None
    last_dir = dirs[len(dirs) - 1]
    return extract_hash_from_filename(last_dir)

def stamp_path(target_dir):
    log('Stamping build info')
    buildinfo_path = os.path.join(target_dir, build_stamp_filename)
    open(buildinfo_path, 'w').write(extract_hash_from_filename(target_dir))

# Remove entry if build_stamp_filename doesn't exist
def validate_storage():
    for build in get_stored_builds()[-10:]:
        target_dir = os.path.join(storage_path, build)
        buildinfo_path = os.path.join(target_dir, build_stamp_filename)
        if not os.path.isfile(buildinfo_path):
            log("Build %s is invalid - removing" % build)
            shutil.rmtree(target_dir)

# Remove entry if build_stamp_filename doesn't exist
def validate_cache():
    for build in get_cached_builds()[-10:]:
        target_dir = os.path.join(cache_path, build)
        buildinfo_path = os.path.join(target_dir, build_stamp_filename)
        if not os.path.isfile(buildinfo_path):
            log("Cache entry %s is invalid - removing" % build)
            shutil.rmtree(target_dir)
    
def get_download_link():
    with urllib.request.urlopen(url) as response:
       raw_html = response.read()
    html_tree = lxml.html.fromstring(raw_html)   
    container = html_tree.find_class(class_name=container_html_element_class)
    #last element with class, first link
    build_rel_url = list(container[len(container) - 1].iterlinks())[0][2]
    parsed_uri = urlparse(url)
    base_url = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    return base_url + build_rel_url

def download_to_cache():
    log('Parsing')
    build_url = get_download_link()
    filename = os.path.basename(urlparse(build_url).path)
    build_hash = extract_hash_from_filename(filename)
    date = datetime.datetime.now()
    cached_build_subdir = date.strftime('%Y-%m-%d__%H__') + build_hash
    target_dir = os.path.join(cache_path, cached_build_subdir)
    # Do not make another dir with same build - can happen due to timezones
    if get_last_cached_hash() != build_hash:
        log('Downloading %s' % build_url)
        with urllib.request.urlopen(build_url) as response:
            build_archive = response.read()
        log('Writing file')
        os.mkdir(target_dir)
        archive_file_path = os.path.join(target_dir, filename)
        archive_file = open(archive_file_path, 'wb')
        archive_file.write(build_archive)
        archive_file.close()
        stamp_path(target_dir)
    else:
        log('Cache is up to date')
        log('  Local hash:\t%s' % get_last_cached_hash())
        log('  Remote hash:\t%s '% build_hash)

def cleanup_cache():
    cached_builds = get_cached_builds()
    number_of_builds_to_clean = len(cached_builds) - max_builds_in_cache
    
    if cached_builds is None:
        return
    if max_builds_in_cache < 1:
        return
    if number_of_builds_to_clean <= 0:
        return
    
    log("Cache cleanup")
    builds_to_cleanup = cached_builds[:number_of_builds_to_clean]
    for build in builds_to_cleanup:
        archive_filename = get_cached_build_filename(build)
        archive_file_path = os.path.join(cache_path, build, archive_filename)
        log("Removing %s" % archive_file_path)
        os.remove(archive_file_path)
        os.rmdir(os.path.join(cache_path, build))

def synchronize_storage():
    cached_builds = get_cached_builds()
    stored_builds = get_stored_builds()
    
    if cached_builds is None:
        log("No builds to synchronize")
        return
    
    if stored_builds is not None:
        builds_to_sync = [i for i in cached_builds if i not in stored_builds]
    else :
        builds_to_sync = cached_builds

    if len(builds_to_sync) < 1:
        log("Storage up to date")

    for build in builds_to_sync:
        if container_html_element_class == 'os windows':
            archive_filename = get_cached_build_filename(build)
            archive_file_path = os.path.join(cache_path, build, archive_filename)
            
            log('Extracting %s' % archive_file_path)
            with zipfile.ZipFile(archive_file_path, 'r') as zip_ref:
                zip_ref.extractall(storage_path)

            archive_filename_no_ext = os.path.splitext(archive_filename)[0]
            extracted_dir = os.path.join(storage_path, archive_filename_no_ext)
            target_dir = os.path.join(storage_path, build)
            os.rename(extracted_dir, target_dir)
        else:
            pass #TODO Is even extracting different in other platforms?
            
        stamp_path(target_dir)

def archive_loop():
    validate_cache()
    download_to_cache()
    try:
        validate_storage()
        synchronize_storage()
    except FileNotFoundError:
        log("Could not access storage")
    except OSError:
        log("Could not access storage")
    cleanup_cache()
    log("Done")

log_file = open(log_file_path, "a")
sys.stderr = log_file

while True:
    archive_loop()
    time.sleep(3600)