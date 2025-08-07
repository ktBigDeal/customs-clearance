# Data Tier - Database Layer

관세청 통관시스템의 데이터 계층입니다. MySQL과 Neo4j를 함께 사용하는 폴리글랏 퍼시스턴스 아키텍처를 구현합니다.

## 구조

```
data-tier/
├── docker-compose.yml          # MySQL & Neo4j 컨테이너 설정
├── mysql/                      # MySQL 관계형 데이터베이스
│   ├── config/
│   │   └── my.cnf             # MySQL 설정 (한글 지원)
│   └── init/
│       ├── 01-schema.sql      # 데이터베이스 스키마
│       └── 02-seed-data.sql   # 초기 테스트 데이터
├── neo4j/                      # Neo4j 그래프 데이터베이스
│   ├── conf/
│   │   └── neo4j.conf         # Neo4j 설정
│   ├── import/
│   │   └── init.cypher        # 초기 그래프 데이터
│   ├── data/                  # 데이터 저장소 (바인드 마운트)
│   ├── logs/                  # 로그 저장소 (바인드 마운트)
│   └── plugins/               # GDS 플러그인 저장소 (바인드 마운트)
├── scripts/
│   ├── test-connection.py     # MySQL 연결 테스트
│   └── neo4j-setup.sh         # Neo4j 관리 스크립트
└── README.md
```

## 설치 및 실행

### 1. 전체 데이터베이스 스택 실행

```bash
cd data-tier
docker-compose up -d
```

### 2. 개별 서비스 실행

```bash
# MySQL만 실행
docker-compose up -d mysql phpmyadmin

# Neo4j만 실행
docker-compose up -d neo4j
```

### 3. 서비스 확인

#### MySQL 관계형 데이터베이스
- **MySQL**: http://localhost:3306
- **phpMyAdmin**: http://localhost:8081

#### Neo4j 그래프 데이터베이스
- **Neo4j Browser**: http://localhost:7474
- **Bolt Protocol**: bolt://localhost:7687

### 4. 연결 정보

#### MySQL
- **Host**: localhost
- **Port**: 3306
- **Database**: customs_clearance
- **Username**: customs_user
- **Password**: customs_pass

#### Neo4j
- **Host**: localhost
- **HTTP Port**: 7474
- **Bolt Port**: 7687
- **Username**: neo4j
- **Password**: neo4j123

## 데이터베이스 아키텍처

### 폴리글랏 퍼시스턴스 설계

이 시스템은 각 데이터베이스의 강점을 활용하는 폴리글랏 퍼시스턴스 패턴을 사용합니다:

#### MySQL (관계형 데이터)
- **용도**: 트랜잭션 데이터, 구조화된 비즈니스 데이터
- **데이터**: 사용자, 신고서, 첨부파일, 감사 로그

#### Neo4j (그래프 데이터)
- **용도**: 관계 분석, 네트워크 분석, 복잡한 쿼리
- **데이터**: 무역 관계, 공급망 분석, 리스크 분석, 관세 규칙

### MySQL 스키마

#### 주요 테이블
1. **users** - 사용자 관리
2. **declarations** - 통관 신고서
3. **attachments** - 첨부파일
4. **declaration_history** - 신고서 이력
5. **codes** - 코드 관리 (국가, 통화, HS코드 등)

#### 문자셋 설정
- 한글 지원을 위해 **utf8mb4** 사용
- 시간대: Asia/Seoul (+09:00)

### Neo4j 그래프 스키마

#### 주요 노드 타입
1. **Declaration** - 신고서
2. **Company** - 회사/기업
3. **Product** - 제품 (HS코드 기반)
4. **Country** - 국가
5. **TradeAgreement** - 무역협정

#### 주요 관계 타입
1. **DECLARED_BY** - 신고서 ↔ 회사
2. **CONTAINS** - 신고서 ↔ 제품
3. **FROM/TO** - 신고서 ↔ 국가 (수출입)
4. **LOCATED_IN** - 회사 ↔ 국가
5. **BETWEEN** - 무역협정 ↔ 국가

#### GDS (Graph Data Science) 기능
- **Community Edition 지원**: GDS 플러그인이 Community Edition에서도 사용 가능
- **제한사항**: 
  - 최대 4개 CPU 코어 병렬 처리
  - 모델 카탈로그 최대 3개 모델
  - 일부 Enterprise 전용 알고리즘 제외
- **사용 가능 알고리즘**: 
  - 중심성 분석 (PageRank, Degree, Betweenness, Closeness)
  - 커뮤니티 탐지 (Weakly Connected Components)
  - 경로 찾기 (Shortest Path, Dijkstra)
  - 유사성 분석 (Node Similarity)
  - 그래프 통계 (Triangle Count, Clustering Coefficient)

## 테스트

### MySQL 연결 테스트

```bash
# 의존성 설치
pip install mysql-connector-python

# 연결 테스트 실행
python scripts/test-connection.py
```

### Neo4j 초기화 및 테스트

```bash
# Neo4j 관리 스크립트 실행 권한 부여 (Linux/macOS)
chmod +x scripts/neo4j-setup.sh

# Neo4j 초기화 (샘플 데이터 포함)
scripts/neo4j-setup.sh init

# Neo4j 상태 확인
scripts/neo4j-setup.sh status

# Neo4j 연결 테스트 및 샘플 쿼리 실행
scripts/neo4j-setup.sh test

# GDS (Graph Data Science) 기능 테스트
scripts/neo4j-setup.sh gds
```

### 애플리케이션에서 연결

#### Spring Boot - MySQL 연결

`application.yml` 설정:

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/customs_clearance?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Seoul
    username: customs_user
    password: customs_pass
    driver-class-name: com.mysql.cj.jdbc.Driver
```

#### Python - Neo4j 연결

```python
from neo4j import GraphDatabase

# Neo4j 연결
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "neo4j123")
)

# 샘플 쿼리
def get_declarations_by_company(company_name):
    with driver.session() as session:
        result = session.run(
            "MATCH (d:Declaration)-[:DECLARED_BY]->(c:Company) "
            "WHERE c.name CONTAINS $company_name "
            "RETURN d.declaration_id, d.status, d.total_value",
            company_name=company_name
        )
        return [record.data() for record in result]
```

#### Java - Neo4j 연결

```java
@Configuration
public class Neo4jConfig {
    
    @Bean
    public Driver neo4jDriver() {
        return GraphDatabase.driver(
            "bolt://localhost:7687",
            AuthTokens.basic("neo4j", "neo4j123")
        );
    }
}
```

## 초기 데이터

### MySQL 테스트 데이터

#### 테스트 사용자
- **admin** (관리자): admin@customs.go.kr / admin123
- **officer1** (검사관): officer1@customs.go.kr / officer123  
- **user1** (사용자): user1@company.com / user123

#### 테스트 신고서
- 3건의 샘플 신고서 (수입/수출/경유)
- 다양한 상태 (제출, 검토중, 승인)

### Neo4j 테스트 데이터

#### 그래프 데이터
- **국가**: 한국, 미국, 중국, 일본, 독일
- **회사**: 삼성전자, LG전자, Apple Inc.
- **제품**: 스마트폰, LED모니터, 노트북 (HS코드 포함)
- **무역협정**: 한미FTA, RCEP
- **신고서**: 2건의 샘플 신고서 (수입/수출)

#### 관계 데이터
- 신고서 ↔ 회사 관계
- 신고서 ↔ 제품 관계
- 신고서 ↔ 국가 관계 (수출입)
- 회사 ↔ 국가 관계 (소재지)
- 무역협정 ↔ 국가 관계

## 관리

### MySQL 관리

#### 백업
```bash
docker exec customs-mysql mysqldump -u customs_user -p customs_clearance > mysql_backup.sql
```

#### 복원
```bash
docker exec -i customs-mysql mysql -u customs_user -p customs_clearance < mysql_backup.sql
```

#### 로그 확인
```bash
docker logs customs-mysql
```

### Neo4j 관리

#### 백업
```bash
# 관리 스크립트 사용
scripts/neo4j-setup.sh backup

# 또는 직접 백업
docker exec customs-neo4j neo4j-admin dump --database=neo4j --to=/tmp/neo4j_backup.dump
docker cp customs-neo4j:/tmp/neo4j_backup.dump ./neo4j_backup.dump
```

#### 데이터 초기화
```bash
# 모든 데이터 삭제 (주의!)
scripts/neo4j-setup.sh clean

# 샘플 데이터 재생성
scripts/neo4j-setup.sh init
```

#### 로그 확인
```bash
docker logs customs-neo4j
```

## 유용한 Neo4j 쿼리 예제

### 기본 분석 쿼리

```cypher
// 1. 모든 노드 타입별 개수
MATCH (n) RETURN labels(n) as NodeType, count(n) as Count ORDER BY Count DESC

// 2. 회사별 신고서 개수
MATCH (d:Declaration)-[:DECLARED_BY]->(c:Company)
RETURN c.name, count(d) as DeclarationCount
ORDER BY DeclarationCount DESC

// 3. 국가간 무역량 분석
MATCH (d:Declaration)-[:FROM]->(origin:Country), (d)-[:TO]->(dest:Country)
RETURN origin.name as From, dest.name as To, 
       count(d) as TradeCount, sum(d.total_value) as TotalValue
ORDER BY TotalValue DESC

// 4. HS코드별 거래 빈도
MATCH (d:Declaration)-[:CONTAINS]->(p:Product)
RETURN p.hs_code, p.name, count(d) as DeclarationCount,
       sum(toFloat(split(toString(d.total_value), '.')[0])) as TotalValue
ORDER BY DeclarationCount DESC
```

### GDS (Graph Data Science) 분석 쿼리

```cypher
// GDS 버전 확인
RETURN gds.version() AS gdsVersion;

// 1. 그래프 프로젝션 생성 (무역 네트워크)
CALL gds.graph.project(
    'customs-trade-network',
    ['Country', 'Company', 'Declaration'],
    ['FROM', 'TO', 'DECLARED_BY']
) YIELD graphName, nodeCount, relationshipCount;

// 2. PageRank - 무역 네트워크에서 영향력 있는 국가/회사 찾기
CALL gds.pageRank.stream('customs-trade-network')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS entity,
       labels(gds.util.asNode(nodeId))[0] AS entityType,
       score AS influence
ORDER BY score DESC LIMIT 10;

// 3. Degree Centrality - 가장 많은 연결을 가진 노드
CALL gds.degree.stream('customs-trade-network')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS entity,
       labels(gds.util.asNode(nodeId))[0] AS entityType,
       score AS connectionCount
ORDER BY score DESC LIMIT 10;

// 4. Betweenness Centrality - 중개 역할을 하는 무역 허브
CALL gds.betweenness.stream('customs-trade-network')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS entity,
       labels(gds.util.asNode(nodeId))[0] AS entityType,
       score AS bridgeScore
ORDER BY score DESC LIMIT 10;

// 5. Node Similarity - 유사한 거래 패턴을 가진 회사들
CALL gds.nodeSimilarity.stream('customs-trade-network')
YIELD node1, node2, similarity
WHERE labels(gds.util.asNode(node1))[0] = 'Company' 
  AND labels(gds.util.asNode(node2))[0] = 'Company'
RETURN gds.util.asNode(node1).name AS company1,
       gds.util.asNode(node2).name AS company2,
       similarity
ORDER BY similarity DESC LIMIT 10;

// 6. Weakly Connected Components - 연결된 무역 클러스터
CALL gds.wcc.stream('customs-trade-network')
YIELD nodeId, componentId
RETURN componentId, 
       collect(gds.util.asNode(nodeId).name) AS cluster,
       count(*) AS clusterSize
ORDER BY clusterSize DESC;

// 7. 그래프 정리
CALL gds.graph.drop('customs-trade-network') YIELD graphName;
```

### 기본 Cypher 분석 쿼리

```cypher
// 8. 국가간 무역량 분석
MATCH (origin:Country)<-[:FROM]-(d:Declaration)-[:TO]->(dest:Country)
RETURN origin.name as From, dest.name as To, 
       count(d) as TradeCount, sum(d.total_value) as TotalValue,
       avg(d.total_value) as AvgValue
ORDER BY TotalValue DESC;

// 9. 회사별 무역 허브 분석
MATCH (c:Company)<-[:DECLARED_BY]-(d:Declaration)
MATCH (d)-[:FROM|TO]->(country:Country)
RETURN c.name, count(DISTINCT country) as CountriesTraded,
       count(d) as TotalDeclarations,
       sum(d.total_value) as TotalTradeValue
ORDER BY CountriesTraded DESC, TotalTradeValue DESC;

// 10. 최단 경로 찾기 (기본 Cypher)
MATCH path = shortestPath((c1:Country)-[*]-(c2:Country))
WHERE c1.country_code = 'KR' AND c2.country_code = 'US'
RETURN path, length(path) as PathLength;
```