import pickle
import os
import sys
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from tabulate import tabulate
import io
import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
from tabulate import tabulate
from fpdf import FPDF
import cv2
import numpy as np
import itertools



openfile2=open("gDriveOverview.html","w")
SCOPES = ['https://www.googleapis.com/auth/drive.metadata',
          'https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/drive']
def get_gdrive_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    # return Google Drive API service
    return build('drive', 'v3', credentials=creds)

def downloadFile(id, name):
    service = get_gdrive_service()
    request = service.files().get_media(fileId=id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("AFTER : In Download function : {0} and status {1} and status progress {2}".format(done, status, int(status.progress())))
        print("AFTER : In Download function DONE : {0}".format(done))
        #print("BEFORE : In Download function var : {0}".format(var))
        print("Download %d%%." % int(status.progress() * 100))
        with io.open("." + "/" + name, 'wb') as f:
            fh.seek(0)
            f.write(fh.read())


'''
def isDuplicate(img1,img2):
    image1 = cv2.imread(img1)
    image2 = cv2.imread(img2)
    try:
        difference = cv2.subtract(image1, image2)
        result = not np.any(difference) #if difference is all zeros it will return False
        if result is True:
            #print(list[i],list[j])
             #duplicate_image.append(list[i])
             print("{} images is matching with {} Occurred {} times ".format(img1,img1,list.count(img1)))
    except:
         i=0

'''


def check_duplicate_image(items):
    #"""given items returned by Google Drive API, prints them in a tabular way"""
    map= {}
    list=[]
    message= set()
    duplicate_image=[]
    if not items:
        print('No files found.')
    else:
        for item in items:
            if item["mimeType"] == "image/jpeg":
                list.append(item["name"])
                #Creating Map
                value=[]
                value.append(item["name"])
                value.append(item["webViewLink"])
                map[item["id"]]=value
                #Dowloading Image
                downloadFile(item["id"],item["name"])
        for i in range(len(list)-1):
        #for x, y in dict.items():
            count=0
            for j in range(i+1,len(list)):
                    image1 = cv2.imread(list[i])
                    image2 = cv2.imread(list[j])
                    try:
                        difference = cv2.subtract(image1, image2)
                        result = not np.any(difference) #if difference is all zeros it will return False
                        if result is True:
                            duplicate_image.append(list[i])
                            print("{} images is matching with {} Occurred {} times ".format(list[i],list[j],list.count(list[i])))
                            message.add("{} images is matching with {}".format(list[i],list[j]))
                    except:
                        i=0
        m={}
        for x, y in map.items():
            if y[0] in duplicate_image:
                if y[0] in m.keys():
                    m[y[0]].append(y[1])
                else:
                    v=[]
                    v.append(y[1])
                    m[y[0]]=v

        return m,message



def main():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 5 files the user has access to.
    """
    service = get_gdrive_service()
    # Call the Drive v3 API
    #results = service.files().list(pageSize=20, fields="nextPageToken, files(id, name,mimeType)").execute()
    results = service.files().list(pageSize=20, fields="nextPageToken,files(id, name,mimeType,parents,webViewLink)").execute()
    #results1 = service.files().list( pageSize = 20, fields="nextPageToken, files(parents)").execute()
    #items1=results1.get('')
    # get the results
    items = results.get('files', [])
    list_files(items)
    
    

def count_files(id):
    folder_count=0
    restoffile=0
    service = get_gdrive_service()
    # Call the Drive v3 API
    #results = service.files().list(pageSize=5, fields="nextPageToken, files(id, name,mimeType)").execute()
    #results = service.files().list(q="mimeType='application/octe	t-stream' and parents in '"+id+"' and trashed = false",fields="nextPageToken, files(id, name)").execute()
    results = service.files().list(pageSize=30,q="'{}' in parents".format(id)).execute()
    #children = service.files().list(q=query,fields='nextPageToken, files(id, name)').execute()
    items = results.get('files', [])
    count=0
    for item in items:
        if item["mimeType"] =="application/vnd.google-apps.folder":
            folder_count=folder_count+1
            openfile2.write("<pre><code> \t\t Folder Name: %s</pre></code>"%item["name"])
        else:
            openfile2.write("<pre><code> \t \t File Name: %s</pre></code>"%item["name"])
            restoffile=restoffile+1
        count=count+1
    #print "\t","The no of folder:-", folder_count
    #print "\t","The no of items:-", restoffile
    f1="Total no of Folders:"+ str(folder_count)
    f2="Total no of Files:"+ str(restoffile)
    openfile2.write("<pre><p><b>\t\t %s</b></p></pre>"% f1)
    openfile2.write("<p>  %s</p>"%" ")
    openfile2.write("<pre><code><b>\t\t %s</b></pre></code>"%f2)
    #openfile2.write("\n")
    return count,folder_count,restoffile

def drive_landing_page_count(items):
    count=0
    for item in items:
        if item["mimeType"] == "application/vnd.google-apps.folder":
           if item["name"]=="testtechm":
            #count=count+1
            count=count_files(item['parents'][0])
            break
    return count  
       
def list_files(items):
    """given items returned by Google Drive API, prints them in a tabular way""" 
    openfile=open("drive.txt","w")
    message = """<html>
    <head><b style ="color:black;text-align: center;font-size:25px;margin-left:-6px;margin-bottom:25px;background-color:#cfe0e8;width:1800px;height:25px;padding:10px;border:2px solid mediumturquoise;float:left;">Google Drive Data Report</b></head>
    <body>
          <p style='color:darkcyan;LINE-HEIGHT:20px;margin-left:60px;margin-top:-6px;font-size:22px'>Summary of Google Drive Data </p></body>
    </html>"""
    openfile2.write(message)
    namehai=[]
    folder_namehai=[]
    file_namehai=[]
    temp_id=[]
    parentid=[]
    count=0
    count_rep=0
    repeat="True"
    ct=drive_landing_page_count(items)
    #output="The no of files in the landing page is:"+str(ct)
    #openfile2.write("<p style='color:yellowgreen'> %s</p>"%output)
    if not items:
        # empty drive
        print('No files found.')
    else:
        rows = []
        for item in items:
            folder_count=0
            restoffile=0
            # get the File ID
            id = item["id"]
            # get the name of file
            name = item["name"]
            #print(name)
            if name in namehai:
                count_rep+=1
            else:
                count_rep=0
            #namehai.append(name)
            mime_type = item["mimeType"]
            if mime_type == "application/vnd.google-apps.folder":
                print(item["name"])
                openfile2.write("<p style='color:darkcyan;margin-left:60px'> \t\t Folder: %s</p>"%item["name"])
                count,folder_count,restoffile=count_files(id)
                folder_namehai.append(item["name"])
            else:
                concat_data='File name:-'+ item["name"]+5*'  '+"File Type:-"+item["mimeType"]
                openfile2.write("<p style='color:Black;margin-left:60px'> \t File: %s</p>"%item["name"])
                file_namehai.append(item["name"])
                count=0
            
            """
            openfile.write(id)
            openfile.write(name)
            openfile.write(mime_type)
            """
            size=len(namehai)
            repeated=[]
            rows.append((id, name,mime_type,count,count_rep,folder_count,restoffile))

        openfile2.write("<p style='color:darkcyan;margin-left:60px'> \t<b> Duplicate Image Summary :</b></p>")
        str,mess = check_duplicate_image(items)
        for x, y in str.items():#<a href=%s>
            openfile2.write("<p style='color:Black;margin-left:60px'> \t Duplicate File name is :- %s, and this file occure,%s times,image url is <a href=%s>%s</a></p>"%(x,len(y),y,y))

        for m in set(mess):
            openfile2.write("<p style='color:Black;margin-left:60px'> \t Description about matching image :- %s</p>"%m)
        # convert to a human readable table
        table = tabulate(rows,headers=["ID","Name","Type","files_inside","Repition","No_of_folders","Rest_of_file"])
        # print the table
        """
        openfile.write(rows)
        """
        openfile.write(table)
        openfile.close()
        openfile2.close()


if __name__ == '__main__':
    main()
