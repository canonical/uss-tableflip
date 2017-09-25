#!/usr/bin/python
# Didn't sort python3 string encoding yet
# Author Chad Smith <chad.smith@canonical.com>

"""trello-report: Query and report trello card info from your boards."""

# Requirements: pip install py-trello
# Example initial call requires key and secret from https://trello.com/app-key
# TRELLO_API_KEY='<key>' TRELLO_API_SECRET='<secret>' python tboard.py
# It will store oauth responses in in CREDS_FILE for reference next run


# Example call python /tboard.py --board-name 'Daily Cloud-init/curtin' --list-name 'Done' --label-name cloud-init

import argparse
import json
import os
try:
    from trello import TrelloClient
    from trello.util import create_oauth_token
except ImportError:
    raise RuntimeError(
        'Missing py-trello package:\n'
        'sudo apt install python-pip; sudo pip install py-trello')

# Add this prefix card comment to set the publishable markdown content,
# If no doc-comment present, we'll try to use card description or title(name).
COMMENT_DOC_PREFIX = 'DOC:'

CREDS_FILE = '.trello-creds'  # Where we cache our oauth creds


def get_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--list-boards', default=False, action='store_true',
                        dest='list_boards', help='List board details')
    parser.add_argument('--list-name', dest='list_name',
                        help='Limit cards reported to a specific named list')
    parser.add_argument('--board-name', dest='board_name',
                        help='Limit cards reported to a specific board')
    parser.add_argument('--label-name', '-l', dest='label_name',
                        help='Only cards with specific label will be reported')
    parser.add_argument('--doc', '-d', action='store_true', default=False,
                        help='Only print the documentation lines for cards.'
                        ' Default behavior is <linked_bugs>: <doc:_comment>')
    return parser

    

def format_board_content(board):
    return board.name

CARD_TEMPLATE = """
------------------
Name: {name}
Labels: {labels}
Doc:
{doc}
Description:
{desc}

URL: {url}

"""

def format_card_content(card, docs_only=False):
    bug_prefix = ''
    for attachment in card.fetch_attachments(force=True):
        if '+bug' in attachment['url']:
            bug_id = attachment['url'].split('bug/')[-1]
            if bug_prefix:
                bug_prefix += '/'  # Separator between bugs
            bug_prefix += '[LP: #{0}]({1})'.format(bug_id, attachment['url'])
    if bug_prefix:
        bug_prefix += ': '
    doc = ''
    for comment in card.fetch_comments(force=True):
        comment_text = comment.get('data', {}).get('text', '')
        if comment_text.startswith(COMMENT_DOC_PREFIX):
            doc = comment_text.replace(COMMENT_DOC_PREFIX, '')
            break
    if any([bug_prefix, doc]):
        doc = '- {}{}'.format(bug_prefix, doc)
    if docs_only:
        return doc
    if not doc:
        doc = card.desc
    try:
        return CARD_TEMPLATE.format(**{
            'name': card.name, 'labels': card.list_labels,
            'desc': card.desc, 'doc': doc, 'url': card.url})
    except UnicodeEncodeError:
        return 'Error: Could not encode content for card: {}'.format(card.url)


def label_matches(label, card):
    '''Return True if label is unset or matches any part of card labels'''
    if not label:
        return True
    if card.list_labels:
        label_names = [l.name for l in card.list_labels]
    else:
        label_names = []
    for label_name in label_names:
        if label in label_name:
            return True
    return False


def get_trello_client():
    '''Returns configured Trello client.
    
    Source .trello-creds if it exists. Otherwise prompt for required env vars.
    '''
    if os.path.exists(CREDS_FILE):
        with open(CREDS_FILE) as stream:
            creds = json.loads(stream.read())
    else:
        if not all([
            os.environ.get('TRELLO_API_KEY'),
            os.environ.get('TRELLO_API_SECRET')]):
            raise RuntimeError(
                'Missing either TRELLO_API_KEY or TRELLO_API_SECRET for'
                ' initialization.\nThey can both be found at'
                ' https://trello.com/app-key')
        creds = {'api_key': os.environ.get('TRELLO_API_KEY'),
                 'api_secret': os.environ.get('TRELLO_API_SECRET')}

    if not creds.get('token'):
        access_token = create_oauth_token(key=creds['api_key'], secret=creds['api_secret'], name='Trello Board Script')
        creds['token'] = access_token['oauth_token']
        creds['token_secret'] = access_token['oauth_token_secret']
        # Save credentials for next run
        with open(CREDS_FILE, 'w') as stream:
            stream.write(json.dumps(creds))
    return TrelloClient(**creds)

def main():
    parser = get_parser()
    args = parser.parse_args()

    client = get_trello_client()
    boards = client.list_boards()
    for board in boards:
        if args.list_boards:
            print(format_board_content(board))
            continue
        if args.board_name and args.board_name != board.name:
            continue
        for board_list in board.list_lists():
            if args.list_name and args.list_name != board_list.name:
                continue
            for card in board_list.list_cards():
                if not label_matches(args.label_name, card):
                    continue
                content = format_card_content(card, args.doc)
                if content:
                    print(content)

if __name__ == '__main__':
    main()
