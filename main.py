import imaplib
import email
import json
import re
from datetime import datetime
import datetime as dt

import os
import oauth2client
from oauth2client import client, tools, file
import httplib2
from apiclient import errors, discovery
import mimetypes
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64

from person import Person

SCOPES = 'https://www.googleapis.com/auth/gmail.send'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Send Email'

CLIENT_INFO_PATH = './Credentials.json'

internet_bill = 112
rent = 1975
DAY_CYCLE = 1


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-email-send.json')
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def send_message(sender, to, subject, msgHtml, msgPlain, attachmentFile=None):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    if attachmentFile:
        message1 = create_message_with_attachment(sender, to, subject, msgHtml, msgPlain, attachmentFile)
    else:
        message1 = create_message_html(sender, to, subject, msgHtml, msgPlain)
    result = send_message_internal(service, "me", message1)
    return result


def send_message_internal(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)
        return "Error"
    return "OK"


def create_message_html(sender, to, subject, msgHtml, msgPlain):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg.attach(MIMEText(msgPlain, 'plain'))
    msg.attach(MIMEText(msgHtml, 'html'))
    msg_string = str.encode(msg.as_string())
    return {'raw': base64.urlsafe_b64encode(msg_string).decode()}


def create_message_with_attachment(
    sender, to, subject, msgHtml, msgPlain, attachmentFile):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      msgHtml: Html message to be sent
      msgPlain: Alternative plain text message for older email clients
      attachmentFile: The path to the file to be attached.

    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEMultipart('mixed')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    message_a = MIMEMultipart('alternative')
    message_r = MIMEMultipart('related')

    message_r.attach(MIMEText(msgHtml, 'html'))
    message_a.attach(MIMEText(msgPlain, 'plain'))
    message_a.attach(message_r)

    message.attach(message_a)

    print("create_message_with_attachment: file: %s" % attachmentFile)
    content_type, encoding = mimetypes.guess_type(attachmentFile)

    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    if main_type == 'text':
        fp = open(attachmentFile, 'rb')
        msg = MIMEText(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'image':
        fp = open(attachmentFile, 'rb')
        msg = MIMEImage(fp.read(), _subtype=sub_type)
        fp.close()
    elif main_type == 'audio':
        fp = open(attachmentFile, 'rb')
        msg = MIMEAudio(fp.read(), _subtype=sub_type)
        fp.close()
    else:
        fp = open(attachmentFile, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()
    filename = os.path.basename(attachmentFile)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)

    return {'raw': base64.urlsafe_b64encode(message.as_string())}


def read_hydro(mail_object):
    """ TODO change to googleAPI using oath """
    """Reads mail from IMAP server"""
    # Result is 'OK" or 'NO' , Searches # of mail.
    result, data = mail_object.search(None, '(SUBJECT "Manitoba Hydro Online Account - New Online Bill")')
    ids = data[0]
    id_list = ids.split()
    latest_email = id_list[-1]
    result, data = mail_object.fetch(latest_email, '(RFC822)')  # Fetch the latest email

    raw_email = data[0][1]

    # Formats mail in byte format to email object to string
    email_message = email.message_from_bytes(raw_email).as_string()

    amount_word_index = email_message.find("Amount due:")
    amount_range = email_message[amount_word_index: amount_word_index + 25]
    amount_string = re.findall('\d+\.\d+', amount_range)
    if not amount_string:
        amount_string = re.findall('\d+', amount_range)
    amount = float(amount_string[0])

    return amount


def read_water(mail_object):
    """ TODO change to googleAPI using oath """
    # Result is 'OK" or 'NO' , Searches # of mail.
    result, data = mail_object.search(None, '(SUBJECT "MyUtilityBill - New Bill Ready")')
    ids = data[0]
    id_list = ids.split()
    latest_email = id_list[-1]
    result, data = mail_object.fetch(latest_email, '(RFC822)')  # Fetch the latest email

    raw_email = data[0][1]

    # Formats mail in byte format to email object
    email_message = email.message_from_bytes(raw_email)

    email_message = email_message.get_payload(decode=True)  # Decodes base64 encoding of content to byte
    email_message = email_message.decode("utf-8")  # Decodes byte using utf-8 to string

    date_word_index = email_message.find("Due date:")
    date_range = email_message[date_word_index:date_word_index + 75]
    date = re.search(r'\w{3,9}?\s\d{1,2}?,\s\d{4}?', date_range)[0]
    new_date = datetime.strptime(date, "%B %d, %Y")

    if datetime.now() > new_date:
        amount = 0
    else:
        amount_word_index = email_message.find("Amount due:")
        amount_range = email_message[amount_word_index: amount_word_index + 100]
        amount_string = re.findall('\d+\.\d+', amount_range)
        if not amount_string:
            amount_string = re.findall('\d+', amount_range)
        amount = float(amount_string[0])

    return amount


def read_groceries(mail_object, spenders_list):
    """ TODO change to googleAPI using oath """
    grocery_total = 0

    for spender in spenders_list:
        # result, data = mail_object.search(None, '( SINCE ' + last_month_25() + ' FROM "' + spender.email + '")')
        result, data = mail_object.search(None, 'SINCE ' + latest_date(DAY_CYCLE) + ' FROM "' + spender.email + '"')
        ids = data[0]
        id_list = ids.split()   # list of ids of mail satisfying the condition
        for id_of_mail in id_list:
            result, data = mail_object.fetch(id_of_mail, '(RFC822)')
            raw_email = data[0][1]

            # Formats mail in byte format to email object to string
            email_message = email.message_from_bytes(raw_email).as_string()

            amount_start_index = email_message.find("$")
            if amount_start_index is not -1:
                amount_range = email_message[amount_start_index: amount_start_index + 8]
                amount_string = re.findall('\d+\.\d+', amount_range)
                if not amount_string:
                    amount_string = re.findall('\d+', amount_range)
                amount = float(amount_string[0])
            else:
                amount = 0

            spender.amount_contributed += amount
            grocery_total += amount

    return grocery_total


def latest_date(day):
    """Returns date of the latest {day} in a dd-mmm-yyyy format. If today's day is the same as {day}, return today's date"""
    today = dt.date.today()
    if today.day < day:
        first_of_this_month = today.replace(day=1)
        last_month = first_of_this_month - dt.timedelta(days=1)
        latest_month_day_string = last_month.replace(day=day).strftime('%d-%b-%Y')
    else:
        latest_month_day_string = today.replace(day=day).strftime('%d-%b-%Y')
    return latest_month_day_string


def mail_content_plain(subject, utilities):
    """Defines the message content for the email"""
    msg = "Greetings! It's that time of the month to pay your bills, " + subject.name + \
        "\n \n You better pay up ASAP! " + \
        "\n Here's the rundown:" + \
        "\n Hydro Bill: " + str(utilities[0]) + \
        "\n Groceries: " + str(utilities[3]) + \
        "\n Rent: " + str(rent) + \
        "\n Water Bill: " + str(utilities[1]) + \
        "\n Internet Bill: " + str(utilities[2]) + \
        ("\n \n You have contributed: " + str(subject.amount_contributed) if subject.amount_contributed > 0 else "") + \
        "\n Your total contribution will be: " + str(subject.amount_owed) + \
        ("\n\nLooks like you paid more than you owe! Let me know about it!" if subject.amount_owed < 0 else "") + \
        "\nQuestions or Concerns? Let me know!"
    return msg


def mail_content_html(subject, utilities):
    """Defines the message content for the email"""
    msg = "Greetings! It's that time of the month to pay your bills, " + subject.name + \
        "<br> <br> You better pay up <u><b>ASAP!</b></u> " + \
        "<br> Here's the rundown:" + \
        "<br> Hydro Bill: " + str(utilities[0]) + \
        "<br> Groceries: " + str(utilities[3]) + \
        "<br> Rent: " + str(rent) + \
        "<br> Water Bill: " + str(utilities[1]) + \
        "<br> Internet Bill: " + str(utilities[2]) + \
        ("<br> <br> You have contributed: " + str(subject.amount_contributed) if subject.amount_contributed > 0 else "") + \
        "<br> Your total contribution will be: " + str(subject.amount_owed) + \
        ("<br><br>Looks like you paid more than you owe! Let me know about it!" if subject.amount_owed < 0 else "") + \
        "<br>Questions or Concerns? Let me know!"
    return msg


def import_json_cred(path):
    with open(path) as json_file:
        data = json.load(json_file)
    return data


def init_person_list(person_list, credentials_json):
    """ Stores the recipient object to the global recipient list. """
    for recipient, recipient_email in credentials_json['recipients'].items():
        person_list.append(Person(recipient, recipient_email))


def establish_constants(person_list):
    """ Modifies amount due and amount contributed for specific instance """

    person_list[3].amount_owed += 500  # this person owes me 500

    person_list[1].amount_contributed += internet_bill  # this person paid the internet


def main():
    client_basic_info = import_json_cred(CLIENT_INFO_PATH)
    list_of_people = list()
    init_person_list(list_of_people, client_basic_info)

    mail = imaplib.IMAP4_SSL(client_basic_info['imap_server']['address'])
    mail.login(client_basic_info['sender']['email'], client_basic_info['sender']['password'])
    mail.select()

    groceries = read_groceries(mail, list_of_people)

    electricity_bill = read_hydro(mail)
    water_bill = read_water(mail)

    utilities_list = [electricity_bill, water_bill, internet_bill, groceries, rent]

    print("The hydro bill is: " + str(utilities_list[0]))
    print("The water bill is: " + str(utilities_list[1]))
    print("The groceries costs: " + str(utilities_list[3]))
    print("The internet bill is: " + str(utilities_list[2]))
    print("The rent is: " + str(utilities_list[4]))
    print("The total bill is: " + str(sum(utilities_list)))

    normal_bill = sum(utilities_list)/4

    establish_constants(list_of_people)

    for person in list_of_people:
        person.amount_owed += normal_bill - person.amount_contributed

    for person in list_of_people:
        print(person.name + "'s Bill is: " + str(person.amount_owed))
        print("Contribution is: " + str(person.amount_contributed))

    email_check = input('Ready to send the email? [y]/[n]')

    if email_check is 'y':
        sender = client_basic_info['sender']['email']
        subject = "BILL TIME!"
        for recipient in list_of_people:
            to = recipient.email
            html_msg = mail_content_html(recipient, utilities_list)
            plain_msg = mail_content_plain(recipient, utilities_list)
            send_message(sender, to, subject, html_msg, plain_msg)
    else:
        print("Alright, have a nice day!")


if __name__ == '__main__':
    main()
