#*****************************************************************************************************************************************************
# Description 				Using the Service Now REST API, this python script downloads all tasks related to ACE tickets into a CSV.
#
# Change Log	User	    Description
# -----------------------------------------------------------------------------------------------------------------------------------------------------
# 2020-12-21 	JFU		    Inital script published to Jon, Jim, and Yosh
# 2020-12-22    JFU         Changed the table used for the query from TASK to SC_TASK because of what I learned from the ServiceNow community forums
#                           where a user explained: "sc_task" table is the table name for Catalog TASK while "task" table is the parent or base table
#                           for all the different kinds of tickets(Incident, Problem, SCTASK, RITM, REQ, CHG etc).
#******************************************************************************************************************************************************

import requests # HTTP request
import getpass # Hide password input
from emailerException import ServiceNowAPIError

# For CSV Processing
import xml.etree.ElementTree as et
import xmltodict as xd
import pandas as pd


# Set the request parameters
#   sysparm_exclude_reference_link - If this is set to false or left out of the URL, then fields that reference
#                                    other SN tables will include two child XML elements: the system id and a
#                                    URL to that object within SN
#
#   sysparm_display_value          - If this is set to false or left out of the URL, then fields that reference
#                                    other SN tables will have SN's system ID for the reference table's key,
#                                    however, if you set this to true, the API will do the "join" for you and
#                                    return the lookup name
#   sysparm_fields                 - If you want do dot walk to other tables you have to explicitly list them
#                                    using this paramater.  The downside is that you then have to explitly
#                                    list out every field you want from the original table
#   sysparm_limit                  - How many "rows" to return
#   request_item.cat_item.sys_id   - XXXXXX is the "Analytics Center of Excellence (ACE)"
#                                    catalog item.  We want to search for this in case there are tickets that
#                                    haven't been assigned to anyone
#   assigned_to.sys_id             - XXXXXX
#
#   FROM: https://community.servicenow.com/community?id=community_question&sys_id=9eb8631cdbd1a010fa192183ca961910&anchor=answer_b49a8820db1da010fa192183ca9619e5
#   The "sc_task" table is the table name for Catalog TASK while "task" table is the parent or base table for all the different kinds of tickets(Incident, Problem, SCTASK, RITM, REQ, CHG etc).
sc_task_url = 'https://place-holder-url/api/now/table/sc_task?' \
    'sysparm_display_value=true'\
    '&sysparm_exclude_reference_link=true'\
    '&sysparm_query='\
    'assignment_group.name=ACE - Business'\
    '^ORassignment_group.name=ACE - Quality'\
    '^ORrequest_item.cat_item.sys_id=XXXXXX'\
    '^ORassigned_to.sys_id=XXXXXX'\
    '&sysparm_fields=parent,made_sla,u_nurse_champion,watch_list,sc_catalog,upon_reject,sys_updated_on,task_effective_number,approval_history,skills,number,sys_updated_by,u_physician_champion'\
    ',opened_by,user_input,sys_created_on,sys_domain,state,route_reason,sys_created_by,knowledge,order,calendar_stc,closed_at,cmdb_ci,impact,u_pending_reason,active,work_notes_list'\
    ',business_service,priority,sys_domain_path,time_worked,expected_start,opened_at,business_duration,group_list,work_end,approval_set,u_covid_flag,universal_request,request'\
    ',short_description,correlation_display,work_start,assignment_group,additional_assignee_list,description,calendar_duration,close_notes,service_offering,sys_class_name,closed_by'\
    ',follow_up,sys_id,contact_type,urgency,company,reassignment_count,activity_due,assigned_to,approval,sla_due,due_date,sys_mod_count,request_item'\
    ',sys_tags,escalation,upon_approval,u_task_covid_flag,correlation_id,location'\
    ',request_item.cat_item.name'
    #,request_item.opened_at --the time when the RITM was opened
    #,request.number' --the REQ number

sc_item_url = 'https://place-holder-url/api/now/table/sc_req_item?' \
    'sysparm_display_value=true'\
    '&sysparm_exclude_reference_link=true'\
    '&sysparm_query='\
    'assignment_group.name=ACE - Business'\
    '^ORassignment_group.name=ACE - Quality'\
    '^ORrequest_item.cat_item.sys_id=XXXXXX'\
    '^ORassigned_to.sys_id=XXXXXX'\

#Excluded Fields


# If you want the original system_id vaues instead of the "English" lookup that is included with
# using sysparm_display_value=True in the URL, set this parameter to false and you can use the
# code below to bring in the System_ID (value or display_value)
"""
# Loop through every result (row)
for result in data_dict['response']['result']:
    # For every result, loop through every key (column)
    for key in result:
       # Check to see if the value for a key is an OrderedDict (basically another dictionary)
       # The Service Now XML output sometimes has additional child elements for the root level elements.  So far as
       # I can see, these child elements are always a Link element and a Value element.  The Link is merely the URL
       # to more detailed information of that particular parent element. For instance, the "Opened By" element has
       # child elements "Link" and "Value".  The Link URL will open the particular user while the Value element is
       # the user's internal Service Now ID. The conversion from XML to Dictionary preserves the child elements as
       # a child dictionary
        if isinstance(result[key], dict):
            # If it's another dictionary, get rid of the Link information and just set it to the Value
            #result[key] = result[key]['value'] # If using sysparm_display_value=false or if it is not set use this
            result[key] = result[key]['display_value'] # If using sysparm_display_value=true then use this
"""
# Note you can't use the following if you have sysparm_display_value=True
# If you use sysparm_display_value=True then any duration field will come through as "X Days Y Hours Z Minutes".
# If there isn't a value, it will come through without the particular time period e.g. 12 Hours 1 Minute.  The
# English value also deals with singular and plural e.g. day vs days.  This function converts the duration string
# into the number of total hours
def convertDurationToHours(duration_string):
    duration = {}

    if duration_string is not None:
        # Process Days
        if duration_string.find('Days') >= 0:
            duration['Days'] = int(duration_string.split('Days')[0])
            duration_string = duration_string.split('Days')[1]
        elif duration_string.find('Day') >= 0:
            duration['Days'] = int(duration_string.split('Day')[0])
            duration_string = duration_string.split('Day')[1]
        else:
            duration['Days'] = 0

        # Process Hours
        if duration_string.find('Hours') >= 0:
            duration['Hours'] = int(duration_string.split('Hours')[0])
            duration_string = duration_string.split('Hours')[1]
        elif duration_string.find('Hour') >= 0:
            duration['Hours'] = int(duration_string.split('Hour')[0])
            duration_string = duration_string.split('Hour')[1]
        else:
            duration['Hours'] = 0

        # Process Minutes
        if duration_string.find('Minutes') >= 0:
            duration['Minutes'] = int(duration_string.split('Minutes')[0])
            duration_string = duration_string.split('Minutes')[1]
        elif duration_string.find('Minute') >= 0:
            duration['Minutes'] = int(duration_string.split('Minute')[0])
            duration_string = duration_string.split('Minute')[1]
        else:
            duration['Minutes'] = 0

        return duration['Days'] * 24 + duration['Hours'] + duration['Minutes'] / 60

def sn_url_to_dataframe(url):

    """
    work_notes - When there are too many notes, it reaches Excel's cell length limit and will carry over to the next line
    comments - When there are too many notes, it reaches Excel's cell length limit and will carry over to the next line
    comments_and_work_notes - When there are too many notes, it reaches Excel's cell length limit and will carry over to the next line
    """
    #print(url) # For debug purposes

    # ask user to type in their username
    user = input('Username:')

    # Set proper headers
    headers = {"Accept":"application/xml"}

    # Do the HTTP request
    pw = getpass.getpass('Password (input will be blank as you type):')
    print('Querying Service Now API...')
    response = requests.get(url, auth=(user, pw), headers=headers)

    # Check for HTTP codes other than 200
    if response.status_code != 200:
        raise ServiceNowAPIError('Status:' + str(response.status_code) + 'Headers:' + str(response.headers) + 'Error Response:' + str(response.content))

    # Decode the XML response into a dictionary and use the data
    with open('tasks.xml', 'w', encoding='utf-8') as file:
        file.write(response.text)
        file.close()

    # Convert the XML file to a dictionary so we can eventually put it into a dataframe for maniuplation
    # and eventually save it as a CSV
    with open('tasks.xml', 'r', encoding='utf-8') as xml_file:
        tree = et.parse(xml_file)

    xml_data = tree.getroot()
    xmlstr = et.tostring(xml_data, encoding='UTF-8', method='xml')

    data_dict = dict(xd.parse(xmlstr))

    # Convert the dictionary to a dataframe for manipulation
    sn_df = pd.DataFrame.from_dict(data_dict['response']['result'])

    # Insert a new column and copy the existing duration value then convert to hours for the three different columns below
    sn_df.insert(sn_df.columns.get_loc('time_worked') + 1, 'time_worked_hours', sn_df['time_worked'])
    sn_df['time_worked_hours'] = sn_df['time_worked_hours'].apply(convertDurationToHours)

    sn_df.insert(sn_df.columns.get_loc('business_duration') + 1, 'business_duration_hours', sn_df['business_duration'])
    sn_df['business_duration_hours'] = sn_df['business_duration_hours'].apply(convertDurationToHours)

    sn_df.insert(sn_df.columns.get_loc('calendar_duration') + 1, 'calendar_duration_hours', sn_df['calendar_duration'])
    sn_df['calendar_duration_hours'] = sn_df['calendar_duration_hours'].apply(convertDurationToHours)
    print('Successfully created dataframe from Service Now API')
    return sn_df

def sn_url_to_csv(url, file_name='Service Now Tasks.csv'):
    df = sn_url_to_dataframe(url)
    df.to_csv(file_name, index=False)