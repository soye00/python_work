# data_seeder_fixed.py

from sqlalchemy import create_engine, Column, Integer, String, DECIMAL, ForeignKey, DateTime
from sqlalchemy import PrimaryKeyConstraint, text, BigInteger, TINYINT
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from faker import Faker
import random
from datetime import datetime, timedelta
import math
import os
from dotenv import load_dotenv

# -------------------------------------------------------------------------------------
# 1. 환경 설정 및 상수 정의

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3307")  # 기본값 3307

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

Base = declarative_base()
TICKET_PRICE = 13000.00
BATCH_SIZE = 500

# 할인 종류 분류 코드 (공통코드 011 참고)
DISCOUNT_POINT_CODE = "01101"
DISCOUNT_COUPON_CODE = "01102"
DISCOUNT_VOUCHER_CODE = "01103"

# 카드/은행/통신사/연령 코드
CARD_COMPANY_CODE = "00501"
BANK_CODE = "01201"
CARRIER_CODE = "00901"
AGE_TYPE_ADULT = "00201"

# -------------------------------------------------------------------------------------
# 2. ORM 모델 정의 

class Reservation(Base):
    __tablename__ = 'reservation'
    reservation_id = Column(BigInteger, primary_key=True)
    schedule_id = Column(BigInteger)
    user_id = Column(BigInteger, nullable=True)
    non_user_id = Column(BigInteger, nullable=True)
    price = Column(DECIMAL(10,2))
    status = Column(TINYINT)
    created_at = Column(DateTime, default=datetime.now)

class ReservationSeat(Base):
    __tablename__ = 'reservation_seat'
    reservation_seat_id = Column(BigInteger, primary_key=True)
    schedule_id = Column(BigInteger)
    seat_id = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.now)

class ReservationCount(Base):
    __tablename__ = 'reservation_count'
    reservation_id = Column(BigInteger)
    age_type = Column(String(7))
    __table_args__ = (PrimaryKeyConstraint('reservation_id','age_type'),)
    count = Column(Integer)
    price = Column(DECIMAL(10,2))

class ReservationSeatList(Base):
    __tablename__ = 'reservation_seat_list'
    reservation_id = Column(BigInteger)
    reservation_seat_id = Column(BigInteger)
    __table_args__ = (PrimaryKeyConstraint('reservation_id','reservation_seat_id'),)

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

class TicketDiscount(Base):
    __tablename__ = 'ticket_discount'
    benefit_id = Column(BigInteger)
    reservation_seat_id = Column(BigInteger)
    benefit_code = Column(String(7))
    __table_args__ = (
        PrimaryKeyConstraint('benefit_id','reservation_seat_id','benefit_code'),
        text('UNIQUE KEY uk_seat_discount (reservation_seat_id)')
    )
    applied_amount = Column(DECIMAL(10,2))
    created_at = Column(DateTime, default=datetime.now)

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

# -------------------------------------------------------------------------------------
# 3. 데이터 생성 함수

def generate_dummy_data(session, num_records):
    faker = Faker('ko_KR')
    random.seed(42)
    
    # FK 참조: 실제 DB에서 조회
    schedule_ids = [row[0] for row in session.execute("SELECT schedule_id FROM schedule").fetchall()]
    seat_ids = [row[0] for row in session.execute("SELECT seat_id FROM seat").fetchall()]
    user_ids = [row[0] for row in session.execute("SELECT user_id FROM user").fetchall()]
    policy_id = 1  # PaymentDiscount용 임시 정책

    if not schedule_ids or not seat_ids:
        raise Exception("schedule 또는 seat 데이터가 없습니다. ")

    entities_to_add = []
    current_benefit_id = 100000

    print(f"--- {num_records}개의 트랜잭션 데이터 생성 시작 (배치 사이즈: {BATCH_SIZE}) ---")

    for i in range(1, num_records+1):
        num_seats = random.randint(1,8)
        reservation_price = TICKET_PRICE * num_seats

        # 회원 / 비회원 랜덤
        is_user = random.choices([True, False], weights=[80, 20], k=1)[0]
        user_id = random.choice(user_ids) if is_user else None
        non_user_id = random.randint(1,1000) if not is_user else None

        schedule_id = random.choice(schedule_ids)
        total_discount_amount = 0.0

        # Reservation
        reservation = Reservation(
            schedule_id=schedule_id,
            user_id=user_id,
            non_user_id=non_user_id,
            price=reservation_price,
            status=1,
            created_at=datetime.now() - timedelta(hours=random.randint(1,500))
        )
        session.add(reservation)
        session.flush()  # reservation_id 획득

        # ReservationSeat + TicketDiscount
        used_seat_ids_in_schedule = set()
        available_seat_ids = seat_ids.copy()
        random.shuffle(available_seat_ids)

        for s in range(num_seats):
            # 중복 방지
            selected_seat_id = available_seat_ids.pop()
            seat = ReservationSeat(
                schedule_id=schedule_id,
                seat_id=selected_seat_id
            )
            entities_to_add.append(seat)
            session.flush()  # reservation_seat_id

            entities_to_add.append(ReservationSeatList(
                reservation_id=reservation.reservation_id,
                reservation_seat_id=seat.reservation_seat_id
            ))

            # 좌석별 할인
            discount_choice = random.randint(0,2)
            discount_amount = 0.0
            if discount_choice == 0:
                discount_amount = TICKET_PRICE
                benefit_code = DISCOUNT_POINT_CODE
            elif discount_choice == 1:
                discount_amount = 2000
                benefit_code = DISCOUNT_COUPON_CODE
            elif discount_choice == 2:
                discount_amount = TICKET_PRICE
                benefit_code = DISCOUNT_VOUCHER_CODE

            if discount_amount > 0:
                total_discount_amount += discount_amount
                entities_to_add.append(TicketDiscount(
                    benefit_id=current_benefit_id,
                    reservation_seat_id=seat.reservation_seat_id,
                    benefit_code=benefit_code,
                    applied_amount=discount_amount
                ))
                current_benefit_id += 1

        # ReservationCount
        entities_to_add.append(ReservationCount(
            reservation_id=reservation.reservation_id,
            age_type=AGE_TYPE_ADULT,
            count=num_seats,
            price=TICKET_PRICE
        ))

        # Payment
        final_amount = max(0.0, reservation_price - total_discount_amount)
        payment_method_choice = random.choices(['CARD', 'BANK', 'MOBILE'], weights=[70, 10, 20], k=1)[0]
        completed_date = reservation.created_at + timedelta(minutes=random.randint(1,10))

        payment = Payment(
            payment_type=0,
            type_id=reservation.reservation_id,
            origin_amount=reservation_price,
            discount_total=total_discount_amount,
            amount=final_amount,
            status=1,
            created_at=reservation.created_at,
            completed_at=completed_date
        )
        session.add(payment)
        session.flush()

        # PaymentDetail
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
                account_number=faker.bank_account_number(),
                account_holder_name=faker.name()[:12]
            ))
        else:
            entities_to_add.append(PaymentMobile(
                payment_id=payment.payment_id,
                carrier_code=CARRIER_CODE,
                phone_number=faker.phone_number()[:13],
                approval_code=faker.numerify('##########')
            ))

        # PaymentDiscount
        payment_level_discount = math.ceil(total_discount_amount * 0.05)
        entities_to_add.append(PaymentDiscount(
            payment_id=payment.payment_id,
            policy_id=policy_id,
            applied_amount=payment_level_discount
        ))

        # 배치 커밋
        if i % BATCH_SIZE == 0:
            session.add_all(entities_to_add)
            session.commit()
            entities_to_add = []
            print(f"--- {i}건 커밋 완료 ---")

    if entities_to_add:
        session.add_all(entities_to_add)
        session.commit()

    print(f"--- 최종 {num_records}개 트랜잭션 데이터 생성 완료 ---")

# -------------------------------------------------------------------------------------
# 4. 실행 진입점

if __name__ == '__main__':
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        print("기존 데이터 삭제 및 초기화 중...")
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()

        # 데이터 생성 (예: 10만 건)
        generate_dummy_data(session, 100000)

        session.close()

    except Exception as e:
        print(f"\n[오류 발생]: {e}")
        if 'session' in locals():
            session.rollback()
