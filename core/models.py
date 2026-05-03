import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone


class TimestampedModel(models.Model):
  created_at = models.DateTimeField(auto_now_add=True)  # 레코드 최초 생성 시각 자동 저장
  updated_at = models.DateTimeField(auto_now=True)      # 레코드 저장할 때마다 현재 시각으로 자동 갱신

  class Meta:
    abstract = True 

class UserManager(BaseUserManager):
    def create_user(self, email, nickname, password=None):
        if not email:
            raise ValueError('이메일은 필수입니다.')
        user = self.model(
            email=self.normalize_email(email),    # 이메일 정규화
            nickname=nickname,                    # 닉네임 저장
        )
        user.set_password(password)               # 비밀번호 해싱하여 저장
        user.save(using=self._db)                 # 데이터베이스에 저장
        return user

    def create_superuser(self, email, nickname, password=None):
        user = self.create_user(email, nickname, password)
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    """
    회원 테이블
    """

    user_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,   
        editable=False       
    )  # UUID 자동 생성, 수정 불가


    email = models.EmailField(max_length=320, unique=True)  # 이메일
    nickname = models.CharField(max_length=6)               # 닉네임
    # password = models.CharField(max_length=16)            # 비밀번호 없어도됨
    created_at = models.DateTimeField(auto_now_add=True)    # 생성 시각
    is_verified = models.BooleanField(default=False)        # 이메일 인증 여부
    is_admin = models.BooleanField(default=False)           # 관리자 여부
    objects = UserManager()

    USERNAME_FIELD = 'email'          # 로그인 시 사용할 필드
    REQUIRED_FIELDS = ['nickname']    # 필수 입력 필드  

    class Meta:
        db_table = 'user'

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    @property
    def is_staff(self):
        return self.is_admin

    def __str__(self):
        return f"{self.nickname} ({self.email})"
    

class EmailVerification(models.Model):
    class Purpose(models.TextChoices):
        SIGNUP = 'SIGNUP', '회원가입'
        RESET = 'RESET', '비밀번호 재설정'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=320)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = 'email'

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.email} ({self.purpose})"
