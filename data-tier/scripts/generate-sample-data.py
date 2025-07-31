#!/usr/bin/env python3
"""
Korean Customs Clearance System - Sample Data Generator
Generates additional Korean sample data for testing
"""

import mysql.connector
from mysql.connector import Error
import random
from datetime import datetime, timedelta
import argparse
import sys

# Sample Korean data
KOREAN_COMPANIES = [
    '삼성전자', '현대자동차', 'LG전자', 'SK하이닉스', 'POSCO홀딩스',
    '한국전력공사', '신한금융지주', '기아', 'LG화학', '셀트리온',
    '한화솔루션', '두산에너빌리티', '삼성물산', '현대모비스', 'KB금융지주',
    '현대중공업지주', '카카오', '네이버', '아모레퍼시픽', 'CJ제일제당'
]

FOREIGN_COMPANIES = [
    'Apple Inc.', 'Microsoft Corporation', 'Amazon.com Inc.', 'Google LLC',
    'Tesla Inc.', 'Samsung Electronics Co., Ltd.', 'Toyota Motor Corporation',
    'Sony Corporation', 'Nintendo Co., Ltd.', 'Canon Inc.',
    'Volkswagen AG', 'BMW AG', 'Mercedes-Benz Group AG', 'Siemens AG',
    'ASML Holding N.V.', 'TSMC', 'Intel Corporation', 'NVIDIA Corporation',
    'Meta Platforms Inc.', 'Netflix Inc.'
]

COUNTRIES = [
    '중국', '일본', '미국', '독일', '베트남', '대만', '싱가포르', '태국',
    '말레이시아', '인도네시아', '필리핀', '인도', '영국', '프랑스', '이탈리아',
    '스페인', '네덜란드', '벨기에', '스위스', '오스트리아'
]

PORTS = [
    '부산항', '인천항', '평택항', '울산항', '군산항', '목포항',
    '인천국제공항', '김포국제공항', '김해국제공항', '제주국제공항'
]

PRODUCT_DESCRIPTIONS = [
    ('8471300000', '휴대용 컴퓨터'),
    ('8517120000', '스마트폰'),
    ('8708100000', '자동차 범퍼'),
    ('3004200000', '항생제'),
    ('6403999000', '가죽신발'),
    ('6204620000', '여성용 바지'),
    ('0901210000', '원두커피'),
    ('2106909000', '식품 첨가물'),
    ('8501310000', '직류전동기'),
    ('8536500000', '스위치'),
    ('9013800000', '액정표시장치'),
    ('8525801000', 'LED 모니터'),
    ('3926909000', '플라스틱 제품'),
    ('7326909000', '철강 제품'),
    ('4011100000', '승용차용 타이어'),
    ('8471490000', '컴퓨터 부품'),
    ('8517629000', '통신 장비'),
    ('9018390000', '의료기기'),
    ('3304990000', '화장품'),
    ('2203000000', '맥주')
]

CURRENCIES = ['KRW', 'USD', 'EUR', 'JPY', 'CNY']
STATUSES = ['PENDING', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'CLEARED']

def generate_declaration_number():
    """Generate a unique declaration number"""
    year = datetime.now().year
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    sequence = random.randint(1, 9999)
    return f'D{year}{month:02d}{day:02d}{sequence:04d}'

def generate_random_date(days_back=30):
    """Generate a random date within the last N days"""
    start_date = datetime.now() - timedelta(days=days_back)
    random_days = random.randint(0, days_back)
    return start_date + timedelta(days=random_days)

def generate_declaration_data(count=10):
    """Generate sample declaration data"""
    declarations = []
    
    for i in range(count):
        declaration = {
            'declaration_number': generate_declaration_number(),
            'importer_name': random.choice(KOREAN_COMPANIES),
            'exporter_name': random.choice(FOREIGN_COMPANIES),
            'declaration_date': generate_random_date(),
            'total_value': round(random.uniform(100000, 50000000), 2),
            'currency': random.choice(CURRENCIES),
            'status': random.choice(STATUSES),
            'description': f"{random.choice(PRODUCT_DESCRIPTIONS)[1]} 및 관련 제품",
            'country_of_origin': random.choice(COUNTRIES),
            'port_of_entry': random.choice(PORTS)
        }
        declarations.append(declaration)
    
    return declarations

def generate_declaration_items(declaration_id, item_count=None):
    """Generate sample declaration items for a declaration"""
    if item_count is None:
        item_count = random.randint(1, 5)
    
    items = []
    for i in range(item_count):
        hs_code, description = random.choice(PRODUCT_DESCRIPTIONS)
        quantity = round(random.uniform(1, 1000), 3)
        unit_price = round(random.uniform(1000, 1000000), 2)
        
        item = {
            'declaration_id': declaration_id,
            'item_sequence': i + 1,
            'hs_code': hs_code,
            'item_description': description,
            'quantity': quantity,
            'unit_of_measure': random.choice(['EA', 'KG', 'MT', 'BOX', 'CARTON']),
            'unit_price': unit_price,
            'total_value': round(quantity * unit_price, 2),
            'country_of_origin': random.choice(COUNTRIES)
        }
        items.append(item)
    
    return items

def insert_declarations(connection, declarations):
    """Insert declarations into database"""
    cursor = connection.cursor()
    
    insert_query = """
        INSERT INTO declarations (
            declaration_number, importer_name, exporter_name, declaration_date,
            total_value, currency, status, description, country_of_origin, port_of_entry
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    inserted_ids = []
    for declaration in declarations:
        values = (
            declaration['declaration_number'],
            declaration['importer_name'],
            declaration['exporter_name'],
            declaration['declaration_date'],
            declaration['total_value'],
            declaration['currency'],
            declaration['status'],
            declaration['description'],
            declaration['country_of_origin'],
            declaration['port_of_entry']
        )
        
        cursor.execute(insert_query, values)
        inserted_ids.append(cursor.lastrowid)
    
    connection.commit()
    cursor.close()
    return inserted_ids

def insert_declaration_items(connection, items):
    """Insert declaration items into database"""
    cursor = connection.cursor()
    
    insert_query = """
        INSERT INTO declaration_items (
            declaration_id, item_sequence, hs_code, item_description,
            quantity, unit_of_measure, unit_price, total_value, country_of_origin
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    for item in items:
        values = (
            item['declaration_id'],
            item['item_sequence'],
            item['hs_code'],
            item['item_description'],
            item['quantity'],
            item['unit_of_measure'],
            item['unit_price'],
            item['total_value'],
            item['country_of_origin']
        )
        
        cursor.execute(insert_query, values)
    
    connection.commit()
    cursor.close()

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Generate Korean Customs Sample Data')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', type=int, default=3306, help='Database port')
    parser.add_argument('--database', default='customs_clearance_dev_db', help='Database name')
    parser.add_argument('--user', default='customs_user', help='Database user')
    parser.add_argument('--password', default='customs_password', help='Database password')
    parser.add_argument('--count', type=int, default=20, help='Number of declarations to generate')
    parser.add_argument('--items-per-declaration', type=int, help='Items per declaration (random if not specified)')
    
    args = parser.parse_args()
    
    print(f"Generating {args.count} sample declarations...")
    
    try:
        # Connect to database
        connection = mysql.connector.connect(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        
        # Generate declaration data
        declarations = generate_declaration_data(args.count)
        print(f"Generated {len(declarations)} declarations")
        
        # Insert declarations
        declaration_ids = insert_declarations(connection, declarations)
        print(f"Inserted {len(declaration_ids)} declarations into database")
        
        # Generate and insert items for each declaration
        total_items = 0
        for declaration_id in declaration_ids:
            items = generate_declaration_items(declaration_id, args.items_per_declaration)
            insert_declaration_items(connection, items)
            total_items += len(items)
        
        print(f"Inserted {total_items} declaration items into database")
        
        connection.close()
        print("Sample data generation completed successfully!")
        
    except Error as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()