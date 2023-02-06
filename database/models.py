import peewee as pw

from config_data import config

db = pw.SqliteDatabase(config.BOT_DATABASE_NAME)


class BaseModel(pw.Model):
    '''Базовая модель класса'''
    class Meta:
        database = db


class Hotel(BaseModel):
    '''Модель класса для хранения отеля в базе.'''
    id = pw.IntegerField(unique=True, index=True)
    name = pw.CharField(max_length=50, null=False)
    address = pw.CharField(max_length=150, null=False)
    distance = pw.FloatField(null=False)

    class Meta:
        order_by = 'id'


class Request(BaseModel):
    '''Модель класса для хранения запроса пользователя в базе.'''
    created_at = pw.DateTimeField(null=False)
    user = pw.CharField(max_length=30, null=False)
    command = pw.CharField(max_length=20, null=False)
    city = pw.CharField(max_length=20, null=False)
    start_date = pw.DateField(null=False)
    end_date = pw.DateField(null=False)
    hotels_count = pw.IntegerField(null=False)
    is_images_needed = pw.BooleanField(default=False, null=False)
    images_count = pw.IntegerField(default=0, null=False)
    distance = pw.IntegerField(null=True)
    low_price = pw.IntegerField(null=True)
    high_price = pw.IntegerField(null=True)

    class Meta:
        indexes = (
            (('created_at', 'user'), True),
        )


class History(BaseModel):
    '''Модель класса для хранения связей запросов с отелями в базе.'''
    request = pw.ForeignKeyField(
        Request, backref='history_request', on_delete='CASCADE', null=False)
    hotel = pw.ForeignKeyField(Hotel, backref='history_hotel', null=False)
    hotel_price = pw.IntegerField(null=False)

    class Meta:
        indexes = (
            (('request', 'hotel'), True),
        )


Hotel.create_table()
History.create_table()
Request.create_table()
