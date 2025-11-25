# data_seeder_store_payment_only.py

from sqlalchemy import create_engine, Column, Integer, String, DECIMAL, ForeignKey, DateTime, Time, Date, PrimaryKeyConstraint, text, BigInteger, UniqueConstraint
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from faker import Faker
import random
from datetime import datetime, timedelta
import math
import os
from dotenv import load_dotenv

# -------------------------------------------------------------------------------------
# 1. 환경 설정 및 상수 정의 (기존 파일과 동일)

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3307")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

Base = declarative_base()
BATCH_SIZE = 500

# 코드 상수 (결제 상세 정보 생성을 위해 필요)
CARD_COMPANY_CODE = "00501"
BANK_CODE = "01201"
CARRIER_CODE = "00901"

# -------------------------------------------------------------------------------------
# 2. ORM 모델 정의 (Payment 및 Order 모델만 필요)

class Payment(Base):
    __tablename__ = 'payment'
    payment_id = Column(BigInteger, primary_key=True)
    payment_type = Column(TINYINT)
    type_id = Column(BigInteger)
    origin_amount = Column(DECIMAL(10,2))
    discount_total = Column(DECIMAL(10,2))
    amount = Column(DECIMAL(10,2))
    status = Column(TINYINT)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

class PaymentDiscount(Base):
    __tablename__ = 'payment_discount'
    payment_id = Column(BigInteger)
    policy_id = Column(BigInteger)
    __table_args__ = (PrimaryKeyConstraint('payment_id','policy_id'),)
    applied_amount = Column(DECIMAL(10,2))
    created_at = Column(DateTime, default=datetime.now)

class PaymentCard(Base):
    __tablename__ = 'payment_card'
    payment_id = Column(BigInteger, primary_key=True)
    card_company_code = Column(String(7))
    card_number = Column(String(4))
    installment_months = Column(Integer, default=0)
    card_approval_number = Column(String(10), nullable=True)

class PaymentBankTransfer(Base):
    __tablename__ = 'payment_bank_transfer'
    payment_id = Column(BigInteger, primary_key=True)
    bank_code = Column(String(7))
    account_number = Column(String(30))
    account_holder_name = Column(String(12))

class PaymentMobile(Base):
    __tablename__ = 'payment_mobile'
    payment_id = Column(BigInteger, primary_key=True)
    carrier_code = Column(String(7))
    phone_number = Column(String(13))
    approval_code = Column(String(10))
    
# ✅ Order 테이블 (데이터 조회를 위해 필요)
class Order(Base):
    __tablename__ = 'order'
    order_id = Column(BigInteger, primary_key=True)
    price = Column(DECIMAL(10,2)) # 총 구매 금액 (payment.origin_amount로 사용)

# -------------------------------------------------------------------------------------
# 3. 스토어 결제 더미 데이터 생성 함수

def generate_random_account_number():
    """임의의 10~14자리 숫자 형태의 계좌 번호를 생성합니다."""
    length = random.randint(10, 14)
    if length > 0:
        return str(random.randint(1, 9)) + ''.join(random.choices('0123456789', k=length - 1))
    return '1234567890'


def generate_store_payments(session, num_payments):
    faker = Faker('ko_KR')
    random.seed(43) # 예매와 다른 시드 사용
    
    # 1. 존재하는 Order 데이터 조회
    # order_data: [(order_id, price), ...]
    order_data = session.execute(
        text("SELECT order_id, price FROM `order`")
    ).fetchall()
    
    if not order_data:
        raise Exception("`order` 테이블에 데이터가 없습니다. 먼저 order 테이블을 채워주세요.")

    # 생성할 결제 건수가 Order 수보다 많을 경우, Order 데이터를 반복 사용
    if num_payments > len(order_data):
        payment_orders = random.choices(order_data, k=num_payments)
    else:
        # num_payments가 Order 수보다 적을 경우, 랜덤하게 Order를 선택
        payment_orders = random.sample(order_data, num_payments)

    policy_id = 1 
    entities_to_add = []

    print(f"--- {num_payments}개의 스토어 결제 데이터 생성 시작 (배치 사이즈: {BATCH_SIZE}) ---")

    for i, (order_id, origin_amount) in enumerate(payment_orders):
        
        # 1. 할인 금액 설정 -> 스토어는 할인 X
        origin_amount = float(origin_amount)
        total_discount_amount = 0.0
        
        final_amount = origin_amount
        completed_date = datetime.now() - timedelta(hours=random.randint(1,10))
        
        # 2. 결제 수단 랜덤 선택 (카드 70%, 은행 10%, 모바일 20%)
        payment_method_choice = random.choices(['CARD','BANK','MOBILE'], weights=[70, 10, 20], k=1)[0]
        
        # 3. Payment 레코드 생성
        payment = Payment(
            payment_type=1, # 스토어 결제로 고정
            type_id=order_id, # order_id 참조
            origin_amount=origin_amount,
            discount_total=total_discount_amount,
            amount=final_amount,
            status=1,
            created_at=completed_date - timedelta(minutes=random.randint(1, 5)),
            completed_at=completed_date
        )
        session.add(payment)
        session.flush()

        # 4. PaymentDetail 생성
        if payment_method_choice == 'CARD':
            entities_to_add.append(PaymentCard(
                payment_id=payment.payment_id,
                card_company_code=CARD_COMPANY_CODE,
                card_number=faker.numerify('####'),
                installment_months=random.choice([0,3,6]),
                card_approval_number=faker.numerify('##########')
            ))
        elif payment_method_choice == 'BANK':
            entities_to_add.append(PaymentBankTransfer(
                payment_id=payment.payment_id,
                bank_code=BANK_CODE,
                account_number=generate_random_account_number(),
                account_holder_name=faker.name()[:12]
            ))
        else:
            mobile_number = "010-" + faker.numerify('####') + "-" + faker.numerify('####')
            entities_to_add.append(PaymentMobile(
                payment_id=payment.payment_id,
                carrier_code=CARRIER_CODE,
                phone_number=mobile_number,
                approval_code=faker.numerify('##########')
            ))

        # # 5. PaymentDiscount 생성 필요 없음 --> 스토어는 할인 적용 X
        # payment_level_discount = math.ceil(total_discount_amount * 0.05)
        # entities_to_add.append(PaymentDiscount(
        #     payment_id=payment.payment_id,
        #     policy_id=policy_id,
        #     applied_amount=payment_level_discount
        # ))

        # 배치 커밋
        if (i + 1) % BATCH_SIZE == 0:
            session.add_all(entities_to_add)
            session.commit()
            entities_to_add = []
            print(f"--- {i + 1}건 커밋 완료 ---")

    if entities_to_add:
        session.add_all(entities_to_add)
        session.commit()

    print(f"--- 최종 {num_payments}개 스토어 결제 데이터 생성 완료 ---")


# -------------------------------------------------------------------------------------
# 4. 실행 진입점

if __name__ == '__main__':
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()

        print("기존 스토어 관련 결제 데이터 삭제 및 초기화 중...")
        # 스토어 결제와 관련된 테이블만 삭제 (FK 제약조건을 피하기 위함)
        
        # Payment 테이블에서 payment_type=1인 레코드의 payment_id를 조회
        payment_ids_to_delete = [
            row[0] for row in session.execute(
                text("SELECT payment_id FROM payment WHERE payment_type = 1")
            ).fetchall()
        ]
        
        if payment_ids_to_delete:
            print(f"{len(payment_ids_to_delete)}건의 기존 스토어 결제 레코드를 삭제합니다.")
            
            # 관련된 PaymentDetail 및 PaymentDiscount 레코드 삭제
            for table_name in ['payment_discount', 'payment_card', 'payment_bank_transfer', 'payment_mobile']:
                session.execute(
                    text(f"DELETE FROM {table_name} WHERE payment_id IN :ids"), 
                    {"ids": payment_ids_to_delete}
                )
                
            # 최종 Payment 레코드 삭제
            session.execute(
                text("DELETE FROM payment WHERE payment_type = 1")
            )
            session.commit()
        else:
             print("기존 스토어 결제 데이터가 없어 삭제를 건너뜁니다.")
        

        # 데이터 생성 (예: 2만 건의 스토어 결제 데이터 생성)
        # ✅ 생성할 결제 건수는 order 테이블의 데이터 수에 맞춰 조정해야 합니다.
        generate_store_payments(session, 100) 

        session.close()

    except Exception as e:
        print(f"\n[오류 발생]: {e}")
        if 'session' in locals():
            session.rollback()