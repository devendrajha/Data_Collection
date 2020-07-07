import csv
import io
import pickle
import os
import pip
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
import cv2
import numpy as np

SCOPES = ['https://www.googleapis.com/auth/drive.metadata',
          'https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/drive']


def install(package):
    if hasattr(pip, 'main'):
        pip.main(['install', package])
    else:
        pip._internal.main(['install', package])


def create_folder(service):
    file_metadata = {
        'name': 'Test Techm',
        'mimeType': 'application/vnd.google-apps.folder'
    }
    file = service.files().create(body=file_metadata,
                                  fields='id').execute()
    print('Folder ID: %s' % file.get('id'))


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
        print("AFTER : In Download function : {0} and status {1} and status progress {2}".format(done, status, int(
            status.progress())))
        print("AFTER : In Download function DONE : {0}".format(done))
        # print("BEFORE : In Download function var : {0}".format(var))
        print("Download %d%%." % int(status.progress() * 100))
        with io.open("." + "/" + name, 'wb') as f:
            fh.seek(0)
            f.write(fh.read())


def duplicate_image_list(imagelist):
    dup_list = []
    if len(imagelist) >= 1:
        for i in range(len(imagelist) - 1):
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


csv_map = {}


def check_duplicate_image(items):
    # """given items returned by Google Drive API, prints them in a tabular way"""
    map = {}
    image_name_list = []
    duplicate_image = []
    for item in items:
        file_type = item["mimeType"]
        if file_type == "image/jpeg":
            image_name_list.append(item["name"])
            # Creating Map
            value = []
            value.append(item["name"])
            value.append(item["webViewLink"])
            map[item["id"]] = value
            csv_map[item["name"]] = item["webViewLink"]
            # Dowloading Image
            downloadFile(item["id"], item["name"])
    duplicate_image = duplicate_image_list(image_name_list)

    return duplicate_image


def renameFile(id, newName):
    service = get_gdrive_service()
    file = service.files().get(fileId=id).execute()
    del file['id']
    file['name'] = newName + ".jpg";
    updated_file = service.files().update(fileId=id, body=file).execute()


def count_image(id):
    imageList = []
    service = get_gdrive_service()
    results = service.files().list(pageSize=30, q="'{}' in parents".format(id)).execute()
    items = results.get('files', [])
    for item in items:
        mime_Type = item["mimeType"]
        if mime_Type == "image/jpeg":
            imageList.append(item["name"])
        if mime_Type == "application/vnd.google-apps.folder":
            imageList.extend(count_image(item["id"]))

    return imageList


def list_files(items, service):
    folder_count = 0
    image_count = 0
    imglist = []
    count = 0
    testtechm_id = ''
    nm_name = []
    img_count = []

    rows = []
    overview_map = {}
    for item in items:
        id = item["id"]
        name = item["name"]
        mime_type = item["mimeType"]
        if name == 'Test Techm':
            testtechm_id = item['parents'][0]
        if mime_type == "application/vnd.google-apps.folder":
            folder_count = folder_count + 1
            folder_name = item["name"]
        if mime_type == "image/jpeg":
            # renameFile(item["id"],"rajj_img"+str(image_count))
            image_count = image_count + 1
        if mime_type == "application/vnd.google-apps.folder" and item["parents"][0] == testtechm_id:
            name1 = count_image(id)
            nm_name.append(name1)
            img_count.append(len(name1))
            overview_map[item["name"]] = name1

        rows.append((id, name, mime_type, folder_count))
        imglist.append(count)
        rows.append((id, name, mime_type, folder_count))

    duplicate_count = len(check_duplicate_image(items))
    # 2nd report page

    duplicateImagehtml(folder_count, image_count, duplicate_count)
    # overview chart report page

    draw_chart_create_report(folder_count, image_count, duplicate_count, overview_map)


def createDeviceCSV():
    fileName = 'DuplicateImage.csv'
    with open(fileName, 'w') as csvFile:
        writer = csv.writer(csvFile)
        row = ["Image Name", 'Image Url']
        writer.writerow(row)
        count = 0
        for k, v in csv_map.items():
            row = [k, v]
            writer.writerow(row)
            count = count + 1
            print("Device's adding into csv: " + str(count))
        csvFile.close()
        print('Device CSV File creation is Done file name is ', fileName)


def duplicateImagehtml(folder_count, image_count, duplicate_count):
    uri = []
    for k, v in csv_map.items():
        name_url = []
        name_url.append(k)
        name_url.append(v)
        uri.append(name_url)
    print(str(uri))

    fb = open('duplicateData.html', 'w')
    message = """ <html>  <head>
            <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
            <script type="text/javascript">
              google.charts.load('current', {'packages':['table']});
              google.charts.setOnLoadCallback(drawTable);
              function drawTable() {
                var data3 = new google.visualization.DataTable();
                data3.addColumn('string', 'Name');
                data3.addColumn('string', 'Count');
                data3.addRows([
                    ['Total Folders', """ + str(folder_count) + """],
                    ['Total Images',  """ + str(image_count) + """],
                    ['Duplicate Images', """ + str(duplicate_count) + """]]);

            var table2 = new google.visualization.Table(document.getElementById('table_div_base'));

            table2.draw(data3, {showRowNumber: true, width: '100%', height: '100%'});
              var data = new google.visualization.DataTable();
              data.addColumn('string', 'Image Name');
              data.addColumn('string', 'Image Url');
                data.addRows(""" + str(uri) + """);
                var table = new google.visualization.Table(document.getElementById('table_div'));
                table.draw(data, {showRowNumber: true, width: '100%', height: '100%'});
              }
                </script>
            </head>
          <body><h2 style="text-align: center">Google Drive Summary Table</h2>
                <div id="table_div_base" style="width: 100%; height: 200px; display:inline-block;border-style: solid"></div>
                <h2 style="text-align: center" >List of Duplicate Image</h2>
                <div id="table_div" style="width: 100%; height: 500px; display:inline-block;border-style: solid"></div>
          </body></html>"""

    fb.write(message)
    fb.close()
    # webbrowser.open_new_tab('helloworld.html')


def draw_chart_create_report(folder_count, image_count, duplicate_count, map):
    fb = open('gDriveOverview.html', 'w')
    values = list(map.values())
    newlist = []
    folder_name = list(map.keys())
    total_image_count = []
    duplicate_image_count_in_folder = []
    for v in values:
        newlist.append(duplicate_image_list(v))
        total_image_count.append(len(v))
    for n in newlist:
        duplicate_image_count_in_folder.append(len(n))
    # create plot
    print(total_image_count, duplicate_image_count_in_folder, map.keys())
    m1 = """<html>
              <head>
              <h1 style ="color:black;text-align: center;font-size:25px;margin-left:-6px;margin-bottom:25px;width:1300px;float:left;">Google Drive Data Overview</h1>
                <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
                <script type="text/javascript">
                  google.charts.load('current', {'packages':['bar','corechart','table']});
                  google.charts.setOnLoadCallback(drawChart);
                  function drawChart() {
                    var paiData = google.visualization.arrayToDataTable([
                      ['Drive', 'Drive Data'],
                      ['Total Images',     """ + str(image_count) + """],
                      ['Total duplicate Images', """ + str(duplicate_count) + """],
                      ['Total Folder',  """ + str(folder_count) + """]
                      ]);
                    var paiOptions = {
                      title: 'Google Drive Overview'
                    };
                    var chart = new google.visualization.PieChart(document.getElementById('piechart'));
                    chart.draw(paiData, paiOptions);
                    var barData = google.visualization.arrayToDataTable("""
    fb.write(m1)
    barchart_data = []
    barchart_data.append(['Folders', 'Total no of Images', 'Total no of duplicate Images'])
    for i in range(len(values)):
        item_list = []
        item_list.append(folder_name[i])
        item_list.append(total_image_count[i])
        item_list.append(duplicate_image_count_in_folder[i])
        barchart_data.append(item_list)

    fb.write(m1)
    m3 = str(barchart_data) + """);
            
                    var barOptions = {
                      chart: {  title: 'Google Drive Folderwise Overview',
                        subtitle: 'This report is created on '+new Date(),
                      }};
            
                    var chart = new google.charts.Bar(document.getElementById('bar_chart'));
            
                    chart.draw(barData, google.charts.Bar.convertOptions(barOptions));
                    }
                </script>
              </head>
              <body>
              <div style="width:100%; margin:0px auto;">
                <div id="piechart" style="width: 900px; height: 500px; display:inline-block;"></div>
                <div id="bar_chart" style="width: 900px; height: 500px; display:inline-block;"></div>
            </div>
            <div>
            <h2>
            <p style="float:right;color:red;">** <a href="duplicateData.html" target="_blank">Click here to know more about duplicate image data</a></p>
            </h2></div></body></html>
    """
    fb.write(m3)
    fb.close()


def main():
    service = get_gdrive_service()
    print("Wait a movement script is running ..!!!")
    results = service.files().list(pageSize=30,
                                   fields="nextPageToken,files(id, name,mimeType,parents,webViewLink)").execute()
    items = results.get('files', [])
    if not items:
        # empty drive
        print('No files found.')
    else:
        # create_folder(service)
        check_duplicate_image(items)
        # createDeviceCSV()
        # html()
        list_files(items, service)


if __name__ == '__main__':
    main()
    print("Script is done ..!!!")
