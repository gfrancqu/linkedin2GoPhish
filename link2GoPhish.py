#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import string
import time
import argparse
import getpass
import requests
import urllib
import sys
import os
from gophish import Gophish
from gophish.models import Group, User


# Print a cool banner
BANNER="""

  _ _       _    ___  _____  _     _     _     
 | (_)     | |  |__ \|  __ \| |   (_)   | |    
 | |_ _ __ | | __  ) | |__) | |__  _ ___| |__  
 | | | '_ \| |/ / / /|  ___/| '_ \| / __| '_ \ 
 | | | | | |   < / /_| |    | | | | \__ \ | | |
 |_|_|_| |_|_|\_\____|_|    |_| |_|_|___/_| |_|
                                               

scrap emails from linkedin to goPhish
"""

# Handle arguments before moving on....
parser = argparse.ArgumentParser()
parser.add_argument('username', type=str, help='A valid LinkedIn username.', action='store')
parser.add_argument('company', type=str, help='Company name.', action='store')
parser.add_argument('-p', '--password', type=str, help='Specify your password on in clear-text on \
                     the command line. If not specified, will prompt and not display on screen.', action='store')
parser.add_argument('-n', '--domain', type=str, help='The domain name to add to the email addresses. default is [company].com \
                     [example: "-n uber.com" would ouput jschmoe@uber.com]', action='store')
parser.add_argument('-d', '--depth', type=int, help='Search depth. If unset, will try to grab them all.', action='store')
parser.add_argument('-s', '--sleep', type=int, help='Seconds to sleep between pages. \
                     defaults to 3.', action='store')
parser.add_argument('-f', '--format', type=int, help='Format for the email address, 1:first.last@domain, 2:f.last@domain, 3:flast@domain. Default is flast@domain', action='store')
parser.add_argument('-u', '--url', type=str, help='Host for the goPhish API', action='store')
parser.add_argument('-k', '--apikey', type=str, help='API key for the goPhish API', action='store')

args = parser.parse_args()

username = args.username
company = args.company

if args.domain:
    domain = '@' + args.domain
else:
    domain = '@' + args.company + '.com'

searchDepth = args.depth or ''
pageDelay = args.sleep or 3
password = args.password or getpass.getpass()
apiKey = args.apikey or None
host = args.url or None


# Set up some nice colors
class bcolors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'


okBox = bcolors.OKGREEN + '[+] ' + bcolors.ENDC
warnBox = bcolors.WARNING + '[!] ' + bcolors.ENDC


class EmailFormatter:
    ''' this class is used to output the email addresse with the correct format '''
    FIRSTDOTLAST = 1
    FDOTLAST = 2
    FLAST = 3

    def __init__(self, format):
        self.format = format

    def formatMail(self, first, last):
        """ return the well formatted email adresse for a given firstname and lastname """

        if self.format == EmailFormatter.FIRSTDOTLAST:
            email = '{}.{}{}'.format(first, last, domain)
        elif self.format == EmailFormatter.FDOTLAST:
            email = '{}.{}{}'.format(first[0], last, domain)
        else:
            email = '{}{}{}'.format(first[0], last, domain)

        return email


emailFormatter = EmailFormatter(args.format or EmailFormatter.FLAST)


class LinkedinUser:
    ''' this class describe a linkedin user '''
    def __init__(self, firstname, lastname, position, company):
        self.firstname = self.remove_accents(firstname.lower())
        self.lastname = self.remove_accents(lastname.lower())
        self.position = position
        self.company = company

    def remove_accents(self, s):
        """Removes common accent characters."""

        s = re.sub(r"[àáâãäå]", 'a', s)
        s = re.sub(r"[èéêë]", 'e', s)
        s = re.sub(r"[ìíîï]", 'i', s)
        s = re.sub(r"[òóôõö]", 'o', s)
        s = re.sub(r"[ùúûü]", 'u', s)
        s = re.sub(r"[ýÿ]", 'y', s)
        s = re.sub(r"[ß]", 'ss', s)
        s = re.sub(r"[ñ]", 'n', s)

        return string

    def toGophish(self):
        return self.firstname + ',' + self.lastname + ',' + self.position + ',' + self.getMail() + '\n'

    def getMail(self):
        return emailFormatter.formatMail(self.firstname, self.lastname)


def login(username, password):
    """Creates a new authenticated session.

    Note that a mobile user agent is used.
    Parsing using the desktop results proved extremely difficult, as shared connections would be returned
    in a manner that was indistinguishable from the desired targets.

    The function will check for common failure scenarios - the most common is logging in from a new location.
    Accounts using multi-factor auth are not yet supported and will produce an error
    """
    session = requests.session()
    mobileAgent = 'Mozilla/5.0 (Linux; U; Android 2.2; en-us; Droid Build/FRG22D) AppleWebKit/533.1 (KHTML, like Gecko) \
                   Version/4.0 Mobile Safari/533.1'
    session.headers.update({'User-Agent': mobileAgent})
    anonResponse = session.get('https://www.linkedin.com/')
    try:
        loginCSRF = re.findall(r'name="loginCsrfParam".*?value="(.*?)"', anonResponse.text)[0]
    except Exception as e:
        print('Having trouble with loading the page... try the command again. (%s)' % str(e))
        exit()

    authPayload = {
        'session_key': username,
        'session_password': password,
        'loginCsrfParam': loginCSRF
        }

    response = session.post('https://www.linkedin.com/uas/login-submit', data=authPayload)

    if bool(re.search('<title>*?LinkedIn*?</title>', response.text)):
        print(okBox + 'Successfully logged in.\n')
        return session
    elif '<title>Sign-In Verification</title>' in response.text:
        print(warnBox + 'LinkedIn doesn\'t like something about this login. Maybe you\'re being sneaky on a VPN or')
        print('    something. You may get an email with a verification token. You can ignore that.')
        print('    Try logging in with the same account in your browser first, then try this tool again.\n')
        exit()
    elif '<title>Sign In</title>' in response.text:
        print(warnBox + 'You\'ve been returned to the login page. Check your password and try again.\n')
        exit()
    elif '<title>Security Verification' in response.text:
        print(warnBox + 'You\'ve triggered the security verification. Please verify your login details and try again.\n')
        exit()
    else:
        print(warnBox + 'Some unknown error logging in. If this persists, please open an issue on github.\n')
        exit()


def get_company_info(name, session):
    """Scapes basic company info.

    Note that not all companies fill in this info, so exceptions are provided. The company name can be found easily
    by browsing LinkedIn in a web browser, searching for the company, and looking at the name in the address bar.
    """
    response = session.get('https://linkedin.com/company/' + name)
    try:
        foundID = re.findall(r'normalized_company:(.*?)[&,]', response.text)[0]
    except:
        print(warnBox + 'Could not find that company name. Please double-check LinkedIn and try again.')
        exit()
    try:
        foundDesc = re.findall(r'localizedName&quot;:&quot;(.*?)&quot', response.text)[0]
    except:
        foundDesc = "No info found, sorry!"
    foundName = re.findall(r'companyUniversalName.*?3D(.*?)"', response.text)[0]
    foundStaff = re.findall(r'staffCount&quot;:(.*?),', response.text)[0]
    print('          Found: ' + foundName)
    print('          ID:    ' + foundID)
    print('          Desc:  ' + foundDesc)
    print('          Staff: ' + str(foundStaff))
    print('\n' + okBox + 'Hopefully that\'s the right ' + name + '! If not, double-check LinkedIn and try again.\n')
    return(foundID, int(foundStaff))


def set_search_csrf(session):
    """Extract the required CSRF token.
    
    LinkedIn's search function requires a CSRF token equal to the JSESSIONID.
    """
    session.headers.update({'Csrf-Token': session.cookies['JSESSIONID'].replace('"', '')})
    return session


def set_loops(staffCount):
    """Defines total hits to the search API.

    Sets a total amount of loops based on either the number of staff discovered in the get_company_info function
    or the search depth argument provided by the user. LinkedIn currently restricts these searches to a limit of 1000.
    I have not implemented that limit in this application, just in case they change their mind. Either way, this
    application will stop searching when no more results are provided.
    """
    global searchDepth
    print(okBox + 'Company has ' + str(staffCount) + ' profiles to check. Some may be anonymous.')
    if staffCount > 1000:
        print(warnBox + 'Note: LinkedIn limits us to a maximum of 1000 results!')
    loops = int((staffCount / 25) + 1)
    if searchDepth != '' and searchDepth < loops:
        print(warnBox + 'You defined a low custom search depth, so we might not get them all.')
    else:
        print(okBox + 'Setting search to ' + str(loops) + ' loops of 25 results each.')
        searchDepth = loops
    print('\n\n')
    return searchDepth


def get_results(session, companyID, page):
    """Scrapes raw data for processing.

    The URL below is what the LinkedIn mobile application queries when manually scrolling through search results.
    The mobile app defaults to using a 'count' of 10, but testing shows that 25 is allowed. This behavior will appear
    to the web server as someone scrolling quickly through all available results.
    """
    url = 'https://linkedin.com'
    url += '/voyager/api/search/hits?count=25&guides=facetCurrentCompany-%3E'
    url += companyID
    url += '&origin=OTHER&q=guided&start='
    url += str(page*25)
    try:
        result = session.get(url)
    except Exception as e:
        choice = input("{} Connection Error ({})! Continue ? [Y/N]".format(warnBox, str(e)))
        if choice is "Y":
            return get_results(session, companyID, page)
        else:
            exit()

    return result.text


def scrape_info(session, companyID, staffCount, company):
    """Uses regexes to extract employee names.

    The data returned is similar to JSON, but not always formatted properly. The regex queries below will build
    individual lists of first and last names. Every search tested returns an even number of each, so we can safely
    match the two lists together to get full names.

    This function will stop searching if a loop returns 0 new names.
    """
    userList = []
    print(okBox + 'Starting search....\n')
    set_loops(staffCount)
    for page in range(0, searchDepth):
        newUsers = 0
        print(okBox + 'OK, looking for results on loop number ' + str(page+1) + '...        ')
        result = get_results(session, companyID, page)
        firstName = re.findall(r'"firstName":"(.*?)"', result)
        lastName = re.findall(r'"lastName":"(.*?)"', result)
        position = re.findall(r'"text":"(.*?)"', result)
        if len(firstName) == 0 and len(lastName) == 0:
            print(okBox + 'We have hit the end of the road! Moving on...')
            break
        for first,last,pos in zip(firstName,lastName,position):
            if len(first) == 0 or len(last) == 0:
                print("{} weird length for first and last names : {} {}".format(warnBox, first, last)) 
            else:
                userList.append(LinkedinUser(first, last, pos, company))
                newUsers +=1
        print('    ' + okBox + 'Added ' + str(newUsers) + ' new names. Running total: '\
                         + str(len(userList)) + '              \r')
        time.sleep(pageDelay)
    return userList


def write_files(company, list):
    """Writes data to various formatted output files.

    After scraping and processing is complete, this function formates the raw names into common username formats
    and writes them into a directory called 'li2u-output'.

    See in-line comments for decisions made on handling special cases.
    """
    dir = 'link2gophish-output'
    if not os.path.exists(dir):
            os.makedirs(dir)
    gophish = open(dir + '/' + company + '-gophish.csv', 'w')

    for u in list:
        gophish.write(u.toGophish())
    gophish.close()


def send_to_gophish(userList):
    ''' create a group with the forged email addresses into gophish '''
    print(okBox + 'Connecting to the goPhish API')
    api = Gophish(apiKey, host=host, verify=False)
    targets = [
        User(first_name=u.firstname, last_name=u.lastname, email=u.getMail(), position=u.position)
        for u in userList
    ]
    group = Group(name='l2gp - ' + company, targets=targets)
    api.groups.post(group)
    print(okBox + 'Group created !')


def main():
    print(BANNER)
    session = login(username, password)
    session = set_search_csrf(session)
    companyID, staffCount = get_company_info(company, session)
    foundUsers = scrape_info(session, companyID, staffCount, company)
    write_files(company, foundUsers)
    if host is not None and apiKey is not None:
        send_to_gophish(foundUsers)
    print('\n\n' + okBox + 'All done! Check out in link2gophish-output.')


if __name__ == "__main__":
    main()
