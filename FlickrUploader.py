#---------------------------------------------------------------------------------------------------------
#    
#     Uploads local photos to flickr and adds to flickr albums based on folder
#     Does not delete images in flickr not in local
#    
#     Requirements
#     -------------
#     Flickr API 
#      - https://github.com/sybrenstuvel/flickrapi
#      - https://stuvel.eu/flickrapi
#      - https://www.archlinux.org/packages/community/any/python-flickrapi/
#
#     Authentication
#     ---------------
#     Note that first run will require authentication.   See here for further instructions
#     (see section: Authenticating without local web server)
#     https://stuvel.eu/flickrapi-doc/3-auth.html
#
#---------------------------------------------------------------------------------------------------------
        

import flickrapi
from xml.etree import ElementTree as ET
import os
import collections


local_album_path = 'xxxxxxxxxxxxxxxxxxxxxx'
api_key = u'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
api_secret = u'xxxxxxxxxxxxxxxxxxxxxxxxxxx'
userid = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'



def flickr_albums():
    """Returns a dictionary of albums (sets) in Flickr where dictionary key = album title
    and value equals flickr set id"""
    
    albums = {}
    sets  = flickr.photosets.getList(user_id = userid)

    for photo_set in sets.iter('photoset'):
        for set_title in photo_set.iter('title'):
            albums[set_title.text] =   photo_set.attrib['id']

    return (albums)


def flickr_photos_in_album(flickr_albums, album_name):
    """Returns a dictionary of flickr photos in album where key = photo title
    and value is the flickr photo id"""
    
    
    set_id = flickr_albums[album_name]
    xml_photos_in_set = flickr.photosets.getPhotos(user_id = userid, photoset_id = set_id)

    photo_dict = {}
    for i in xml_photos_in_set.iter('photo'):
        photo_dict[i.attrib['title']] = i.attrib['id']
    return(photo_dict)


def local_albums():
    """Returns albums stored locally / network as a list of album names
    which equal folder names"""
    
    
    folder_list = []
    for (root, folders, files) in os.walk(local_album_path):
        for folder in folders:
            
            #Only recognise folders as album if photos in folder to prevent errors
            #further in code
            if len(os.listdir(os.path.join(local_album_path, folder))) > 0:
                folder_list.append(folder)

    return(folder_list)


def local_photos_in_album(album):
    """Returns albums stored locally or on network as a dictionary where key is filename
    excluding extension and values is the full file path including filename and extension"""
    
    photo_dict = {}
    album_path = os.path.join(local_album_path, album)
    for (root, folder, files) in os.walk(album_path):
        for file in files:
            file_excl_extension = os.path.splitext(file)[0]
            photo_dict[file_excl_extension] = os.path.join(album_path, file)
            
    return  (photo_dict)



def flickr_upload_family_friends_photo (photo_file_path):        
    """Upload photo tp flickr with visibility to family and friends only
    Returns photo id"""
    
    photo_title = os.path.basename(photo_file_path).split(".")[0]
    xml_response = flickr.upload(filename = photo_file_path, title = photo_title, is_public = 0, is_family = 1, is_friend =1 )
    for i in xml_response.iter('photoid'):
        flickr_photo_id = i.text
    return (flickr_photo_id)
        
    
def flickr_create_album (album_name, primary_photo_id):
    """Create album in flickr inlcuding primary photo
    Return set id"""

    xml_response = flickr.photosets.create(title = album, description = album, primary_photo_id = flickr_photo_id)
    for i in xml_response.iter('photoset'):
        photoset_id = (i.attrib['id'])
    return (photoset_id)
    

    
def write_temp_xml_file(xml_element):
    """ For debig purposes to view Flickr API responses"""
    xml_tree = ET.ElementTree(xml_element)
    xml_tree.write('\\\\ARCH_SERVER\\Documents_Charl\\Temp\\temp_xml_output.xml')


    
def sort_flickr_albums(flkr_albums):
    """Sorts flickr albums alphabetically in reverse order so that latest YYYY_Qtr 
    are displayed first.
    flickr_albums parameter is a dictionary of flickr photos in album where
    key = photo title and value is the flickr photo id"""

    od = collections.OrderedDict(sorted(flkr_albums.items(), reverse = True))
    sorted_album_id_list = list(od.values())
    id_string = ''
    for album_id in sorted_album_id_list:
        if id_string == '':
                id_string = album_id
        else:
            id_string = id_string + ',' + album_id
    
    flickr.photosets.orderSets (photoset_ids = id_string)
    
    
    
if __name__ == '__main__':
        
    flickr = flickrapi.FlickrAPI(api_key, api_secret)
    
    # ------------------------------------------------------
    #    Authenticate
    #    Only do this if we don't have a valid token already
    # ------------------------------------------------------
    
    if not flickr.token_valid(perms='write'):

        # Get a request token
        flickr.get_request_token(oauth_callback='oob')

        # Open a browser at the authentication URL. Do this however
        # you want, as long as the user visits that URL.
        authorize_url = flickr.auth_url(perms='write')
        print(authorize_url)

        # Get the verifier code from the user. Do this however you
        # want, as long as the user gives the application the code.
        verifier = str(input('Verifier code: '))

        # Trade the request token for an access token
        flickr.get_access_token(verifier)
 
    
    
    flkr_albums = flickr_albums()
    lcl_albums = local_albums()

    for album in lcl_albums:
        
        local_album_photos = local_photos_in_album(album)
        
        if album not in flkr_albums:
            #upload single photo, create album with this photo, and update
            #dictionary containing flickr albums
            single_photo_path = list(local_album_photos.values())[0]
            print ('uploading ' + single_photo_path)
            flickr_photo_id = flickr_upload_family_friends_photo(single_photo_path)
            print ('Creating album ' + album)
            photoset_id = flickr_create_album (album, flickr_photo_id)
            #Add the new album to flickr album dictionary
            flkr_albums.update({album : photoset_id})
            #Remove uploaded photo from local album dictionary to prevent double uploading below
            del local_album_photos[list(local_album_photos.keys())[0]]

        flickr_album_photos = flickr_photos_in_album(flkr_albums, album)
        flickr_album_id = flkr_albums[album]
        
        for photo in local_album_photos:
            if not photo in flickr_album_photos:
                photo_path = local_album_photos[photo]
                print('uploading ' + photo_path)
                flickr_photo_id = flickr_upload_family_friends_photo(photo_path)
                flickr.photosets.addPhoto (photoset_id = flickr_album_id, photo_id = flickr_photo_id)

    sort_flickr_albums(flkr_albums)
