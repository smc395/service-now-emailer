# -*- coding: utf-8 -*-
"""
Created on Wed Jan 20 08:16:16 2021

@author: schao
Remember, indentation matters in Python! (i.e. it's not just aesthetics)
"""
from emailerException import SendSMTPEmailError, ServiceNowAPIError
import service_now_processor as sp
import send_email_smtp as se
import jinja_sntasks as j
from datetime import datetime
import pandas as pd
import sys
import service_now_api as snapi

#columns to be used in the sc_task table for SN Tasks (SCTASK)
task_columns = [
    'parent'
    ,'sys_updated_on'
    #,'number'
    ,'sys_updated_by'
    ,'opened_by'
    ,'sys_created_on'
    ,'state'
    ,'sys_created_by'
    ,'closed_at'
    ,'impact'
    ,'u_pending_reason'
    ,'active'
    ,'priority'
    ,'time_worked'
    ,'time_worked_hours'
    ,'expected_start'
    ,'due_date'
    #,'opened_at'
    ,'u_covid_flag'
    #,'work_notes'
    ,'request'
    ,'short_description'
    ,'assignment_group'
    ,'additional_assignee_list'
    ,'description'
    ,'closed_by'
    ,'sys_id'
    ,'urgency'
    ,'assigned_to'
    ,'comments'
    #,'comments_and_work_notes'
    #,'request_item'
    ,'sys_tags'
    ,'escalation'
    #,'request_item.opened_at'
    #,'request.number'
    ,'request_opened_date'
    ,'request_number'
    ,'task_number'
    ,'item_number'
    ,'request_approval_date'
    ,'requested_for'
]

#columns to be used in the sc_req_item table for SN Items (RITM)
item_columns =[
    'requested_for'
    ,'sys_updated_on'
    #,'number'
    ,'item_number'
    ,'sys_updated_by'
    ,'opened_by'
    ,'sys_created_on'
    ,'state'
    ,'sys_created_by'
    ,'closed_at'
    ,'impact'
    ,'active'
    ,'priority'
    #,'opened_at'
    ,'request_opened_date'
    ,'approval_set'
    #,'work_notes'
    ,'request'
    ,'short_description'
    ,'closed_by'
    ,'follow_up'
    ,'sys_id'
    ,'urgency'
    ,'assigned_to'
    ,'comments'
    ,'approval'
    #,'comments_and_work_notes'
    ,'due_date'
    ,'cat_item'
    ,'stage'
]

# write a given message to a log file
def writeToLog(message):
    fileName = 'emailLog_' + pd.to_datetime(datetime.today()).strftime('%Y_%m_%d') + '.txt'

    with open('./' + fileName, 'at', newline='\n', encoding='utf-8') as f:
        f.write(message)

# export the columns of dataframe to csv to mimic emailer output
def export_df_to_csv(dataframe, exportFileName = 'default', exportColumns = []):
    fileName = exportFileName + pd.to_datetime(datetime.today()).strftime('%Y_%m_%d') + '.csv'

    if len(exportColumns) == 0:
        writeToLog('🗙 No columns given to export from dataframe for file ' + exportFileName + '\n')
    else:
        dataframe.to_csv(path_or_buf = './' + fileName, index = False, columns = exportColumns)

# get all service now tickets from URL
def get_all_sn_tickets(task_url, item_url, task_exclusion_list=[]):
    #TODO figure out a way to identify recurring tasks and discuss how to handle them
    #TODO determine a way to display the analyst work notes from SN tasks
    try:
        # get datafarme of Service Now tasks from API
        print('\n\nGet Service Now tasks with API. Input Service Now credentials and press Enter')
        sn_tasks = snapi.sn_url_to_dataframe(task_url)
        writeToLog('✓ Successfully created task dataframe from Service Now API\n')

        # get dataframe of Service Now items from API
        print('\n\nGet Service Now items with API. Input Service Now credentials and press Enter')
        sn_items = snapi.sn_url_to_dataframe(item_url)
        writeToLog('✓ Successfully created item dataframe from Service Now API\n')
    except ServiceNowAPIError as e:
        print('\nService Now API error. Check service_now_api.py and log file.', file=sys.stderr)
        writeToLog('🗙 Service Now API Error = ' + str(e) + '\n')
        sys.exit()

    # read in csv of tasks
    # tasks = sp.process_sntasks_from_file('task.csv')

    # rename column names
    task_aliases = {
        'request_item.opened_at':'request_opened_date'
        , 'opened_at':'request_approval_date'
        , 'number':'task_number'
        , 'sys_id':'task_sys_id'
        , 'request_item':'item_number'
        , 'request.number':'request_number'
        , 'request.requested_for': 'requested_for'
        , 'request_item.sys_id':'item_sys_id'
    }
    sn_tasks.rename(columns=task_aliases, inplace=True)

    # process tasks using the renamed column names
    tasks = sp.process_sntasks_from_dataframe(sn_tasks[sn_tasks.columns])

    # process items needing approval
    # task_columns uses original names of columns and differs than sn_tasks column names
    approvals = sp.process_tasks_waiting_for_approval(sn_items, task_columns)

    # get the tasks for specified ACE group
    # assignment_group is one of 'ACE - Business', 'ACE - Quality', IM - EDW Services', 'Unassigned'
    group = 'ACE - Business'
    group_tasks = sp.get_group_sntasks(tasks, assignment_group=group)

    # if there are items that are waiting on approval, append with group tasks
    if not approvals.empty:
        all_tasks = pd.concat([group_tasks, approvals], ignore_index=True)
    else:
        all_tasks = group_tasks

    writeToLog('✓ Successfully retrieved all tasks for ' + group + '\n')

    # return all tasks excluding the ones in the exclusion list
    return all_tasks[~all_tasks['task_number'].isin(task_exclusion_list)]

# create CSV export for analysis using set columns
def create_csv(tasks, fileName):
    # unique list of requester name and email
    #distinctRequester = all_tasks[['requester_name', 'requester_email']].drop_duplicates()

    # export data to csv to refer to if requester asks questions
    try:
        col = [
              'assigned_to_name'
            , 'state'
            , 'requester_name'
            , 'requester_email'
            , 'requester_task_num'
            , 'item_number'
            , 'task_number'
            , 'short_description'
            , 'sys_updated_on'
            , 'sys_updated_by'
            , 'opened_by'
            , 'request_opened_date'
            , 'request_approval_date'
            , 'due_date'
            , 'place_in_queue'
            , 'days_in_queue'
        ]

        export_df_to_csv(dataframe = tasks, exportFileName=fileName, exportColumns = col)
        writeToLog('✓ Successfully created '+ fileName + ' CSV export\n')
    except Exception as e:
        print('\nUnable to create CSV. Check log file.', file=sys.stderr)
        writeToLog('🗙 ' + str(e) + '\n')

# send emails to requesters
def send_email(task_df):
    group_open_queue_size = len(task_df[task_df['state'] == 'Open'])

    # get unique list of requesters
    # DEBUG comment requester_list line out and add your own array of alias
    # Example: request_list = ['schao']
    requester_list = task_df['requester_alias'].unique()

    # email prep
    today_dt = pd.to_datetime(datetime.today()).strftime('%B %d, %Y')
    email_subject = 'Data Request Status - ' + today_dt
    #email_subject = group + ' Data Request Status - ' + today_dt
    asset_path = './templates/assets/'

    # establish SMTP connection
    try:
        smtp = se.open_smtp_connection()
        writeToLog('✓ Successfully established SMTP connection\n')
    except Exception as e:
        print('\nSMTP connection error. Check send_email_smtp.py and log file.', file=sys.stderr)
        writeToLog('🗙 ' + str(e) + '\n')
        sys.exit()

    # for each requester in the group, generate an HTML email of their open tickets
    for r in requester_list:
        try:
            r_tasks = sp.get_requester_tasks(dataframe=task_df, requester=r)

            email_body = j.create_requester_email_body(
                template_file = 'child_sliding_pointer.html'
                , requester_tasks = r_tasks
                , group_email = 'group@email'
                , escalation_email = 'manager@email'
                , queue_size = group_open_queue_size
                , today_date = today_dt
            )
        except Exception as e:
            print('\nCreate email error. Check log file.', file=sys.stderr)
            writeToLog('🗙 Error creating email body for ' + r + '. ' + str(e) + '\n')
            continue

        try:
            # DEBUG comment recipient_list line out and add your own array of email
            # Example: recipient_list = ['schao@email']
            recipient_list = [r_tasks.iloc[0].requester_email]
            copies_list = []

            se.send_outlook_html_mail(smtp_obj=smtp, recipients=recipient_list, subject=email_subject, body=email_body, asset_path=asset_path, copies=copies_list)
            writeToLog('✓ Successfully created email body for ' + r_tasks.iloc[0].requester_name + ' and sent email to ' + r_tasks.iloc[0].requester_email + '\n')
        except SendSMTPEmailError as e:
            print('\nSend email error. Check send_email_smtp.py and log file.', file=sys.stderr)
            writeToLog('🗙 Error sending email for ' + r + '. ' + str(e) + '\n')
            continue

    se.close_smtp_connection(smtp_connection=smtp)
    writeToLog('✓ Successfully closed SMTP connection\n')

def historicalExport(exclusion_list):
    # get a list of tickets opened in the past fiscal year excluding the state Closed Incomplete
    historical_sc_task_url = 'https://place-holder-email/api/now/table/sc_task?' \
        'sysparm_display_value=true'\
        '&sysparm_exclude_reference_link=true'\
        '&sysparm_query=state!=4'\
        '^assignment_group.name=ACE - Business'\
        '^ORassignment_group.name=ACE - Quality'\
        '^ORrequest_item.cat_item.sys_id=XXXXXX'\
        '^ORassigned_to.sys_id=XXXXXX'\
        '^opened_at>=javascript:sn_bc.GlideBusinessCalendarUtil.getCalendarStart(\'Fiscal Year\', \'-1\', \'Last Fiscal Year\')'\
        '&sysparm_fields=parent,made_sla,u_nurse_champion,watch_list,sc_catalog,'\
        'upon_reject,sys_updated_on,task_effective_number,approval_history,skills,number,sys_updated_by,'\
        'u_physician_champion,opened_by,user_input,sys_created_on,sys_domain,state,route_reason,sys_created_by,knowledge,'\
        'order,calendar_stc,closed_at,cmdb_ci,impact,u_pending_reason,active,work_notes_list,business_service,'\
        'priority,sys_domain_path,time_worked,time_worked_hours,expected_start,opened_at,business_duration,'\
        'business_duration_hours,group_list,work_end,approval_set,u_covid_flag,work_notes,universal_request,request,'\
        'short_description,correlation_display,work_start,assignment_group,additional_assignee_list,description,'\
        'calendar_duration,calendar_duration_hours,close_notes,service_offering,sys_class_name,closed_by,follow_up,'\
        'sys_id,contact_type,urgency,company,reassignment_count,activity_due,assigned_to,comments,approval,sla_due,'\
        'comments_and_work_notes,due_date,sys_mod_count,request_item,sys_tags,escalation,upon_approval,u_related_record,'\
        'u_task_covid_flag,correlation_id,location,'\
        'request_item.opened_at,request_item.sys_id,request.number,request.requested_for'

    # get a list of tickets opened in the past fiscal year
    historical_sc_req_item_url = 'https://place-holder-email/api/now/table/sc_req_item?'\
        'sysparm_display_value=true&sysparm_exclude_reference_link=true'\
        '&sysparm_query=cat_item.sys_id=XXXXXX'\
        '^opened_at>=javascript:sn_bc.GlideBusinessCalendarUtil.getCalendarStart(\'Fiscal Year\', \'-1\', \'Last Fiscal Year\')'\
        '^state!=4&sysparm_fields='\
        'parent,made_sla,u_nurse_champion,watch_list,sc_catalog,upon_reject,sys_updated_on,task_effective_number'\
        ',approval_history,skills,number,sys_updated_by,u_physician_champion,opened_by,user_input,price,sys_created_on'\
        ',recurring_frequency,sys_domain,state,route_reason,sys_created_by,knowledge,order,u_cancellation,closed_at'\
        ',cmdb_ci,backordered,impact,active,work_notes_list,business_service,priority,sys_domain_path,time_worked,expected_start'\
        ',opened_at,business_duration,group_list,configuration_item,work_end,approval_set,work_notes,order_guide,universal_request'\
        ',request,short_description,correlation_display,work_start,assignment_group,additional_assignee_list,description,calendar_duration'\
        ',close_notes,service_offering,sys_class_name,closed_by,follow_up,sys_id,contact_type,urgency,company,reassignment_count'\
        ',activity_due,assigned_to,comments,quantity,approval,sla_due,comments_and_work_notes,due_date,sys_mod_count,recurring_price'\
        ',sys_tags,billable,cat_item,stage,escalation,upon_approval,u_task_covid_flag,correlation_id,location,estimated_delivery'\
        ',request.requested_for'

    # get all Service Now tickets with URL parameters, excluding tasks in the exclusion list
    historical_tasks = get_all_sn_tickets(task_url = historical_sc_task_url, item_url = historical_sc_req_item_url, task_exclusion_list = exclusion_list)

    # create CSV export for analyst and historical
    create_csv(historical_tasks, fileName='historicalEmailerExport_')

def service_now_emailer(exclusion_list):
    # ========================================================================================================
    # Service Now API URL: https://developer.servicenow.com/dev.do#!/reference/api/quebec/rest/c_TableAPI
    #   * processed by service_now_api.py
    #   * request_item.opened_at : the time when the RITM was opened
    #   * request.number' : the REQ number
    #   * request.requested_for' : the person the request is for, this may be different from who opened the ticket
    #   * state 3 = Closed Complete; state 4 = Closed Incomplete
    # ========================================================================================================
    sc_task_url = 'https://place-holder-email/api/now/table/sc_task?' \
        'sysparm_display_value=true'\
        '&sysparm_exclude_reference_link=true'\
        '&sysparm_query=state!=3^state!=4'\
        '^assignment_group.name=ACE - Business'\
        '^ORassignment_group.name=ACE - Quality'\
        '^ORrequest_item.cat_item.sys_id=XXXXXX'\
        '^ORassigned_to.sys_id=XXXXXX'\
        '&sysparm_fields=parent,made_sla,u_nurse_champion,watch_list,sc_catalog,'\
        'upon_reject,sys_updated_on,task_effective_number,approval_history,skills,number,sys_updated_by,'\
        'u_physician_champion,opened_by,user_input,sys_created_on,sys_domain,state,route_reason,sys_created_by,knowledge,'\
        'order,calendar_stc,closed_at,cmdb_ci,impact,u_pending_reason,active,work_notes_list,business_service,'\
        'priority,sys_domain_path,time_worked,time_worked_hours,expected_start,opened_at,business_duration,'\
        'business_duration_hours,group_list,work_end,approval_set,u_covid_flag,work_notes,universal_request,request,'\
        'short_description,correlation_display,work_start,assignment_group,additional_assignee_list,description,'\
        'calendar_duration,calendar_duration_hours,close_notes,service_offering,sys_class_name,closed_by,follow_up,'\
        'sys_id,contact_type,urgency,company,reassignment_count,activity_due,assigned_to,comments,approval,sla_due,'\
        'comments_and_work_notes,due_date,sys_mod_count,request_item,sys_tags,escalation,upon_approval,u_related_record,'\
        'u_task_covid_flag,correlation_id,location,'\
        'request_item.opened_at,request_item.sys_id,request.number,request.requested_for'

    sc_req_item_url = 'https://place-holder-email/api/now/table/sc_req_item?'\
        'sysparm_display_value=true&sysparm_exclude_reference_link=true'\
        '&sysparm_query=cat_item.sys_id=XXXXXX'\
        '^state!=3^state!=4&sysparm_fields='\
        'parent,made_sla,u_nurse_champion,watch_list,sc_catalog,upon_reject,sys_updated_on,task_effective_number'\
        ',approval_history,skills,number,sys_updated_by,u_physician_champion,opened_by,user_input,price,sys_created_on'\
        ',recurring_frequency,sys_domain,state,route_reason,sys_created_by,knowledge,order,u_cancellation,closed_at'\
        ',cmdb_ci,backordered,impact,active,work_notes_list,business_service,priority,sys_domain_path,time_worked,expected_start'\
        ',opened_at,business_duration,group_list,configuration_item,work_end,approval_set,work_notes,order_guide,universal_request'\
        ',request,short_description,correlation_display,work_start,assignment_group,additional_assignee_list,description,calendar_duration'\
        ',close_notes,service_offering,sys_class_name,closed_by,follow_up,sys_id,contact_type,urgency,company,reassignment_count'\
        ',activity_due,assigned_to,comments,quantity,approval,sla_due,comments_and_work_notes,due_date,sys_mod_count,recurring_price'\
        ',sys_tags,billable,cat_item,stage,escalation,upon_approval,u_task_covid_flag,correlation_id,location,estimated_delivery'\
        ',request.requested_for'

    all_tasks = get_all_sn_tickets(task_url = sc_task_url, item_url = sc_req_item_url, task_exclusion_list = exclusion_list)

    # create CSV export for analyst and historical
    create_csv(all_tasks, fileName='analystEmailerExport_')

    # comment out send_email when running historical
    send_email(task_df = all_tasks)

if __name__ == '__main__':

    print('In main.py')

    # create log file to capture success/errors
    writeToLog('----Begin Service Now Emailer run at ' + str(pd.to_datetime(datetime.today())) + '----\n')

    # Service Now task exclusion list
    exclusion_list = ['SCTASKXXXXXX']

    service_now_emailer(exclusion_list)

    # uncomment historicalExport() and comment out service_now_emailer() when doing a historical export
    # historicalExport(exclusion_list)

    writeToLog('----End of Service Now Emailer run----\n')

    print('\nScript finished')
