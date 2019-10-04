Reconciliation application.

It retrieves data from MetaTrader 4 report server and compares open positions for the selected Mt4 groups against net
positions on FXCM accounts.

It's necessary to add to the standard fxcmpy library header:

from fxcmpy.fxcmpy import ServerError as ServerError
to fxcm __init__.py file to get the error

Also it's necessary to check all paths in the config.ini and config.py

Config file should be named config.ini and contain information about Mt4 report server (MySQL):

    [ReportServer]
    charset = utf8                      // optional
    use_unicode = True                  // optional
    host = 127.0.0.1
    port = 3306
    user =
    password =

And information each connection

    [live-api]
    db = dbname                            // report server database name
    upload_db = db_to_upload               // optional, if not specified data is dumped to xls
    token = fxcmtoken                      // fxcm api token
    groups = mt4_group1;mt4_group2         // mt4 group names for the net position retrieving

