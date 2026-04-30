from django.db import models
import uuid

# Create your models here.

# Django의 FK/OneToOneField는 DB 테이블에서 _id가 기본적으로 붙는다. (ex. hello = models.ForeignKey() --> hello_id로 DB에 생성)

# 테이블명: contract
    # (참고) NN = Not Null
    # chatroom_id   uuid            NN      (FK)
    # contract_id   uuid            NN      (PK)
    # title         varchar(100)    Null
    # content       text            Null
    # created_at    timestamp       NN
    # size          int             Null

class Contract(models.Model):
    contract_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chatroom = models.OneToOneField('chat.Chatroom', on_delete=models.CASCADE)              # chat앱의 Chatroom 참조 | chatroom에서 해당 chatroom 삭제 시, contract도 같이 삭제
    title = models.CharField(max_length=100, null=True)                                     #
    content = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    size = models.IntegerField(null=True)

    class Meta:
        db_table = 'contract'



# 테이블명: contract
    # (참고) NN = Not Null
    # contract_id   uuid            NN      (FK)
    # location      varchar(100)    Null
    # period        date            Null
    # month_rent    int             Null
    # security      int             Null
    # house_cost    varchar(10)     Null

class PropertyInfo(models.Model):
    contract = models.OneToOneField(Contract, on_delete=models.CASCADE, primary_key=True)   # 동일 Contract 참조 | contract(테이블)에서 해당 chatroom 삭제 시, property_info도 같이 삭제
    location = models.CharField(max_length=40, null=True)
    period = models.DateField(null=True)
    month_rent = models.IntegerField(null=True)
    security = models.IntegerField(null=True)
    house_cost = models.CharField(max_length=10, null=True)

    class Meta:
        db_table = 'property_info'