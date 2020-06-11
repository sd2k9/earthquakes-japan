#!/usr/bin/env python
#
#    Fetch Japan Earthquake Information and put to Twitter
#    Copyright (C) 2010,2011,2013,2018 Robert Lange <sd2k9@sethdepot.org>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3 of the License.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# Infos: Local Earthquake Information (target 2) is commented off,
#        because it would provide too much information
#

# *** Import modules
# Fetch the URL Head
import httplib
# Fetch the real web page
import urllib2
# Regular Expression Service
import re
# Time conversion
from datetime import datetime
# Data storage
import pickle
# To control output level easily
# from __future__ import print_function
import logging
# Argument parser
import optparse
# To be able to catch socket.(gai)error
import socket
# Twitter interface - import after Global options, in case debug is not set



# *** Global settings
opts = { # Earthquake and Seismic Intensity Information
         'target1_server': "www.jma.go.jp",
         'target1_file': "/en/quake/quake_singendo_index.html",
         # Local Earthquake Information
         'target2_server': "www.jma.go.jp",
         'target2_file': "/en/quake/quake_local_index.html",
         # When set to true, print debug information and don't tweet
         'debug': False
         # 'debug': True
       }

state_filename = "weather_info_fetch.state"

# Provide wprint and iprint
iprint = logging.info
wprint = logging.warning
eprint = logging.error

# Twitter interface - import only when debug is not set
if not opts['debug']:
    import twitter



# ********************************************************************************

# *** Twitter messager class
class twittermsg:
    """ Twitter the given string to the embedded account details"""

    # Variables
    _api = ""

    def __init__(self):     # C'tor
        # Changes: Username/password: Consumer Data, not account
        # access_*: Fetch from tool python-twitter/get_access_token.py
        if not opts['debug']:
            self._api = twitter.Api(consumer_key='FILLME',
                       consumer_secret='FILLME',
                       access_token_key='FILLME',
                      access_token_secret='FILLME',
                                )
        # print self._api.VerifyCredentials()

    def doit(self, msg):   # Twitter the message
        # Debug
        if opts['debug']:
            print "Would tweet: " + msg
        else:
            self._api.PostUpdates(msg)

    def finish(self):      # Cleanup
        if not opts['debug']:
            self._api.ClearCredentials()


# ********************************************************************************

# *** Build an request&check class
class CheckForChange:
    """Checks whether a web location has changed and retrieves then changes"""

    """Returns true when change must be fetched, false when no change"""
    # Variables
    _server = ""
    _file   = ""
    # Store last requested time, for comparision - zero for first run
    _lasttime = ""
    # Store the values from last run
    _lastval = ""

    # Init Functions
    def __init__(self, server, file):       # Initialising function
        self._server = server
        self._file = file

    # Check for update of the web site
    def check_update(self):
        # Variables
        lastmod = 0
        lastmod_dt = 0
        prevmod_dt = 0

        # Code
        iprint("Checking update for " + self._server + self._file)
        conn = httplib.HTTPConnection(self._server)
        conn.request("HEAD", self._file)
        res = conn.getresponse()
        iprint("   " + str(res.status) + " " + res.reason)
        lastmod = res.getheader("last-modified")
        iprint("      Last Header:" + self._lasttime)
        # Convert to datetime object
        # Format:     Wed, 11 Aug 2010 05:25:38 GMT - stripping Time Zone
        lastmod = lastmod[:-4]
        iprint("   Current Header:" + lastmod)
        #        dbg = datetime.now()
        #        print dbg.strftime("%a, %d %b %Y %H:%M:%S")
        if self._lasttime is "":    # First run is always new
            self._lasttime = lastmod
            return True    # Change occured
        else:   # Compare and decide
            prevmod_dt = datetime.strptime(self._lasttime,
                                           "%a, %d %b %Y %H:%M:%S")
            lastmod_dt = datetime.strptime(lastmod, "%a, %d %b %Y %H:%M:%S")
            if prevmod_dt < lastmod_dt:   # Yes, and also update
                self._lasttime = lastmod
                return True    # Change occured
            else:
                return False   # Identical

    # Retrieve Change function
    # Return False: Fail
    #        True: OK, no change
    #         Everything else: Newly to report data
    def get_change(self):
        # Vars
        # Web page
        page = ""
        # Urllib response
        response = ""
        # RegExp matchers
        re_line = re.compile('<[tT][rR]>.+M\d.+</[tT][rR]>')
        # Old Template:      <tr><td nowrap><a href=./20100810212809484-102124.html>21:28 JST 10 Aug 2010  </a></td><td nowrap>21:24 JST 10 Aug 2010</td><td>Ehime-ken Nan-yo</td><td nowrap>M4.3</td><td nowrap>3</td></tr>
        # re_data = re.compile('<[tT][rR]><[tT][dD].*><[aA]\s+[hH][rR][eE][fF]=(.+)>(.+)</[aA]></[tT][dD]><[tT][dD].*>(.+)</[tT][dD]><[tT][dD].*>(.+)</[tT][dD]><[tT][dD].*>(M[\d\.]+)</[tT][dD]><[tT][dD].*>(.{1,3})</[tT][dD]></[tT][rR]>')
        # New Template 2018: <tr><td nowrap><a href=./20180324164926393-25014523.html>01:45 JST 25 Mar 2018</a></td><td nowrap>Akita-ken Nairiku-nambu</td><td>M1.2</td><td nowrap style="text-align:center">1</td><td nowrap>01:49 JST 25 Mar 2018</td></tr>
        #                    <tr><td nowrap><a href=./20180413190444393-14040010.html>04:00 JST 14 Apr 2018</a></td><td nowrap>Nemuro-hanto Nanto-oki</td><td>M5.4</td> <td nowrap style="text-align:center">5 Lower</td><td nowrap>04:04 JST 14 Apr 2018</td></tr>
        re_data = re.compile('<tr><td.*><a\s+href=(.+)>(.+)</a></td><td.*>(.+)</td><td.*>(M[\d\.]+)</td><td.*>\d\s*\w*</td><td.*>(.+)</td></tr>', re.IGNORECASE)
        # Template Normal:  07:58 JST 18 Jun 2018
        # Template Special: 07:58 JST 18 Jun 2018(2nd)
        re_date_strip = re.compile("^(\d{1,2}:\d\d JST \d{1,2} \w+ \d{4})")
        # Isolated matches
        found = 0
        data = 0
        ddict = 0
        ddictlist = []
        ddretlist = []
        # Change detected
        change = False
        # Change times
        lastmod_dt = 0
        prevmod_dt = 0

        # Get page content
        # Get a file-like object for the Python Web site's home page.
        response = urllib2.urlopen( "http://" + self._server + self._file)
        # Read Data
        page = response.read()

        # Get the relevant lines - absolutely simple approach is to look for "M\d"
        found = re_line.findall(page)
        #print found
        if not found:
            iprint("No matches found in page - it seems it's all empty (or something is wrong!)")
            return True
        # Split and extract information
        for schl in found:
            # print schl
            # Debug
            if opts['debug']:
                print("Debug: Data before match=", schl)
            data = re_data.match(schl)
            if not data:
                wprint("No extraction from matches possible - something is wrong!")
                return False
            # print "Data: ", data.groups()
            # Need to filter out appended non-date text
            date_stripped = re_date_strip.match(data.group(2))
            if not date_stripped:
                wprint("No date stripping possible - something is wrong!")
                return False
            date_stripped = date_stripped.group(1)
            # Get interesting data, put to dictionary
            ddict= dict(url = data.group(1),   # URL
                        date = date_stripped,  # Occurance Date
                        place = data.group(3), # Occurance Place
                        mag = data.group(4)   # Magnitude
                        )
            ddictlist.append(ddict)

        iprint( "      Last Values:" + str(self._lastval))
        iprint( "   Current Values:" + str(ddictlist))
        if (self._lastval is "") or (len(self._lastval) is 0):
            # First run or empty list is always new
            self._lastval = ddictlist
            return ddictlist   # Change occured, return all
        else:   # Compare and decide - It's true when first entry is newer
            prevmod_dt = datetime.strptime(self._lastval[0]['date'],
                                           "%H:%M JST %d %b %Y")
            lastmod_dt = datetime.strptime(ddictlist[0]['date'], "%H:%M JST %d %b %Y")
            if prevmod_dt < lastmod_dt:   # Yes, and also update
                self._lastval = ddictlist
                change = True    # Change occured
            else:
                change = False  # Identical, no change detected

        if change is False:
            iprint("No change, done")
            return True
        # else: Need to compute difference
        iprint("Computing differences")
        # Easy: just look at the date and provide dates which are
        #       not yet in oldval
        # prevmod=dt is still valid
        for schl in ddictlist:
            lastmod_dt = datetime.strptime(schl['date'],
                                           "%H:%M JST %d %b %Y")
            if lastmod_dt > prevmod_dt:   # More current value
                ddretlist.append(schl)

        # now return updated list - but reverse it before to right order
        if ddretlist:
            ddretlist.reverse()
        return ddretlist

    # Report the changes, Format is list of dict:
    #                   url = data.group(1),   # URL
    #                   date = data.group(3),  # Occurance Date
    #                   place = data.group(4), # Occurance Place
    #                   mag = data.group(5)   # Magnitude
    def report_changes(self, list):
        # Vars
        msg = ""
        twit = ""
        # Remove url name from url
        filestrip = self._file[1:self._file.rfind("/")] + "/"
        iprint(filestrip)
        iprint("")
        iprint("New Earthquake information:")
        twit = twittermsg()       # Create new object
        for schl in list:
            # python 2.6+ Syntax
            #            msg = ('{0}: {1} earthquake in {2}: {3}'.format(schl['date'],
            #                    schl['mag'], schl['place'],
            #                    "http://" + self._server + "/" + filestrip + schl['url'] ))
            # python 2.5 Syntax
            msg = schl['date'] + ": " + schl['mag'] + " earthquake in " + \
        	    schl['place'] + ": " + \
                    "http://" + self._server + "/" + filestrip + schl['url']
            iprint(msg)
            # Do Reporting via twitter
            twit.doit(msg)
            # Debug: from os import system
            # system( "xmessage " + msg)
        iprint("Twitter update done")
        twit.finish()    # Cleanup




# ********************************************************************************

# *** Main Program
def main():

    # Variables
    ret = False     # Return value


    # Command line parsing: QUIET option
    parser = optparse.OptionParser()
    parser.add_option('--quiet', '-q', dest='QUIET', action='store_true',
                        help='Quiet Output')
    (options, args) = parser.parse_args()

    # Setup logging: Show only from warnings when being QUIET
    logging.basicConfig(level=logging.WARNING if options.QUIET else logging.INFO,
                    format="%(message)s")

    # Code
    # Make objects
    quakes = [ CheckForChange(opts['target1_server'], opts['target1_file']) ]
              # ,
              # CheckForChange(opts['target2_server'], opts['target2_file']) ]

    # Load old state
    try:
        f = open(state_filename, 'rb')
        data = pickle.load(f)
        for it in quakes:
            it._lasttime = data.pop(0)
            it._lastval = data.pop(0)
        f.close()
    except IOError:
            iprint("State file " + state_filename + "not found; continuing new")


    # Check for change
    try: # Catch all errors for inspection
      for it in quakes:
        if it.check_update():
            iprint("Update occured")
            ret = it.get_change()
            if ret is False: # Something went wrong
                wprint("Error in parsing the update - Exiting")
                return False
            if ret is True: # No change
                iprint("Still the same")
            else:  # Need to report change
                # And now report the changes in user-readbale format
                it.report_changes(ret)

    except socket.gaierror, detail:
        # Error: -3, 'Temporary failure in name resolution' can be ignored
        # if detail[0].error == -3:
        if detail[0] == -3:   #???
            iprint("Got an Temporary failure in name resolution error - ignoring and exiting")
            return 1
        # Error: -2, 'Name or service not known' can be ignored
        # if detail[0].error == -2:
        elif detail[0] == -2:   #???
            iprint("Got an Name or service not known error - ignoring and exiting")
            return 1
        else:
            eprint("Error: Unknown socket.gaierror flew by!")
            raise
    except urllib2.URLError, detail:
        # Error: -2, 'Name or service not known' can be ignored
        # if detail[0].error == -2:
        if detail[0] == -2:   #???
            iprint("Got an Name or service not known error - ignoring and exiting")
            return 1
        else:
            eprint("Error: Unknown socket.gaierror flew by!")
            raise
    except socket.error, detail:
        # Error: 110, 'Connection timed out' can be ignored
        if detail[0] == 110:
            iprint("Got an Connection timed out - ignoring and exiting")
            return 1
        else:
            eprint("Error: Unknown socket.error flew by!")
            raise
    except httplib.BadStatusLine, detail:
        # Error can be ignored - I hope
        iprint("Got an Bad Status Line - ignoring and exiting")
        return 1
    except:
        eprint("Error: Exception flew by!")
        raise

    # Save new state
    f = open(state_filename, 'wb')
    data = [];
    for it in quakes:
        data.append(it._lasttime)
        data.append(it._lastval)
    pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
    f.close()


# *** Call Main program
if __name__ == "__main__":
    main()
