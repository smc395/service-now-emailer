# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 10:42:47 2021

@author: schao
"""
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from emailerException import CreateEmailBodyError

def create_requester_email_body(template_file, requester_tasks, group_email, escalation_email, queue_size, today_date):
    # file name of the HTML template
    f = template_file

    try:
        # set the path of where this script is being run and the templates folder
        directory = str(Path.cwd() / 'templates')

        # https://jinja2docs.readthedocs.io/en/stable/api.html#jinja2.FileSystemLoader
        # create a template environment from the specified path
        env = Environment(loader=FileSystemLoader(directory))

        # load template file from environment
        template = env.get_template(f)

        # set the data for the template to fill in
        data = {
            'requester_name': requester_tasks.iloc[0].requester_name \
            , 'assignment_group': requester_tasks.iloc[0].assignment_group \
            , 'group_email': group_email \
            , 'escalation_email': escalation_email \
            , 'today_date': today_date
            , 'open_queue_size': queue_size
            , 'requester_queue_size': len(requester_tasks.index) \
            , 'tasks': requester_tasks
            , 'task_card_length' : '840'
            , 'timeline_line_length': '50'
        }

        # applies the template's logic and data to create the HTML for the email body
        raw_html = template.render(data)

        # Uncomment three below to create a HTML file of the email for debugging purposes. Open HTML file with browser.
        out_file = 'emailer_output.html'#Name of HTML file to be written
        out_file_path = Path.cwd() / 'outputs' / out_file
        out_file_path.write_text(raw_html)

        return raw_html
    except:
        raise CreateEmailBodyError()