# Notes
# Outlook won't do...
#   TR heights
#   Top or bottom margin/padding (so you have to use transparent gifs to force sizing)
#   background images e.g. background=
#   Applying font-family to the body of the email doesn't work you have to apply it to the table elements
#   Set every TD's font-size: 0px because if you ever have elements on multiple lines, the Outlook webclient and iOS Gmail client defaults the height of each line to a standard font height and messes with the spacing
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from emailerException import SendSMTPEmailError

def open_smtp_connection():
    smtp = smtplib.SMTP(host='host-server', port=25)
    smtp.starttls() # enable encryption
    return smtp

def close_smtp_connection(smtp_connection):
    smtp_connection.quit()

def AddImageToEmail(asset_path, attachment_obj, asset_filename):
    # separate full file name into its type and name without the "."
    asset_type = asset_filename[asset_filename.find('.')+1:]
    asset_name = asset_filename[:asset_filename.find('.')]

    # load the image into a MIME image and attach it to the message with headers
    with open(asset_path + asset_filename, 'rb') as f:
        img = MIMEImage(f.read(), _subtype = asset_type)

    img.add_header('Content-ID', '<' + asset_name + '>')
    attachment_obj.attach(img)

def send_outlook_html_mail(smtp_obj,recipients, subject='No Subject', body='Test Email', copies=None, asset_path=''):
    """
    Send an Outlook HTML email
    :param recipients: list of recipients' email addresses (list object)
    :param subject: subject of the email
    :param body: HTML body of the email
    :param copies: list of CCs' email addresses
    :param asset_path: the path of where the images/other assets are located
    :return: None
    """

    body = body.replace('./assets/', 'cid:')
    body = body.replace('.png', '')
    body = body.replace('.gif', '')

    if len(recipients) > 0 and isinstance(recipients, list) and asset_path != '':
        # set from address
        fromAddress = 'donotreply-acebusiness@queens.org'

        # create the email object
        message = MIMEMultipart()

        # set the subject
        message['Subject'] = subject

        # set the To recipient(s)
        # currently, we think only the first To recipient receives the email
        str_to = ""
        for recipient in recipients:
            str_to += recipient + ";"

        message['To'] = str_to

        # set any CC repicient(s)
        if copies is not None:
            str_cc = ""
            for cc in copies:
                str_cc += cc + ";"

            message['CC'] = str_cc

        # Attach the images used in the HTML layout to be referenced by the body of the email
        # https://www.rgbtohex.net/
        # https://www.generateit.net/rounded-corner/

        # 0x370E001F is PR_ATTACH_CONTENT_ID
        # 0x3712001F ha something to do with setting the cid

        # ==========================================================================================
        # add assets that creates the generic card and timeline
        AddImageToEmail(asset_path, message, 'top-left.png')
        AddImageToEmail(asset_path, message, 'top-right.png')
        AddImageToEmail(asset_path, message, 'bottom-left.png')
        AddImageToEmail(asset_path, message, 'bottom-right.png')
        AddImageToEmail(asset_path, message, 'transparent.gif')
        AddImageToEmail(asset_path, message, 'timeline-background.gif')
        AddImageToEmail(asset_path, message, 'gray-bullet.gif')
        AddImageToEmail(asset_path, message, 'green-bullet.gif')
        # ==========================================================================================


        # ==========================================================================================
        # top left blue ticket status indicator
        AddImageToEmail(asset_path, message, 'top-left-dark-blue.png')
        AddImageToEmail(asset_path, message, 'top-right-dark-blue.png')
        AddImageToEmail(asset_path, message, 'bottom-left-dark-blue.png')
        AddImageToEmail(asset_path, message, 'bottom-right-dark-blue.png')
        # ==========================================================================================


        # ==========================================================================================
        # Begin queue transparent gifs
        # When the ticket status is "Open", sets the pointer position based on the ticket's place in line
        if body.find('cid:transparent_40px') > 0:
            AddImageToEmail(asset_path, message, 'transparent_40px.gif')
            AddImageToEmail(asset_path, message, 'transparent_50px.gif')

        if body.find('cid:transparent_65px') > 0:
            AddImageToEmail(asset_path, message, 'transparent_65px.gif')
            AddImageToEmail(asset_path, message, 'transparent_75px.gif')

        if body.find('cid:transparent_90px') > 0:
            AddImageToEmail(asset_path, message, 'transparent_90px.gif')
            AddImageToEmail(asset_path, message, 'transparent_100px.gif')

        if body.find('cid:transparent_125px') > 0:
            AddImageToEmail(asset_path, message, 'transparent_125px.gif')
            AddImageToEmail(asset_path, message, 'transparent_135px.gif')

        if body.find('cid:transparent_147px') > 0:
            AddImageToEmail(asset_path, message, 'transparent_147px.gif')
            AddImageToEmail(asset_path, message, 'transparent_157px.gif')

        if body.find('cid:timeline-pointer') > 0:
            AddImageToEmail(asset_path, message, 'timeline-pointer.gif')
        # ==========================================================================================


        # ==========================================================================================
        # Service Now Activty Pull Section
        if body.find('cid:top-left-dark-gray') > 0:
            AddImageToEmail(asset_path, message, 'top-left-dark-gray.png')
            AddImageToEmail(asset_path, message, 'top-right-dark-gray.png')
            AddImageToEmail(asset_path, message, 'bottom-left-dark-gray.png')
            AddImageToEmail(asset_path, message, 'bottom-right-dark-gray.png')
        # ==========================================================================================


        # ==========================================================================================
        # action icons
        if body.find('cid:red-bullet') > 0:
            AddImageToEmail(asset_path, message, 'red-bullet.gif')

        if body.find('cid:email') > 0:
            AddImageToEmail(asset_path, message, 'email.gif')

        #if body.find('cid:chat') > 0:
        #    AddImageToEmail(asset_path, message, 'chat.gif')

        if body.find('cid:escalate') > 0:
            AddImageToEmail(asset_path, message, 'escalate.gif')
        # ==========================================================================================


        # ==========================================================================================
        # avatars
        if body.find('cid:avatar-micah') > 0:
            AddImageToEmail(asset_path, message, 'avatar-micah.png')

        if body.find('cid:avatar-unassigned') > 0:
            AddImageToEmail(asset_path, message, 'avatar-unassigned.png')
        # ==========================================================================================

        # attach body to the email
        message.attach(MIMEText(body,'html', _charset='utf-8'))

        #send the email
        smtp_obj.send_message(from_addr=fromAddress, to_addrs=str_to, msg=message)

    else:
        raise SendSMTPEmailError()