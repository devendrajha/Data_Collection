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
import matplotlib.pyplot as plotter

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


def check_duplicate_image(items):
    #"""given items returned by Google Drive API, prints them in a tabular way"""
    map= {}
    list=[]
    message= set()
    duplicate_image=[]
    duplicate_count=0
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
                            duplicate_count=duplicate_count+1
                    except:
                        i=0
    return duplicate_count    
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

def draw_piechart(folder_count,image_count,dublicate_count):
    pieLabels='Total_Folder','Total_Image','Duplicate'
    f_c=int((folder_count/(folder_count+image_count+dublicate_count))*100)
    i_c=int((image_count/(folder_count+image_count+dublicate_count))*100)
    d_c=int((dublicate_count/(folder_count+image_count+dublicate_count))*100)
    populationShare= [folder_count,image_count,dublicate_count]
    figureObject, axesObject = plotter.subplots()
    axesObject.pie(populationShare,labels=pieLabels,autopct='%1.2f',startangle=90)
    axesObject.axis('equal')
    #plotter.show()
    plotter.savefig("piechart.png")
    openfile2.write("<img src ='piechart.png'>")
def list_files(items):
    """given items returned by Google Drive API, prints them in a tabular way""" 
    message = """<html>
    <head><b style ="color:black;text-align: center;font-size:25px;margin-left:-6px;margin-bottom:25px;background-color:#cfe0e8;width:1800px;height:25px;padding:10px;border:2px solid mediumturquoise;float:left;">Google Drive Data Report</b></head>
    <body>
          <p style='color:darkcyan;LINE-HEIGHT:20px;margin-left:60px;margin-top:-6px;font-size:22px'>Summary of Google Drive Data </p></body>
    </html>"""
    openfile2.write(message)
    folder_count=0
    image_count=0
    dublicate_count=0
    #output="The no of files in the landing page is:"+str(ct)
    #openfile2.write("<p style='color:yellowgreen'> %s</p>"%output)
    if not items:
        # empty drive
        print('No files found.')
    else:
        rows = []
        for item in items:
            # get the File ID
            id = item["id"]
            # get the name of file
            name = item["name"]
            #print(name)
            mime_type = item["mimeType"]
            if mime_type == "application/vnd.google-apps.folder":
                folder_count=folder_count+1
            if mime_type == "image/jpeg":
                image_count=image_count+1
            repeated=[]
            rows.append((id, name,mime_type,folder_count))
        openfile2.write("<table BORDER><tr><th>Types Of Data \t</th><th>\t Number of Data</th></tr>")
        f1="Total no of Folders"
        f2="Total no of Image"
        f3="Total no of Duplicate Image"
        openfile2.write("<tr><td>"+str(f1)+"</td><td>"+str(folder_count)+"</td></tr>")
        openfile2.write("<p>  %s</p>"%" ")
        #openfile2.write("<pre><code><b>\t\t %s</b></pre></code>"%f2)
        openfile2.write("<tr><td>"+str(f2)+"</td><td>"+str(image_count)+"</td></tr>")
        openfile2.write("<p>  %s</p>"%" ")
        openfile2.write("<tr><td>"+str(f3)+"</td><td>"+str(dublicate_count)+"</td></tr>")
        openfile2.write("</table>")
        dublicate_count=check_duplicate_image(items)
        draw_piechart(folder_count,image_count,dublicate_count)
        #openfile2.write("<p style='color:darkcyan;margin-left:60px'> \t<b> Duplicate Image Summary :</b></p>")
        openfile2.write("<p style ='color:black;text-align: center;font-size:15px;margin-left:-6px;margin-bottom:25px;background-color:#cfe0e8;width:200px;height:20px;padding:10px;border:2px solid mediumturquoise;float:left;'>Folder: %s\n</p>"%folder_count)
        openfile2.write("<p style ='color:black;text-align: center;font-size:15px;margin-left:-6px;margin-bottom:25px;background-color:#cfe0e8;width:200px;height:20px;padding:10px;border:2px solid mediumturquoise;float:left;'>Image: %s\n</p>"%image_count)
        openfile2.write("<p style ='color:black;text-align: center;font-size:15px;margin-left:-6px;margin-bottom:25px;background-color:#cfe0e8;width:200px;height:20px;padding:10px;border:2px solid mediumturquoise;float:left;'>Duplicate: %s\n</p>"%dublicate_count)
        #convert to a human readable table
        table = tabulate(rows,headers=["ID","Name","Type","No_of_folders"])
        # print the table
        openfile2.close()

if __name__ == '__main__':
    main()
