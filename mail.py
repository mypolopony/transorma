from apiclient.discovery import build
from googleapiclient import errors
from httplib2 import Http
from oauth2client import file, client, tools
from google_auth_oauthlib.flow import InstalledAppFlow
import _pickle as pickle
import os

FORCE = False
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Template:
# ('Susanne Choe <susannechoemd@gmail.com>', [{'internalDate': '1525828495000', 'historyId': '10152591', 'id': '1634277434045126', 'snippet': 'Hello, I have a patient who is relocating to Colorado and is seeking a both therapist and psychiatrist in Fort Collins, Denver, or Boulder. She is a bright, insightful 34yo single female with a', 'sizeEstimate': 7680, 'threadId': '1634277434045126', 'labelIds': ['UNREAD', 'CATEGORY_FORUMS', 'INBOX'], 'payload': {'mimeType': 'multipart/alternative', 'headers': [{'name': 'From', 'value': 'Susanne Choe <susannechoemd@gmail.com>'}]}}])

def ListMessagesWithLabels(service, user_id, label_ids=[]):
    '''List all Messages of the user's mailbox with label_ids applied.

    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    label_ids: Only return Messages with these labelIds applied.

    Returns:
    List of Messages that have all required Labels applied. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate id to get the details of a Message.
    '''

    try:
        response = service.users().messages().list(userId=user_id,
                                                   labelIds=label_ids).execute()
        messages = list()
        batch = service.new_batch_http_request()

        if 'messages' in response:
            for msg in response['messages']:
                batch.add(service.users().messages().get(userId=user_id, id=msg['id'], format='metadata', metadataHeaders=['From']), callback=lambda id,resp,e: messages.append(resp))

            batch.execute()

            while 'nextPageToken' in response:
                batch = service.new_batch_http_request()
                page_token = response['nextPageToken']
                response = service.users().messages().list(userId=user_id,
                                                         labelIds=label_ids,
                                                         pageToken=page_token).execute()
                for msg in response['messages']:
                    batch.add(service.users().messages().get(userId=user_id, id=msg['id'], format='metadata', metadataHeaders=['From']), callback=lambda id,resp,e: messages.append(resp))
                
                batch.execute()

            return messages
    except errors.HttpError as error:
        print('An error occurred: {}'.format(error))


if __name__ in ('__main__', '__console__'):
    fname = 'unread.dat'

    if not os.path.exists(fname) or FORCE:
        print('Downloading data')
    
        uid = 'mypolopony@gmail.com'

        # Setup the Gmail API (user input)
        flow = InstalledAppFlow.from_client_secrets_file('client_secret.json',scopes=SCOPES)
        creds = flow.run_console()

        # The service
        service = build('gmail', 'v1', credentials=creds)

        # Request
        labels = ['UNREAD']
        
        # print('Searching for messages marked: {}'.format(labels))
        messages = ListMessagesWithLabels(service, uid, label_ids=labels)
        # print('{} messages found'.format(len(messages)))
        # print('Sample: {}'.format(messages[0]))

        # Save
        print('Saving to: {}'.format(fname))
        pickle.dump(messages,open(fname,'wb'))

    else:
        print('Data Found')
        messages = pickle.load(open(fname,'rb'))

    finaldata = {k: list() for k in list(set([m['payload']['headers'][0]['value'] for m in messages]))}
    for datum in messages:
        sender = datum['payload']['headers'][0]['value']
        finaldata[sender].append(datum)

    print('Saving')
    pickle.dump(finaldata,open('finaldata.dat', 'wb'))

    sdata = sorted(finaldata, key=lambda k: len(finaldata[k]), reverse=True)
    for k in sdata:
        try:
            print('{}\t{}'.format(k,len(finaldata[k])))
        except:
            pass