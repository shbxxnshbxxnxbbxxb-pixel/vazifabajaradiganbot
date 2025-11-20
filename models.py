from peewee import *
from datetime import datetime

# SQLite ma'lumotlar bazasi
db = SqliteDatabase('presentation_bot.db')


class BaseModel(Model):
    """Asosiy model - barcha modellar uchun bazaviy klass"""
    class Meta:
        database = db


class User(BaseModel):
    """Foydalanuvchi modeli"""
    telegram_id = BigIntegerField(unique=True, index=True)
    full_name = CharField(max_length=200)
    gmail = CharField(max_length=200, unique=True)
    phone_number = CharField(max_length=20)
    age = IntegerField()
    
    # Google account ma'lumotlari (ixtiyoriy)
    google_account_name = CharField(max_length=200, null=True)
    profile_photo_url = TextField(null=True)
    
    # Tizim ma'lumotlari
    is_active = BooleanField(default=True)
    registration_date = DateTimeField(default=datetime.now)
    last_login = DateTimeField(default=datetime.now)
    
    # Statistika
    presentations_created = IntegerField(default=0)
    total_slides_generated = IntegerField(default=0)
    
    class Meta:
        table_name = 'users'
        indexes = (
            (('gmail',), True),  # Unique index
            (('telegram_id',), True),  # Unique index
        )
    
    def __str__(self):
        return f"User {self.full_name} ({self.gmail})"
    
    def increment_presentations(self, slide_count):
        """Prezentatsiyalar sonini oshirish"""
        self.presentations_created += 1
        self.total_slides_generated += slide_count
        self.last_login = datetime.now()
        self.save()


class Presentation(BaseModel):
    """Yaratilgan prezentatsiyalar modeli"""
    user = ForeignKeyField(User, backref='presentations', on_delete='CASCADE')
    topic = CharField(max_length=500)
    language = CharField(max_length=2)  # 'uz' yoki 'en'
    slide_count = IntegerField()
    background_color = CharField(max_length=50)
    
    created_at = DateTimeField(default=datetime.now)
    file_path = CharField(max_length=500, null=True)
    
    class Meta:
        table_name = 'presentations'
        indexes = (
            (('user', 'created_at'), False),
        )
    
    def __str__(self):
        return f"Presentation '{self.topic}' by {self.user.full_name}"


class UserSession(BaseModel):
    """Foydalanuvchi sessiylari (ixtiyoriy - xavfsizlik uchun)"""
    user = ForeignKeyField(User, backref='sessions', on_delete='CASCADE')
    session_token = CharField(max_length=200, unique=True)
    ip_address = CharField(max_length=50, null=True)
    user_agent = TextField(null=True)
    
    created_at = DateTimeField(default=datetime.now)
    expires_at = DateTimeField()
    is_active = BooleanField(default=True)
    
    class Meta:
        table_name = 'user_sessions'


class ActivityLog(BaseModel):
    """Faoliyat logi"""
    user = ForeignKeyField(User, backref='activities', on_delete='CASCADE', null=True)
    action_type = CharField(max_length=100)  # 'registration', 'login', 'create_presentation'
    description = TextField(null=True)
    ip_address = CharField(max_length=50, null=True)
    
    timestamp = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'activity_logs'
        indexes = (
            (('user', 'timestamp'), False),
            (('action_type', 'timestamp'), False),
        )


def initialize_database():
    """Ma'lumotlar bazasini yaratish va jadvallarni sozlash"""
    db.connect()
    db.create_tables([User, Presentation, UserSession, ActivityLog], safe=True)
    print("✓ Ma'lumotlar bazasi muvaffaqiyatli yaratildi!")


def get_user_by_telegram_id(telegram_id):
    """Telegram ID bo'yicha foydalanuvchini topish"""
    try:
        return User.get(User.telegram_id == telegram_id)
    except DoesNotExist:
        return None


def get_user_by_gmail(gmail):
    """Gmail bo'yicha foydalanuvchini topish"""
    try:
        return User.get(User.gmail == gmail)
    except DoesNotExist:
        return None


def create_user(telegram_id, full_name, gmail, phone_number, age, google_account_name=None):
    """Yangi foydalanuvchi yaratish"""
    try:
        user = User.create(
            telegram_id=telegram_id,
            full_name=full_name,
            gmail=gmail,
            phone_number=phone_number,
            age=age,
            google_account_name=google_account_name
        )
        
        # Ro'yxatdan o'tish logini saqlash
        ActivityLog.create(
            user=user,
            action_type='registration',
            description=f"Yangi foydalanuvchi ro'yxatdan o'tdi: {full_name}"
        )
        
        return user
    except IntegrityError as e:
        print(f"Xatolik: {e}")
        return None


def get_user_statistics(user):
    """Foydalanuvchi statistikasini olish"""
    return {
        'total_presentations': user.presentations_created,
        'total_slides': user.total_slides_generated,
        'registration_date': user.registration_date.strftime('%Y-%m-%d'),
        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M'),
        'recent_presentations': list(
            user.presentations
            .order_by(Presentation.created_at.desc())
            .limit(5)
        )
    }


# Ma'lumotlar bazasini avtomatik ishga tushirish
if __name__ == "__main__":
    initialize_database()