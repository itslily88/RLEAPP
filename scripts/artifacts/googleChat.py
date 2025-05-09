# Module Description: Parses Google Chat messages from Takeout
# Author: @KevinPagano3 & John Hyla {jfhyla@gmail.com}
# Date: 2022-03-08
# Updated: 2022-08-01 (Added Group Members to data)
# Artifact version: 0.0.2
# Requirements: none

import datetime
import json
import os

from pathlib import Path
from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline, is_platform_windows, media_to_html

def get_googleChat(files_found, report_folder, seeker, wrap_text):
    
    data_list = []
    data_list_tsv = []
    monthDict={'January':1, 
           'February':2,
           'March':3,
           'April':4,
           'May':5,
           'June':6,
           'July':7,
           'August':8,
           'September':9,
           'October':10,
           'November':11,
           'December':12}
    
    for file_found in files_found:
        file_found = str(file_found)
        
        if not os.path.basename(file_found) == 'messages.json': # skip -journal and other files
            continue

        with open(file_found, encoding = 'utf-8', mode = 'r') as f:
            data = json.loads(f.read())
        
        group_info_file = os.path.dirname(file_found) + os.path.sep + 'group_info.json'
        if Path(group_info_file).is_file():
            with open(group_info_file, encoding = 'utf-8', mode = 'r') as fg:
                group_data = json.loads(fg.read())
            
            members = []
            for member in group_data["members"]:
                members.append(member.get('name', '') + ' - ' + member.get('email',''))
                
            members_html = '<br>'.join(members)
            members_tsv = '\n'.join(members)
        else:
            members_html = ''
            members_tsv = ''
        
        for chat_message in data['messages']:
            month = ''
            #Possible to have deleted messages. created_date, creator doesn't exists for this messages.
            #example: {"message_state": "DELETED", 
            #          "deleted_date": "Wednesday, 4 January 2023 at 10:59:50 UTC", 
            #          "topic_id": "0o-KXA8ap5g,
            #          "deletion_metadata": {"deletion_type": "CREATOR"}
            #         }
            created_date = chat_message.get('created_date','')
            deleted_date = chat_message.get('deleted_date','')
            if created_date == '' and deleted_date == '':
                continue

            if created_date == '':
                created_data = deleted_date;
                chat_message['creator']={}
                chat_message['creator']['name']='deleted'

            sender_name = chat_message['creator'].get('name','')
            sender_email = chat_message['creator'].get('email','')
            sender_user_type = chat_message['creator'].get('user_type','')
            
            #checks for empty date field
            created_date_split = created_date.split(', ')
            if len(created_date_split)==3:
                created_month = str(created_date_split[1].split(' ')[0])
                created_day = created_date_split[1].split(' ')[1]
                created_year = created_date_split[2].split(' ')[0]
                created_time = created_date_split[2].split(' ')[2]
                time_flag = str(created_date_split[2].split(' ')[3])
            else: 
                if (len (created_date_split))==2:
                    #Example: Tuesday, 7 February 2021 at 17:13:43 UTC
                    #Probably other formats are exposed by Google. Need to transform all dates,
                    #in a standard format.
                    created_date_split2 = created_date_split[1].split(' at ')
                    created_month = str(created_date_split2[0].split(' ')[1])
                    created_day = created_date_split2[0].split(' ')[0]
                    created_year = created_date_split2[0].split(' ')[2]
                    created_time = created_date_split2[1]
                    time_flag = ""
                    
            time_hour = created_time.split(':')[0]
            time_minute = created_time.split(':')[1]
            time_second = created_time.split(':')[2]
            
            if time_flag == 'PM' and int(time_hour) < 12:
                time_hour = str(int(time_hour) + 12)
            else: time_hour = str(time_hour)
            
            if time_flag == 'AM' and int(time_hour) == 12:
                time_hour = '00'

            if len(time_hour) < 2:
                time_hour = '0' + time_hour
            
            if created_month in monthDict.keys():
                month = str(monthDict[created_month])
            
            if len(month) < 2:
                month = '0' + month
            
            if len(created_day) < 2:
                created_day = '0' + created_day
            
            datestamp = created_year + '-' + month + '-' + created_day
            timestamp = time_hour + ':' + time_minute + ':' + time_second
            
            datetime_stamp = datestamp + ' ' + timestamp
            
            message_text = chat_message.get('text','')
            message_text_tsv = chat_message.get('text','').encode("ascii", errors="backslashreplace")
            message_text_tsv = message_text_tsv.decode('ascii')
            message_text_tsv = message_text_tsv.replace(u'\xa0',u' ')    
            
            if 'attached_files' in chat_message:
                if len(chat_message['attached_files']) == 0:
                    attachments = '' 
                    ipAddr = ''
                else:
                    attachments = chat_message['attached_files'][0].get('export_name','')
                    attachments = media_to_html(attachments, files_found, report_folder)
                    ipAddr = (chat_message.get('upload_metadata', [{}])[0].get('backend_upload_metadata', {}).get('upload_ip')
                              if chat_message.get('upload_metadata') else '')
            else: 
                attachments = ''
                ipAddr = ''
            data_list.append((datetime_stamp,sender_name,sender_email,sender_user_type,members_html,message_text,attachments,ipAddr))
            data_list_tsv.append((datetime_stamp,sender_name,sender_email,sender_user_type,members_tsv,message_text_tsv,attachments,ipAddr))
    
    
    directory = os.path.dirname(file_found)
    num_entries = len(data_list)
    if num_entries > 0:
        report = ArtifactHtmlReport('Google Chat - Messages')
        report.start_artifact_report(report_folder, 'Google Chat - Messages')
        report.add_script()
        data_headers = ('Created Timestamp','Sender Name','Sender Email','Sender Type','Group Members','Message','Attachment','IP Address')

        report.write_artifact_data_table(data_headers, data_list, directory, html_no_escape=['Group Members','Attachment'])
        report.end_artifact_report()
        
        tsvname = f'Google Chat - Messages'
        tsv(report_folder, data_headers, data_list_tsv, tsvname)
        
        tlactivity = f'Google Chat - Messages'
        timeline(report_folder, tlactivity, data_list, data_headers)
    else:
        logfunc('No Google Chat - Messages data available')

__artifacts__ = {
        "googleChat": (
            "Google Takeout Archive",
            ('*/Google Chat/Groups/*/**'),
            get_googleChat)
}
