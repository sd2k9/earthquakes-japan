Earthquakes Japan @EarthquakesJA
================================

Overview
--------
Repository:  
https://github.com/sd2k9/earthquakes-japan

This is the source code serving the Twitter account
[@EarthquakesJA](https://twitter.com/EarthquakesJA)
since August 2010.  
It fetches the earthquake information for Japan from the
[JMA website](http://www.jma.go.jp/en/quake/quake_singendo_index.html)
and tweets out new entries.

Retirement & Takeover Offer
---------------------------
Running this service now for over 10 years, I plan to retire the server in
the near future.  
This will of course also mean the end of
[@EarthquakesJA](https://twitter.com/EarthquakesJA) tweets.

If you enjoy it and want the service to continue, then feel free to
fetch the source code and get it running on your server.  
If it's running stable on your own server and you would be willing to maintain
this account, then contact me.

If nobody cares enough to spend the effort, then this service
will enter it's well-earned retirement.

Setup
-----
1. Install the required modules, see weather_info_fetch.py
1. Define the twitter API key, search for "self._api = twitter.Api"
   in weather_info_fetch.py
1. Set mail addresses "MAIL_TO_ME" and "MAIL_TO_TWITTER"
   in watcher_report_output.sh
1. Adjust and install the user .crontab


Questions
---------
Just drop me a message via Github, or (as long as my server is still running)
via [eMail](https://sethdepot.org/site/RoLa.html) .
