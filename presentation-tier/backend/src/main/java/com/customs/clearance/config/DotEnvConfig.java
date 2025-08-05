package com.customs.clearance.config;

import org.springframework.context.annotation.Bean;
import io.github.cdimascio.dotenv.Dotenv;
import org.springframework.context.annotation.Configuration;
/**
 * DotEnvConfig.java
 * 
 * 이 클래스는 Dotenv 라이브러리를 사용하여 .env 파일에서 환경 변수를 로드합니다.
 * 
 * <p>Dotenv 라이브러리는 애플리케이션의 환경 설정을 외부 파일에서 관리할 수 있게 해줍니다.
 * 이 설정을 통해 데이터베이스 연결 정보, API 키 등 민감한 정보를 코드에 하드코딩하지 않고 안전하게 관리할 수 있습니다.</p>
 * 
 * <p>이 클래스는 Spring의 @Configuration 어노테이션을 사용하여 스프링 컨테이너에 빈으로 등록됩니다.
 * 빈으로 등록된 Dotenv 객체는 애플리케이션 전역에서 사용할 수 있습니다.</p>
 * 
 * <p>이 설정은 .env 파일이 존재하지 않을 경우에도 애플리케이션이 정상적으로 동작하도록 ignoreIfMissing() 메서드를 사용하여 설정되어 있습니다.</p>
 * 
 * 
 * 이 클래스는 Spring Boot 애플리케이션에서 환경 변수를 관리하는 데 유용하며,
 * 개발, 테스트, 배포 환경에서 일관된 설정을 유지하는 데 도움을 줍니다. 
 * 
 * <p>이 클래스는 다음과 같은 환경 변수를 로드합니다:</p>
 * <ul>
 *  <li>JWT_SECRET: JWT 토큰 서명에 사용되는 비밀 키</li>  
 *  <li>DB_HOST: 데이터베이스 호스트</li>
 *  <li>DB_PORT: 데이터베이스 포트</li>
 *  <li>DB_NAME: 데이터베이스 이름</li>
 *  <li>DB_USERNAME: 데이터베이스 사용자 이름</li>
 *  <li>DB_PASSWORD: 데이터베이스 비밀번호</li>
 *  <li>EXTERNAL_API_URL: 외부 API URL</li>
 *  <li>SERVER_PORT: 서버 포트</li>
 * </ul>
 * 
 * 
 * @author Customs Clearance Team
 * @version 1.0.0
 */
@Configuration
public class DotEnvConfig {

    @Bean
    public Dotenv dotenv() {
        // .env 파일을 읽어서 환경변수로 사용
        return Dotenv.configure().directory("./")
                .ignoreIfMissing() // .env 파일이 없어도 에러 발생 안함
                .load();
    }
}