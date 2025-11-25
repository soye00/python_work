# data_seeder_reservation_only.py

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
# 1. 환경 설정 및 상수 정의

load_dotenv()

# DB 연결 정보 (사용자 환경에 맞게 .env 파일 설정 필수)
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT", "3306")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

Base = declarative_base()
BATCH_SIZE = 500

# ✅ 기본 티켓 가격
BASE_TICKET_PRICE = 13000.00

# 할인/결제 코드 상수
DISCOUNT_POINT_CODE = "01101"
DISCOUNT_COUPON_CODE = "01102"
DISCOUNT_VOUCHER_CODE = "01103"
CARD_COMPANY_CODE = "00501"
BANK_CODE = "01201"
CARRIER_CODE = "00901"

# ✅ 관람 연령 코드 (common_code "002" 참고)
AGE_TYPE_ADULT = "00201"
AGE_TYPE_YOUTH = "00202"
AGE_TYPE_SENIOR = "00203"
AGE_TYPE_PRIME = "00204"
AGE_TYPE_CODES = [AGE_TYPE_ADULT, AGE_TYPE_YOUTH, AGE_TYPE_SENIOR, AGE_TYPE_PRIME]

# -------------------------------------------------------------------------------------
# 2. ORM 모델 정의 (데이터 삽입 및 조회에 필요한 모델만 정의)

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
    payment_type = Column(TINYINT) # 0: 예매, 1: 스토어
    type_id = Column(BigInteger)    # reservation_id 또는 order_id
    origin_amount = Column(DECIMAL(10,2))
    discount_total = Column(DECIMAL(10,2))
    amount = Column(DECIMAL(10,2))
    status = Column(TINYINT)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)

class TicketDiscount(Base):
    __tablename__ = 'ticket_discount'
    benefit_id = Column(BigInteger, primary_key=True) 
    reservation_seat_id = Column(BigInteger)
    benefit_code = Column(String(7))
    applied_amount = Column(DECIMAL(10,2))
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        # ✅ UniqueConstraint로 변경: 컬럼 이름을 인수로 전달
        UniqueConstraint('reservation_seat_id', name='uk_seat_discount'),
    )

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
    
# ✅ 가격 정보 조회를 위한 ORM 모델
class ScreenSchedule(Base):
    __tablename__ = 'screen_schedule'
    schedule_id = Column(BigInteger, primary_key=True)
    screen_type = Column(String(7))
    screen_time = Column(String(7))
    start_time = Column(Time) 

# -------------------------------------------------------------------------------------
# 3. 데이터 생성 함수

def apply_discount_policy(origin_amount, policy_id, policy_map):
    """discount_policy 테이블의 정책을 적용하여 할인 금액을 계산합니다."""
    policy = policy_map.get(policy_id)
    if not policy or origin_amount < policy['min_price']:
        return 0.0

    discount = 0.0
    
    # 1. 고정 금액 할인
    if policy['amount'] is not None:
        discount = policy['amount']
    # 2. 비율 할인
    elif policy['percent'] is not None:
        discount = origin_amount * policy['percent']
    
    # 3. 최대 할인 금액 제한 적용
    if policy['max_benefit_amount'] is not None:
        discount = min(discount, policy['max_benefit_amount'])
        
    return round(discount, 2)


def generate_random_account_number():
    """임의의 10~14자리 숫자 형태의 계좌 번호를 생성합니다."""
    # 0으로 시작하지 않는 숫자 문자열 생성
    # 계좌 번호가 길이를 초과하지 않도록 10~14자리로 지정
    length = random.randint(10, 14)
    if length > 0:
        return str(random.randint(1, 9)) + ''.join(random.choices('0123456789', k=length - 1))
    return '1234567890'


def calculate_coupon_discount(ticket_price, coupon_id, coupon_map):
    """쿠폰 정책에 따라 할인 금액을 계산합니다."""
    coupon = coupon_map.get(coupon_id)
    if not coupon:
        return 0.0

    # 최소 사용 금액 확인
    if ticket_price < coupon['min_price']:
        return 0.0

    discount = 0.0
    
    if coupon['type'] == 0: # 0: 할인 금액 (고정값)
        discount = coupon['value']
    elif coupon['type'] == 1: # 1: 할인율 (비율)
        discount = ticket_price * (coupon['value'] / 100.0) # discount_value를 %로 가정
        
        # 최대 할인 금액 제한 적용
        if coupon['max_amount'] is not None:
            discount = min(discount, coupon['max_amount'])
            
    return round(discount, 2)


def calculate_final_ticket_price(schedule_id, age_type_code, 
                                 schedule_map, screen_type_map, 
                                 screen_time_map, age_type_map):
    """모든 가격 변동 요소를 고려하여 최종 티켓 가격을 계산합니다."""
    
    screen_type, screen_time = schedule_map.get(schedule_id, (None, None))
    if not screen_type or not screen_time:
        return BASE_TICKET_PRICE

    final_price = BASE_TICKET_PRICE 
    
    # 상영관 유형 가격 적용
    screen_price = screen_type_map.get(screen_type, 0.00)
    final_price += screen_price 

    # 상영 시간 가감 가격 적용
    time_adjustment = screen_time_map.get(screen_time, 0.00)
    final_price += time_adjustment
    
    # 연령별 가감 가격 적용
    age_adjustment = age_type_map.get(age_type_code, 0.00)
    final_price += age_adjustment
    
    return max(0.0, final_price) 


def generate_dummy_data(session, num_records):
    faker = Faker('ko_KR')
    random.seed(42)
    
    # ------------------ DB 참조 데이터 및 가격 정책 조회 ------------------

    schedule_data = session.execute(
       text( "SELECT schedule_id, screen_type, screen_time FROM screen_schedule")
    ).fetchall()
    schedule_map = {row[0]: (row[1], row[2]) for row in schedule_data}
    schedule_ids = list(schedule_map.keys())

    screen_type_prices = session.execute(text("SELECT screen_type, price FROM screen_type")).fetchall()
    screen_type_map = {row[0]: float(row[1]) for row in screen_type_prices}

    screen_time_adjustments = session.execute(text("SELECT screen_time, adjust_price FROM screen_time")).fetchall()
    screen_time_map = {row[0]: float(row[1]) for row in screen_time_adjustments}

    age_type_adjustments = session.execute(text("SELECT age_type, adjust_price FROM age_type")).fetchall()
    age_type_map = {row[0]: float(row[1]) for row in age_type_adjustments}
    
    seat_ids = [row[0] for row in session.execute(text("SELECT seat_id FROM seat")).fetchall()]
    user_ids = [row[0] for row in session.execute(text("SELECT user_id FROM user")).fetchall()]
    policy_id = 1 

    policy_data = session.execute(
        text("SELECT policy_id, discount_amount, discount_percent, min_price, max_benefit_amount FROM discount_policy")
    ).fetchall()

    policy_map = {
        row[0]: {
            'amount': float(row[1]) if row[1] else None,
            'percent': float(row[2]) if row[2] else None,
            'min_price': float(row[3]),
            'max_benefit_amount': float(row[4]) if row[4] else None,
        }
        for row in policy_data
    }
    policy_ids = list(policy_map.keys())
    policy_id = random.choice(policy_ids) if policy_ids else 1 # 사용할 정책 ID 랜덤 선택

    # 쿠폰 정책 데이터 조회
    coupon_data = session.execute(
        text("SELECT coupon_id, discount_type, discount_value, max_discount_amount, min_price FROM coupon")
    ).fetchall()
    
    # coupon_id를 키로 하는 딕셔너리로 저장
    coupon_map = {
        row[0]: {
            'type': row[1], # 0: 금액, 1: 비율
            'value': float(row[2]) if row[2] else 0.0,
            'max_amount': float(row[3]) if row[3] else None,
            'min_price': float(row[4]),
        }
        for row in coupon_data
    }
    coupon_ids = list(coupon_map.keys())
    
    if not coupon_ids:
        # 쿠폰 데이터가 없으면 쿠폰 할인을 비활성화하기 위해 임의의 ID를 설정
        print("경고: coupon 테이블에 데이터가 없어 쿠폰 할인이 적용되지 않습니다.")


    
    if not schedule_ids or not seat_ids or not user_ids:
        raise Exception("필수 데이터(schedule, seat, user)가 없습니다. 먼저 기본 데이터를 생성하세요.")

    entities_to_add = []
    current_benefit_id = 100000

    print(f"--- {num_records}개의 예매 트랜잭션 데이터 생성 시작 (배치 사이즈: {BATCH_SIZE}) ---")

    for i in range(1, num_records+1):
        
        # ------------------ ✅ 회원/비회원 비율 설정 ------------------
        # 회원 80%, 비회원 20%
        is_user = random.choices([True, False], weights=[80, 20], k=1)[0]
        user_id = random.choice(user_ids) if is_user and user_ids else None
        non_user_id = random.randint(1, 1000) if not is_user else None
        
        # ------------------ ✅ 예매 트랜잭션 고정 설정 ------------------
        payment_type_choice = 0 # 0: 영화 예매로 고정
        total_discount_amount = 0.0
        reservation_id = None
        
        # ------------------ 0. 예매 데이터 생성 ------------------
        
        num_seats = random.randint(1, 4)
        schedule_id = random.choice(schedule_ids)
        
        final_reservation_price = 0.0
        age_count_map = {}
        
        # 연령 비율 (성인 60, 청소년 25, 경로 10, 우대 5)
        age_types_for_seats = random.choices(
            AGE_TYPE_CODES, 
            weights=[60, 25, 10, 5], 
            k=num_seats
        )

        for age_type in age_types_for_seats:
            # 동적 가격 계산
            ticket_price = calculate_final_ticket_price(
                schedule_id, age_type, 
                schedule_map, screen_type_map, 
                screen_time_map, age_type_map
            )
            final_reservation_price += ticket_price
            
            if age_type not in age_count_map:
                age_count_map[age_type] = {'count': 0, 'price': ticket_price}
            age_count_map[age_type]['count'] += 1

        # Reservation 테이블 생성
        reservation = Reservation(
            schedule_id=schedule_id,
            user_id=user_id,
            non_user_id=non_user_id,
            price=final_reservation_price,
            status=1,
            created_at=datetime.now() - timedelta(hours=random.randint(1,500))
        )
        session.add(reservation)
        session.flush()
        reservation_id = reservation.reservation_id

        # ReservationSeat + TicketDiscount 생성
        available_seat_ids = seat_ids.copy()
        random.shuffle(available_seat_ids)
        
        base_ticket_price = final_reservation_price / num_seats if num_seats > 0 else 0
        
        
        for s in range(num_seats):
            selected_seat_id = available_seat_ids.pop()
            seat = ReservationSeat(
                schedule_id=schedule_id,
                seat_id=selected_seat_id
            )

            session.add(seat)
            session.flush() # 👈 즉시 DB에 삽입하고 seat.reservation_seat_id 할당

            # entities_to_add.append(seat)
            # session.flush()

            # entities_to_add.append(ReservationSeatList(
            #     reservation_id=reservation_id,
            #     reservation_seat_id=seat.reservation_seat_id
            # ))
            reservation_seat_list_entry = ReservationSeatList(
                reservation_id=reservation_id,
                reservation_seat_id=seat.reservation_seat_id
            )
            entities_to_add.append(reservation_seat_list_entry)


            # # 좌석별 할인
            # discount_choice = random.randint(0, 3) 
            # discount_amount = 0.0
            # max_discount = base_ticket_price * 0.5 
            
            # if discount_choice == 0: 
            #     discount_amount = round(random.uniform(500, max_discount), 2)
            #     benefit_code = DISCOUNT_POINT_CODE
            # elif discount_choice == 1: 
            #     discount_amount = 2000
            #     benefit_code = DISCOUNT_COUPON_CODE
            # elif discount_choice == 2: 
            #     discount_amount = base_ticket_price if random.random() < 0.2 else round(random.uniform(1000, max_discount), 2)
            #     benefit_code = DISCOUNT_VOUCHER_CODE

            # discount_amount = min(discount_amount, max_discount)
            discount_choice = random.randint(0, 3) 
            discount_amount = 0.0    

            current_ticket_price = base_ticket_price
            max_discount = current_ticket_price # 최대 할인은 티켓 가격을 넘을 수 없음

            if discount_choice == 0: 
                # 수정: 포인트 할인 14,000원 고정 (티켓 가격을 넘지 않도록 min으로 제한)
                discount_amount = min(14000.00, current_ticket_price) 
                benefit_code = DISCOUNT_POINT_CODE

            elif discount_choice == 1 and coupon_ids: 
            # 수정: 쿠폰 정책을 참조하여 할인 금액 계산
                random_coupon_id = random.choice(coupon_ids)
                discount_amount = calculate_coupon_discount(current_ticket_price, random_coupon_id, coupon_map)
                benefit_code = DISCOUNT_COUPON_CODE

            elif discount_choice == 2: #  수정: 상품권 사용 = 무료 관람 (전액 할인)
                discount_amount = current_ticket_price
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

        # ReservationCount 생성
        for age_type, data in age_count_map.items():
            entities_to_add.append(ReservationCount(
                reservation_id=reservation_id,
                age_type=age_type,
                count=data['count'],
                price=data['price']
            ))
        
        origin_amount = final_reservation_price
            

        # ------------------ 1. Payment 생성 ------------------
        
        final_amount = max(0.0, origin_amount - total_discount_amount)
        completed_date = datetime.now() - timedelta(hours=random.randint(1,10))

        # 결제 수단 비율 (카드 70%, 은행 10%, 모바일 20%)
        payment_method_choice = random.choices(['CARD','BANK','MOBILE'], weights=[70, 10, 20], k=1)[0]
        
        payment = Payment(
            payment_type=0, # 예매로 고정
            type_id=reservation_id, # reservation_id 사용
            origin_amount=origin_amount,
            discount_total=total_discount_amount,
            amount=final_amount,
            status=1,
            created_at=completed_date - timedelta(minutes=random.randint(1, 5)),
            completed_at=completed_date
        )
        session.add(payment)
        session.flush()

        # ------------------ 2. PaymentDetail 생성 ------------------
        
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

        # ------------------ 3. PaymentDiscount 생성 ------------------
        
        # payment_level_discount = math.ceil(total_discount_amount * 0.05) # 테스트용 랜덤적용방법
        # entities_to_add.append(PaymentDiscount(
        #     payment_id=payment.payment_id,
        #     policy_id=policy_id,
        #     applied_amount=payment_level_discount
        # ))
        payment_level_discount = apply_discount_policy(
            origin_amount, 
            policy_id, 
            policy_map
        )

        if payment_level_discount > 0:
            entities_to_add.append(PaymentDiscount(
                payment_id=payment.payment_id,
                policy_id=policy_id,
                applied_amount=payment_level_discount
            ))
            
            # 최종 금액 업데이트: Payment.discount_total에 정책 할인 금액 추가
            payment.discount_total += payment_level_discount 
            payment.amount -= payment_level_discount 

            # 정책 ID를 랜덤하게 다시 선택
            policy_id = random.choice(policy_ids) if policy_ids else 1



        # 배치 커밋
        if i % BATCH_SIZE == 0:
            session.add_all(entities_to_add)
            session.commit()
            entities_to_add = []
            print(f"--- {i}건 커밋 완료 ---")

    if entities_to_add:
        session.add_all(entities_to_add)
        session.commit()

    print(f"--- 최종 {num_records}개 예매 데이터 생성 완료 ---")

# -------------------------------------------------------------------------------------
# 4. 실행 진입점

if __name__ == '__main__':
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()

        print("기존 예매 관련 데이터 삭제 및 초기화 중...")
        # 예매 관련 테이블만 삭제 (order 테이블은 제외)
        tables_to_delete = ['reservation_seat_list', 'payment_discount', 'ticket_discount', 
                            'payment_card', 'payment_bank_transfer', 'payment_mobile', 
                            'payment', 'reservation_count', 'reservation_seat', 'reservation']
        
        for table_name in tables_to_delete:
            session.execute(text(f"DELETE FROM {table_name}"))
        session.commit()

        # 데이터 생성 
        generate_dummy_data(session, 100)

        session.close()

    except Exception as e:
        print(f"\n[오류 발생]: {e}")
        if 'session' in locals():
            session.rollback()