"""
Created on Tue Jan 19 13:32:43 2021
Take a dataframe or file from the Service Now API and transforms to a sorted list of tasks based on the assignment group
Assignment group is one of 'ACE - Business', 'ACE - Quality', IM - EDW Services', 'Unassigned'
Returns a data frame of tasks

@author: schao
"""
from datetime import datetime
import pandas as pd

#'ACE - Quality' : []
#'IM - EDW Serves' : []

ace_dict = {
    # Unassigned should be anyone who tasks would be assigned to regardless of the group they belong to
    'Unassigned' : []
    ,'ACE - Business' : []
}

def map_state_order(state):
    if state == 'Waiting for Approval':
        return 1
    elif state == 'Open':
        return 2
    elif state == 'Requirements Gathering':
        return 3
    elif state == 'Work in Progress':
        return 4
    elif state == 'Customer Testing':
        return 5
    else:
        return 0

def fill_state_with_pending_reason(df):
    fill_state = df.copy()
    for i in range(fill_state.index.stop):
        if fill_state.loc[i,'u_pending_reason'] != 'null':
            fill_state.loc[i, 'state'] = fill_state.loc[i,'u_pending_reason']
    return fill_state

def recurring_flag_check(tags):
    if tags is None:
        return 0
    elif 'Recurring' in tags:
        return 1
    else:
        return 0

def process_sntasks_from_file(file_name='task.csv'):
    # read in tasks.csv
    try:
        raw_df = pd.read_csv(file_name,encoding='cp1252')
    except:
        raise FileNotFoundError(filename=file_name)

    raw_df = raw_df.reset_index(drop=True)

    base_tasks = process_sntasks_from_dataframe(raw_df)
    return base_tasks

def process_sntasks_from_dataframe(data_frame):
    # remove rows where who the request is for is unknown
    df = data_frame.copy()
    df.dropna(inplace=True, subset=['requested_for'])

    raw_df = df.reset_index(drop=True)

    # clean data
    raw_df['assignment_group'] = raw_df['assignment_group'].fillna(value='Unassigned')
    raw_df['assigned_to'] = raw_df['assigned_to'].fillna(value='Unassigned')
    #raw_df['requested_for'] = raw_df['requested_for'].fillna(value='Unknown')
    raw_df['sys_created_by'] = raw_df['sys_created_by'].apply(lambda x: x.lower())

    # fill in the state column with the pending reson if there is one
    base_tasks = fill_state_with_pending_reason(raw_df)

    # add column that check for the recurring flag
    base_tasks['is_recurring'] = base_tasks['sys_tags'].apply(lambda x: recurring_flag_check(x))

    # add column that is just requester's name
    # applies lambda function to the "name (email)" format and returns the beginning of the string to the "(" minus the space
    base_tasks['requester_name'] = base_tasks['requested_for'].apply(lambda x: x[0: x.find('(') - 1])
    base_tasks['requester_email'] = base_tasks['requested_for'].apply(lambda x: x[x.find('(')+1 : -1])
    base_tasks['requester_alias'] = base_tasks['requested_for'].apply(lambda x: x[x.find('(')+1 : x.find('@')])
    base_tasks['requester_alias'] = base_tasks['requester_alias'].apply(lambda x: x.lower())

    # add column that is just the analyst's name, email, or ad name
    base_tasks['assigned_to_name'] = base_tasks['assigned_to'].apply(lambda x: x[0: x.find('(') - 1] if x != 'Unassigned' else x)
    base_tasks['assigned_to_email'] = base_tasks['assigned_to'].apply(lambda x: x[x.find('(')+1 : -1] if x != 'Unassigned' else x)
    base_tasks['assigned_to_alias'] = base_tasks['assigned_to'].apply(lambda x: x[x.find('(')+1 : x.find('@')])
    base_tasks['assigned_to_alias'] = base_tasks['assigned_to_alias'].apply(lambda x: x.lower())

    # create column to track an order of task state
    base_tasks['state_order'] = base_tasks['state'].apply(lambda x: map_state_order(x))

    # convert data types
    base_tasks['sys_updated_on'] = pd.to_datetime(base_tasks['sys_updated_on'])
    base_tasks['sys_created_on'] = pd.to_datetime(base_tasks['sys_created_on'])
    base_tasks['closed_at'] = pd.to_datetime(base_tasks['closed_at'])
    base_tasks['expected_start'] = pd.to_datetime(base_tasks['expected_start'])
    base_tasks['due_date'] = pd.to_datetime(base_tasks['due_date'])
    base_tasks['request_approval_date'] = pd.to_datetime(base_tasks['request_approval_date'])
    base_tasks['request_opened_date'] = pd.to_datetime(base_tasks['request_opened_date'])

    return base_tasks

def get_group_sntasks(dataframe, assignment_group='ACE - Business'):

    # filter to specified assignment group
    df = dataframe[dataframe['assignment_group'] == assignment_group]

    # remove people who belong to the assignment group
    df = df[~df['requester_alias'].isin(ace_dict[assignment_group])]

    # sort open tasks by creation date ascending
    base_sorted = df.sort_values(by=['state','sys_created_on'], ascending=True)

    # create the place in queue for the Open tasks.
    # ranks the task by state and created date. method of first keeps the order that the tasks were sorted by
    base_sorted['place_in_queue'] = base_sorted.groupby('state')['sys_created_on'].rank(method='first')

    # create the task number for each requester. this is how many ACE requests a person has
    # rank by created date
    base_sorted['requester_task_num'] = base_sorted.groupby('requester_alias')['sys_created_on'].rank(method='first')

    # note this creates a timedelta object for column days_in_queue. use ".days" to get the days on this object
    base_sorted['days_in_queue'] = pd.to_datetime(datetime.today()) - base_sorted['sys_created_on']

    # format date values from datetime to string for user friendly view
    base_sorted['sys_updated_on'] = base_sorted['sys_updated_on'].dt.strftime('%b %d, %Y')
    base_sorted['sys_created_on'] = base_sorted['sys_created_on'].dt.strftime('%b %d, %Y')
    base_sorted['closed_at'] = base_sorted['closed_at'].dt.strftime('%b %d, %Y')
    base_sorted['expected_start'] = base_sorted['expected_start'].dt.strftime('%b %d, %Y')
    base_sorted['due_date'] = base_sorted['due_date'].dt.strftime('%b %d, %Y')
    base_sorted['request_approval_date'] = base_sorted['request_approval_date'].dt.strftime('%b %d, %Y')
    base_sorted['request_opened_date'] = base_sorted['request_opened_date'].dt.strftime('%b %d, %Y')

    return base_sorted

def get_requester_tasks(dataframe, requester):
    # filter to specified requester
    df = dataframe[dataframe['requester_alias'] == requester]
    df = df.sort_values(by=['requester_task_num'], ascending=True)

    return df

def process_tasks_waiting_for_approval(items, task_columns):
    approval_items = items[items['stage'] == 'Waiting for Approval']
    if not approval_items.empty:
        # rename/insert columns from approval items into temp dataframe to eventually union to tasks
        item_aliases = {
             'number':'item_number'
            ,'opened_at':'request_opened_date'
            ,'state':'item_state'
            ,'stage':'state'
            ,'u_task_covid_flag': 'u_covid_flag'
            ,'request.requested_for': 'requested_for'
        }
        approval_items = approval_items.rename(columns=item_aliases)
        approval_items.insert(len(approval_items.columns),'u_pending_reason', 'null')
        approval_items.insert(len(approval_items.columns),'task_number', None)
        approval_items.insert(len(approval_items.columns),'request_approval_date', None)
        approval_items.insert(len(approval_items.columns),'request_number', approval_items['request'])
        # process items with the same columns as the tasks
        approval_df = process_sntasks_from_dataframe(approval_items[task_columns])
        approval_tasks = get_group_sntasks(approval_df, 'Unassigned')
        return approval_tasks
    else:
        return approval_items
