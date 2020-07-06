import csv
import io
import pickle
import os
import webbrowser
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
import cv2
import numpy as np
import matplotlib.pyplot as plotter

openfile2=open("gDriveOverview3.html","w")
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

def duplicate_image_list(imagelist):
    dup_list=[]
    if len(imagelist) >= 1:
        for i in range(len(imagelist)-1):
            for j in range(i + 1, len(imagelist)):
                image1 = cv2.imread(imagelist[i])
                image2 = cv2.imread(imagelist[j])
                try:
                    difference = cv2.subtract(image1, image2)
                    result = not np.any(difference)  # if difference is all zeros it will return False
                    if result is True:
                        dup_list.append(imagelist[i])
                except:
                    i = 0
    return dup_list

csv_map= {}

def check_duplicate_image(items):
    #"""given items returned by Google Drive API, prints them in a tabular way"""
    map= {}
    image_name_list=[]
    duplicate_image=[]
    for item in items:
        file_type=item["mimeType"]
        if file_type == "image/jpeg":
            image_name_list.append(item["name"])
            #Creating Map
            value=[]
            value.append(item["name"])
            value.append(item["webViewLink"])
            map[item["id"]]=value
            csv_map[item["name"]]=item["webViewLink"]
            #Dowloading Image
            downloadFile(item["id"],item["name"])
            duplicate_image=duplicate_image_list(image_name_list)

    return duplicate_image

def renameFile(id, newName):
    service = get_gdrive_service()
    file = service.files().get(fileId=id).execute()
    del file['id']
    file['name'] = newName+".jpg";
    updated_file = service.files().update(fileId=id,body=file).execute()


def count_image(id):
    imageList=[]
    service = get_gdrive_service()
    results = service.files().list(pageSize=30,q="'{}' in parents".format(id)).execute()
    items = results.get('files', [])
    for item in items:
        mime_Type=item["mimeType"]        
        if mime_Type == "image/jpeg":
            imageList.append(item["name"])
        if mime_Type == "application/vnd.google-apps.folder":
            imageList.extend(count_image(item["id"]))

    return imageList

def count_files(id):
    folder_count=0
    restoffile=0
    service = get_gdrive_service()
    # Call the Drive v3 API
    results = service.files().list(pageSize=60,q="'{}' in parents".format(id)).execute()
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
    f1="Total no of Folders:"+ str(folder_count)
    f2="Total no of Files:"+ str(restoffile)
    openfile2.write("<pre><p><b>\t\t %s</b></p></pre>"% f1)
    openfile2.write("<p>  %s</p>"%" ")
    openfile2.write("<pre><code><b>\t\t %s</b></pre></code>"%f2)
    #openfile2.write("\n")
    return count,folder_count,restoffile

def draw_barchart(map):
    n_groups = 4
    values = list(map.values())
    newlist=[]
    total_image_count=[]
    duplicate_image_count_in_folder=[]
    for v in values:
        newlist.append(duplicate_image_list(v))
        total_image_count.append(len(v))
    for n in newlist:
        duplicate_image_count_in_folder.append(len(n))

    # create plot
    print(total_image_count,duplicate_image_count_in_folder,map.keys())
    fig, ax = plotter.subplots()
    index = np.arange(n_groups)
    bar_width = 0.35
    opacity = 0.8
    rects1 = plotter.bar(index, total_image_count, bar_width,alpha=opacity,color='b',label='Image')
    rects2 = plotter.bar(index + bar_width, duplicate_image_count_in_folder, bar_width,alpha=opacity,color='r',label='Duplicate_Image')
    plotter.xlabel('Folders')
    plotter.ylabel('Images')
    plotter.title('Folder Name')
    plotter.xticks(index + bar_width, list(map.keys()))#('A', 'B', 'C', 'D'))
    plotter.legend()
    plotter.tight_layout()
    #plotter.show()
    plotter.savefig("barchart.png")


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
    openfile2.write("<div><img style=margin-left:800px;margin-top:-850px;width:500;height:350; src ='piechart.png'></div>")


def list_files(items,service):
    """given items returned by Google Drive API, prints them in a tabular way""" 
    message = """<html>
    <head><b style ="color:black;text-align: center;font-size:25px;margin-left:-6px;margin-bottom:25px;width:1300px;float:left;">Google Drive Data Report</b></head>
    <body>
      </html>"""
    openfile2.write(message)
    folder_count=0
    image_count=0
    imglist=[]
    count=0
    testtechm_id=''
    nm_name=[]
    img_count=[]
    
    rows = []
    map={}
    for item in items:
        id = item["id"]
        name = item["name"]
        mime_type = item["mimeType"]
        if name=='Test Techm':
            testtechm_id=item['parents'][0]
        if mime_type == "application/vnd.google-apps.folder":
            folder_count=folder_count+1
            folder_name=item["name"]
        if mime_type == "image/jpeg":
            #renameFile(item["id"],"rajj_img"+str(image_count))
            image_count=image_count+1
        if mime_type=="application/vnd.google-apps.folder" and item["parents"][0]==testtechm_id:
            name1=count_image(id)
            nm_name.append(name1)
            img_count.append(len(name1))
            map[item["name"]]=name1

        rows.append((id, name,mime_type,folder_count))
        imglist.append(count)
        rows.append((id, name,mime_type,folder_count))
    html()
    dublicate_count=len(check_duplicate_image(items))
    draw_barchart(map)
    openfile2.write("<table BORDER='3' style=width:35%;margin-left:80px;margin-top:-110px><tr><th style=height:45px;background-color:darkgreen;color:white;font-size:20px>Types Of Data</th><th style=height:45px;background-color:darkgreen;color:white;font-size:20px> Number of Data</th></tr>")
    f1="Total no of Folders"
    f2="Total no of Image"
    f3="Duplicate Image Count"
    openfile2.write("<tr><td style=height:43px>"+str(f1)+"</td><td style=height:43px;text-align:center;font-size:18px>"+str(folder_count)+"</td></tr>")
    openfile2.write("<p>  %s</p>"%" ")
    openfile2.write("<tr><td style=height:43px>"+str(f2)+"</td><td style=height:43px;text-align:center;font-size:18px>"+str(image_count)+"</td></tr>")
    openfile2.write("<p>  %s</p>"%" ")
    openfile2.write("<tr><td style=height:43px>"+str(f3)+"</td><td style=height:43px;text-align:center;font-size:18px>"+str(dublicate_count)+"</td></tr>")
    openfile2.write("</table>")
    openfile2.write("<div><img style=margin-left:50px;margin-bottom:10px;margin-top:90px src ='barchart.png'></div>")
    draw_piechart(folder_count,image_count,dublicate_count)
    openfile2.close()


def createDeviceCSV():
    fileName = 'DuplicateImage.csv'
    with open(fileName, 'w',newline='') as csvFile:
        writer = csv.writer(csvFile)
        row = ["Image Name", 'Image Url']
        writer.writerow(row)
        count = 0
        for k,v in csv_map.items():
            row = [k, v]
            writer.writerow(row)
            count = count + 1
            print("Device's adding into csv: " + str(count))
        csvFile.close()
        print('Device CSV File creation is Done file name is ',fileName)

def html():
    uri=[]
    for k,v in csv_map.items():
        name_url=[]
        name_url.append(k)
        name_url.append(v)
        uri.append(name_url)

    fb = open('duplicateData.html','w')
    message1 = """<html>
          <head>
            <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
            <script type="text/javascript">
              google.charts.load('current', {'packages':['table']});
              google.charts.setOnLoadCallback(drawTable);
        
              function drawTable() {
                var data = new google.visualization.DataTable();
                data.addColumn('string', 'Image Name');
                data.addColumn('string', 'Image Url');
                """
    fb.write(message1)
    message2="""data.addRows([['Mike',  %s],]);"""
    fb.write("data.addRows("+str(uri)+");")

    message3="""
                var table = new google.visualization.Table(document.getElementById('table_div'));
        
                table.draw(data, {showRowNumber: true, width: '40%', height: '30%'});
              }
            </script>
          </head>
          <body>
            <div id="table_div"></div>
          </body>
        </html>
        """

    fb.write(message3)
    fb.close()
    #webbrowser.open_new_tab('helloworld.html')

def create_folder(service):
        file_metadata = {
        'name': 'Test Techm',
        'mimeType': 'application/vnd.google-apps.folder'
        }
        file = service.files().create(body=file_metadata,
                                    fields='id').execute()
        print('Folder ID: %s' % file.get('id'))

def main():
    service = get_gdrive_service()
    print("Wait a movement script is running ..!!!")
    results = service.files().list(pageSize=60, fields="nextPageToken,files(id, name,mimeType,parents,webViewLink)").execute()
    items = results.get('files', [])
    if not items:
        # empty drive
        print('No files found.')
    else:
        #create_folder(service)
        print(check_duplicate_image(items))
        #createDeviceCSV()
        #html()
        list_files(items,service)


if __name__ == '__main__':
    main()

    print("Script is done ..!!!")
