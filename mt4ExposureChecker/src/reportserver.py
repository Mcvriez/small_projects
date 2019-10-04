from peewee import *


def get_trades(dbname, params):
    db = MySQLDatabase(dbname, **params)

    class BaseModel(Model):
        class Meta:
            database = db

    class Mt4Trades(BaseModel):
        close_price = FloatField(column_name='CLOSE_PRICE')
        close_time = DateTimeField(column_name='CLOSE_TIME', index=True)
        cmd = IntegerField(column_name='CMD', index=True)
        comment = CharField(column_name='COMMENT')
        commission = FloatField(column_name='COMMISSION')
        commission_agent = FloatField(column_name='COMMISSION_AGENT')
        conv_rate1 = FloatField(column_name='CONV_RATE1')
        conv_rate2 = FloatField(column_name='CONV_RATE2')
        digits = IntegerField(column_name='DIGITS')
        expiration = DateTimeField(column_name='EXPIRATION')
        gw_close_price = IntegerField(column_name='GW_CLOSE_PRICE', constraints=[SQL("DEFAULT 0")])
        gw_open_price = IntegerField(column_name='GW_OPEN_PRICE', constraints=[SQL("DEFAULT 0")])
        gw_volume = IntegerField(column_name='GW_VOLUME', constraints=[SQL("DEFAULT 0")])
        internal_id = IntegerField(column_name='INTERNAL_ID')
        login = IntegerField(column_name='LOGIN', index=True)
        magic = IntegerField(column_name='MAGIC', constraints=[SQL("DEFAULT 0")])
        margin_rate = FloatField(column_name='MARGIN_RATE')
        modify_time = DateTimeField(column_name='MODIFY_TIME')
        open_price = FloatField(column_name='OPEN_PRICE')
        open_time = DateTimeField(column_name='OPEN_TIME', index=True)
        profit = FloatField(column_name='PROFIT')
        reason = IntegerField(column_name='REASON', constraints=[SQL("DEFAULT 0")])
        sl = FloatField(column_name='SL')
        swaps = FloatField(column_name='SWAPS')
        symbol = CharField(column_name='SYMBOL')
        taxes = FloatField(column_name='TAXES')
        ticket = AutoField(column_name='TICKET')
        timestamp = IntegerField(column_name='TIMESTAMP', index=True)
        tp = FloatField(column_name='TP')
        volume = IntegerField(column_name='VOLUME')

        class Meta:
            table_name = 'mt4_trades'

    return Mt4Trades


def get_users(dbname, params):
    db = MySQLDatabase(dbname, **params)

    class BaseModel(Model):
        class Meta:
            database = db

    class Mt4Users(BaseModel):
        address = CharField(column_name='ADDRESS')
        agent_account = IntegerField(column_name='AGENT_ACCOUNT')
        api_data = TextField(column_name='API_DATA', null=True)
        balance = FloatField(column_name='BALANCE')
        city = CharField(column_name='CITY')
        comment = CharField(column_name='COMMENT')
        country = CharField(column_name='COUNTRY')
        credit = FloatField(column_name='CREDIT')
        currency = CharField(column_name='CURRENCY', constraints=[SQL("DEFAULT ''")])
        email = CharField(column_name='EMAIL')
        enable = IntegerField(column_name='ENABLE')
        enable_change_pass = IntegerField(column_name='ENABLE_CHANGE_PASS')
        enable_otp = IntegerField(column_name='ENABLE_OTP', constraints=[SQL("DEFAULT 0")])
        enable_readonly = IntegerField(column_name='ENABLE_READONLY')
        equity = FloatField(column_name='EQUITY', constraints=[SQL("DEFAULT 0")])
        group = CharField(column_name='GROUP')
        id = CharField(column_name='ID')
        interestrate = FloatField(column_name='INTERESTRATE')
        lastdate = DateTimeField(column_name='LASTDATE')
        lead_source = CharField(column_name='LEAD_SOURCE', constraints=[SQL("DEFAULT ''")])
        leverage = IntegerField(column_name='LEVERAGE')
        login = AutoField(column_name='LOGIN')
        margin = FloatField(column_name='MARGIN', constraints=[SQL("DEFAULT 0")])
        margin_free = FloatField(column_name='MARGIN_FREE', constraints=[SQL("DEFAULT 0")])
        margin_level = FloatField(column_name='MARGIN_LEVEL', constraints=[SQL("DEFAULT 0")])
        modify_time = DateTimeField(column_name='MODIFY_TIME')
        mqid = IntegerField(column_name='MQID', constraints=[SQL("DEFAULT 0")])
        name = CharField(column_name='NAME')
        password_phone = CharField(column_name='PASSWORD_PHONE')
        phone = CharField(column_name='PHONE')
        prevbalance = FloatField(column_name='PREVBALANCE')
        prevmonthbalance = FloatField(column_name='PREVMONTHBALANCE')
        regdate = DateTimeField(column_name='REGDATE')
        send_reports = IntegerField(column_name='SEND_REPORTS')
        state = CharField(column_name='STATE')
        status = CharField(column_name='STATUS')
        taxes = FloatField(column_name='TAXES')
        timestamp = IntegerField(column_name='TIMESTAMP', index=True)
        user_color = IntegerField(column_name='USER_COLOR')
        zipcode = CharField(column_name='ZIPCODE')

        class Meta:
            table_name = 'mt4_users'

    return Mt4Users