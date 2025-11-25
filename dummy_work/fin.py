# data_seeder_unified_final.py

from sqlalchemy import create_engine, Column, Integer, String, DECIMAL, ForeignKey, DateTime, Time, Date
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
DB_PORT = os.getenv("DB_PORT", "3307")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

Base = declarative_base()
BATCH_SIZE = 500

# 기본 티켓 가격
BASE_TICKET_PRICE = 15000.00

# 할인/결제 코드 상수
DISCOUNT_POINT_CODE = "01101"   # 포인트
DISCOUNT_COUPON_CODE = "01102"  # 쿠폰
DISCOUNT_VOUCHER_CODE = "01103" # 관람권 (Voucher)
CARD_COMPANY_CODE_PREFIX = "005" 

# 관람 연령 코드
AGE_TYPE_ADULT = "00201"
AGE_TYPE_YOUTH = "00202"
AGE_TYPE_SENIOR = "00203"
AGE_TYPE_PRIME = "00204"
AGE_TYPE_CODES = [AGE_TYPE_ADULT, AGE_TYPE_YOUTH, AGE_TYPE_SENIOR, AGE_TYPE_PRIME]

# -------------------------------------------------------------------------------------
# 2. ORM 모델 정의 (모든 관련 테이블 포함)

# 제공된 스키마 기반 ORM 모델
class User(Base):
    __tablename__ = 'user'
    user_id = Column(BigInteger, primary_key=True)
    point = Column(DECIMAL(10,2))
    # 필요한 필드만 정의

class NonUser(Base):
    __tablename__ = 'non_user'
    non_user_id = Column(BigInteger, primary_key=True)
    # 필요한 필드만 정의

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
    benefit_id = Column(BigInteger, primary_key=True) 
    reservation_seat_id = Column(BigInteger)
    benefit_code = Column(String(7))
    __table_args__ = (
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
    
# 스토어 모델 (8:2 비율 반영을 위해 필요)
class Order(Base):
    __tablename__ = 'order'
    order_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger)
    price = Column(DECIMAL(10,2))
    # 필요한 필드만 정의

class StoreItem(Base):
    __tablename__ = 'store_item'
    store_item_id = Column(BigInteger, primary_key=True)
    price = Column(DECIMAL(10,2))

# -------------------------------------------------------------------------------------
# 3. 데이터 생성 함수

def calculate_final_ticket_price(schedule_id, age_type_code, 
                                 schedule_map, screen_type_map, 
                                 screen_time_map, age_type_map):
    """모든 가격 변동 요소를 고려하여 최종 티켓 가격을 계산합니다."""
    screen_type, screen_time = schedule_map.get(schedule_id, (None, None))
    if not screen_type or not screen_time: return BASE_TICKET_PRICE
    final_price = BASE_TICKET_PRICE 
    final_price += screen_type_map.get(screen_type, 0.00) 
    final_price += screen_time_map.get(screen_time, 0.00)
    final_price += age_type_map.get(age_type_code, 0.00)
    return max(0.0, final_price) 


def generate_dummy_data(session, num_records):
    faker = Faker('ko_KR')
    random.seed(42)
    
    # ------------------ 1. DB 참조 데이터 및 정책 조회 ------------------
    
    # 스케줄, 좌석 ID 조회
    schedule_data = session.execute(text("SELECT schedule_id, screen_type, screen_time FROM screen_schedule")).fetchall()
    schedule_map = {row[0]: (row[1], row[2]) for row in schedule_data}
    schedule_ids = list(schedule_map.keys())
    seat_ids = [row[0] for row in session.execute(text("SELECT seat_id FROM seat")).fetchall()]
    
    # ✅ 회원/비회원 정보 및 포인트 조회
    user_data = session.execute(text("SELECT user_id, point FROM user")).fetchall()
    user_point_map = {row[0]: float(row[1]) for row in user_data}
    user_ids = list(user_point_map.keys())
    non_user_ids = [row[0] for row in session.execute(text("SELECT non_user_id FROM non_user")).fetchall()]
    
    # 가격 정책 조회
    screen_type_prices = session.execute(text("SELECT screen_type, price FROM screen_type")).fetchall()
    screen_type_map = {row[0]: float(row[1]) for row in screen_type_prices}
    screen_time_adjustments = session.execute(text("SELECT screen_time, adjust_price FROM screen_time")).fetchall()
    screen_time_map = {row[0]: float(row[1]) for row in screen_time_adjustments}
    age_type_adjustments = session.execute(text("SELECT age_type, adjust_price FROM age_type")).fetchall()
    age_type_map = {row[0]: float(row[1]) for row in age_type_adjustments}
    
    # 스토어 상품 ID 조회 및 맵 생성: {store_item_id: price}
    store_items_data = session.execute(text("SELECT store_item_id, price FROM store_item")).fetchall()
    store_item_map = {row[0]: float(row[1]) for row in store_items_data}
    store_item_ids = list(store_item_map.keys())

    # ✅ 할인 정책 조회 및 가공
    policy_data = session.execute(
        text("SELECT policy_id, partner_id, discount_amount, discount_percent, min_price, max_benefit_amount FROM discount_policy WHERE end_date >= CURDATE()")
    ).fetchall()
    
    discount_policy_map = {}
    for row in policy_data:
        policy_id, partner_id, amount, percent, min_price, max_benefit = row
        if partner_id not in discount_policy_map:
            discount_policy_map[partner_id] = []
        discount_policy_map[partner_id].append({
            'id': policy_id, 'amount': float(amount) if amount else None,
            'percent': float(percent) if percent else None,
            'min_price': float(min_price), 'max_benefit': float(max_benefit) if max_benefit else float('inf')
        })
    available_partner_ids = [k for k in discount_policy_map.keys() if k.startswith(CARD_COMPANY_CODE_PREFIX)]

    if not schedule_ids or not seat_ids or not user_ids or not non_user_ids or not store_item_ids:
        raise Exception("필수 데이터(schedule, seat, user, non_user, store_item)가 없습니다. 먼저 기본 데이터를 생성하세요.")

    # ✅ 혜택 소유 시뮬레이션 (인메모리)
    # 30%의 유저가 쿠폰 소유, 15%가 관람권 소유
    coupon_users = set(random.sample(user_ids, int(len(user_ids) * 0.3)))
    voucher_users = set(random.sample(user_ids, int(len(user_ids) * 0.15)))

    entities_to_add = []

    print(f"--- {num_records}개의 통합 트랜잭션 데이터 생성 시작 (예매:80%, 스토어:20%, 배치 사이즈: {BATCH_SIZE}) ---")

    for i in range(1, num_records+1):
        
        # ------------------ 2. 트랜잭션 타입 결정 (8:2 비율) ------------------
        payment_type_choice = random.choices([0, 1], weights=[80, 20], k=1)[0] # 0: 예매, 1: 스토어
        
        # ------------------ 3. 사용자 타입 결정 ------------------
        # 스토어(1)는 회원 필수, 예매(0)는 회원/비회원 가능
        if payment_type_choice == 1:
            is_user = True
            user_id = random.choice(user_ids)
            non_user_id = None
        else:
            is_user = random.choices([True, False], weights=[80, 20], k=1)[0]
            user_id = random.choice(user_ids) if is_user else None
            non_user_id = random.choice(non_user_ids) if not is_user else None
        
        total_discount_amount = 0.0
        reservation_id = None
        order_id = None 
        
        # ------------------ 4. 예매(0) vs 스토어(1) 데이터 생성 로직 ------------------
        
        if payment_type_choice == 0: # 영화 예매 트랜잭션
            num_seats = random.randint(1, 4)
            schedule_id = random.choice(schedule_ids)
            final_reservation_price = 0.0
            age_count_map = {}
            
            age_types_for_seats = random.choices(AGE_TYPE_CODES, weights=[60, 25, 10, 5], k=num_seats)

            # 티켓 가격 및 할인 계산
            for age_type in age_types_for_seats:
                ticket_price = calculate_final_ticket_price(schedule_id, age_type, schedule_map, screen_type_map, screen_time_map, age_type_map)
                final_reservation_price += ticket_price
                if age_type not in age_count_map:
                    age_count_map[age_type] = {'count': 0, 'price': ticket_price}
                age_count_map[age_type]['count'] += 1

            # Reservation 생성
            reservation = Reservation(
                schedule_id=schedule_id, user_id=user_id, non_user_id=non_user_id, price=final_reservation_price, status=1, created_at=datetime.now() - timedelta(hours=random.randint(1,500))
            )
            session.add(reservation)
            session.flush()
            reservation_id = reservation.reservation_id

            # ReservationSeat & TicketDiscount 생성
            base_ticket_price = final_reservation_price / num_seats if num_seats > 0 else 0
            
            for s in range(num_seats):
                seat = ReservationSeat(schedule_id=schedule_id, seat_id=random.choice(seat_ids))
                entities_to_add.append(seat)
                session.flush()

                entities_to_add.append(ReservationSeatList(reservation_id=reservation_id, reservation_seat_id=seat.reservation_seat_id))
                
                # 좌석별 할인 적용 (회원만 혜택 가능, 50% 확률로 사용 시도)
                if is_user and random.random() < 0.5:
                    
                    possible_benefits = []
                    # 1. 포인트 사용 가능
                    if user_point_map.get(user_id, 0.0) > 1000: # 포인트 잔액이 1000원 이상일 때 시도 가능
                        possible_benefits.append(DISCOUNT_POINT_CODE)
                    # 2. 쿠폰 소유
                    if user_id in coupon_users:
                        possible_benefits.append(DISCOUNT_COUPON_CODE)
                    # 3. 관람권 소유
                    if user_id in voucher_users:
                        possible_benefits.append(DISCOUNT_VOUCHER_CODE)
                        
                    if possible_benefits:
                        benefit_code = random.choice(possible_benefits)
                        max_discount = base_ticket_price * 0.5 
                        discount_amount = round(random.uniform(500, max_discount), 2)
                        
                        if benefit_code == DISCOUNT_POINT_CODE:
                            # 포인트는 보유 포인트 이상 할인 불가 (시뮬레이션)
                            available_point = user_point_map.get(user_id, 0.0)
                            discount_amount = min(discount_amount, available_point)
                            # 포인트 사용 후 잔액 감소 로직은 not yet 

                        if discount_amount > 0:
                            total_discount_amount += discount_amount
                            entities_to_add.append(TicketDiscount(
                                reservation_seat_id=seat.reservation_seat_id, 
                                benefit_code=benefit_code,
                                applied_amount=discount_amount
                            ))

            # ReservationCount 생성
            for age_type, data in age_count_map.items():
                entities_to_add.append(ReservationCount(reservation_id=reservation_id, age_type=age_type, count=data['count'], price=data['price']))
            
            origin_amount = final_reservation_price
            
        else: # 스토어 구매 트랜잭션 
            # 스토어 로직은 TicketDiscount 로직은 없음
            
            selected_item_id = random.choice(store_item_ids)
            unit_price = store_item_map[selected_item_id]
            quantity = random.randint(1, 3)
            total_price = round(unit_price * quantity, 2)
            
            # Order 테이블 생성 (FK 제약조건 충족을 위해 필수)
            order = Order(
                user_id=user_id, 
                price=total_price, 
                status=0,
                created_at=datetime.now() - timedelta(hours=random.randint(1,500))
            )
            session.add(order)
            session.flush()
            order_id = order.order_id 

            # Payment 금액 설정
            origin_amount = total_price
            
            # 스토어 할인 (총 금액의 5% ~ 15% 랜덤)
            discount_percentage = random.uniform(0.05, 0.15)
            total_discount_amount = round(origin_amount * discount_percentage, 2)

        # ------------------ 5. 공통 Payment 생성 및 결제 할인 적용 ------------------
        
        final_amount_before_payment_discount = max(0.0, origin_amount - total_discount_amount)
        final_amount = final_amount_before_payment_discount
        payment_discount_amount = 0.0
        
        completed_date = datetime.now() - timedelta(hours=random.randint(1,10))
        payment_method_choice = random.choices(['CARD','BANK','MOBILE'], weights=[70, 10, 20], k=1)[0]
        selected_card_company_code = None
        
        if payment_method_choice == 'CARD':
            # 카드사 코드 랜덤 선택 (할인 정책이 존재하는 카드사 중)
            selected_card_company_code = random.choice(available_partner_ids)
            
            # ✅ PAYMENT_DISCOUNT 시나리오: 카드 결제 시 60% 확률로 할인 시도
            if random.random() < 0.6: 
                policies = discount_policy_map.get(selected_card_company_code, [])
                
                if policies:
                    policy = random.choice(policies)
                    
                    if final_amount_before_payment_discount >= policy['min_price']:
                        
                        discount = 0.0
                        if policy['amount'] is not None:
                            discount = policy['amount']
                        elif policy['percent'] is not None:
                            discount = final_amount_before_payment_discount * (policy['percent'] / 100)
                            
                        payment_discount_amount = round(min(discount, policy['max_benefit']), 2)
                        
                        if payment_discount_amount > 0:
                            # PaymentDiscount 레코드 추가 준비 (나중에 payment_id 채움)
                            entities_to_add.append(PaymentDiscount(
                                payment_id='placeholder', 
                                policy_id=policy['id'],
                                applied_amount=payment_discount_amount
                            ))
                            final_amount = final_amount_before_payment_discount - payment_discount_amount

        # 최종 할인 금액 업데이트
        total_discount_amount += payment_discount_amount
        final_amount = max(0.0, final_amount)
        
        # Payment 테이블 생성
        payment = Payment(
            payment_type=payment_type_choice, 
            type_id=reservation_id if payment_type_choice == 0 else order_id,
            origin_amount=origin_amount,
            discount_total=total_discount_amount,
            amount=final_amount,
            status=1,
            created_at=completed_date - timedelta(minutes=random.randint(1, 5)),
            completed_at=completed_date
        )
        session.add(payment)
        session.flush()

        # PaymentDiscount의 payment_id 업데이트 (PaymentDiscount 객체가 생성되었다면)
        for entity in entities_to_add:
            if isinstance(entity, PaymentDiscount) and entity.payment_id == 'placeholder':
                entity.payment_id = payment.payment_id

        # PaymentDetail 생성
        if payment_method_choice == 'CARD':
            entities_to_add.append(PaymentCard(
                payment_id=payment.payment_id,
                card_company_code=selected_card_company_code,
                card_number=faker.numerify('####'),
                installment_months=random.choice([0,3,6]),
                card_approval_number=faker.numerify('##########')
            ))
        elif payment_method_choice == 'BANK':
            entities_to_add.append(PaymentBankTransfer(
                payment_id=payment.payment_id,
                bank_code='01201', # 임의의 은행 코드
                account_number=faker.bank_account_number(),
                account_holder_name=faker.name()[:12]
            ))
        else:
            entities_to_add.append(PaymentMobile(
                payment_id=payment.payment_id,
                carrier_code='00901', # 임의의 통신사 코드
                phone_number=faker.phone_number()[:13],
                approval_code=faker.numerify('##########')
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

    print(f"--- 최종 {num_records}개 통합 데이터 생성 완료 ---")

# -------------------------------------------------------------------------------------
# 6. 실행 진입점

if __name__ == '__main__':
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()

        print("기존 트랜잭션 데이터(예매, 스토어) 삭제 및 초기화 중...")
        # 역순 삭제 (FK 제약조건을 피하기 위해 모든 관련 테이블 삭제)
        tables_to_delete = ['reservation_seat_list', 'payment_discount', 'ticket_discount', 
                            'payment_card', 'payment_bank_transfer', 'payment_mobile', 
                            'payment', 'reservation_count', 'reservation_seat', 'reservation', 
                            'order'] 
        
        for table_name in tables_to_delete:
            session.execute(text(f"TRUNCATE TABLE {table_name}"))
        session.commit()

        # 데이터 생성 (예: 10만 건)
        # 80%는 예매 , 20%는 스토어 
        generate_dummy_data(session, 100000)

        session.close()

    except Exception as e:
        print(f"\n[오류 발생]: {e}")
        if 'session' in locals():
            session.rollback()