import os
import datetime
import json
import shutil
from pathlib import Path	

from scripts.artifact_report import ArtifactHtmlReport
from scripts.ilapfuncs import logfunc, tsv, timeline, kmlgen, is_platform_windows, utf8_in_extended_ascii, media_to_html

def get_instagramPostsviewed(files_found, report_folder, seeker, wrap_text):
    data_list = []
    for file_found in files_found:
        file_found = str(file_found)
        
        filename = os.path.basename(file_found)
        
        if filename.startswith('posts_viewed.json'):
            
            with open(file_found, "r") as fp:
                deserialized = json.load(fp)
        
            for x in deserialized['impressions_history_posts_seen']:
                author = x['string_map_data']['Author'].get('value', '')
                timestamp = x['string_map_data']['Time'].get('timestamp', '')
                if timestamp > 0:
                    timestamp = (datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S'))
                    
                data_list.append((timestamp, author))
    
                
    if data_list:
        report = ArtifactHtmlReport('Instagram Archive - Posts Viewed')
        report.start_artifact_report(report_folder, 'Instagram Archive - Posts Viewed')
        report.add_script()
        data_headers = ('Timestamp','Author')
        report.write_artifact_data_table(data_headers, data_list, file_found, html_no_escape=['Media'])
        report.end_artifact_report()
        
        tsvname = f'Instagram Archive - Posts Viewed'
        tsv(report_folder, data_headers, data_list, tsvname)
        
        tlactivity = f'Instagram Archive - Posts Viewed'
        timeline(report_folder, tlactivity, data_list, data_headers)

    else:
        logfunc('No Instagram Archive - Posts Viewed')
                
__artifacts__ = {
        "instagramPostsviewed": (
            "Instagram Archive",
            ('*/ads_and_content/posts_viewed.json'),
            get_instagramPostsviewed)
}