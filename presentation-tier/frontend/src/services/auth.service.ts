/**
 * 인증 관련 API 서비스
 * 백엔드 JWT 인증 시스템과 연동
 */

export interface RegisterRequest {
  username: string;
  password: string;
  name: string;
  email: string;
  role: 'ADMIN' | 'USER';
  company?: string;
}

export interface UserResponse {
  id: number;
  username: string;
  name: string;
  email: string;
  role: string;
  enabled: boolean;
  company?: string;
  lastLogin?: string;
}

export interface UpdateUserRequest {
  name: string;
  email: string;
  password?: string;
  company?: string;
}

export interface AuthUser {
  username: string;
  name: string;
  email: string;
  role: string;
  token: string;
  company?: string;
  lastLogin?: string;
}

class AuthService {
  // 인증 관련 (로그인/회원가입)
  private authURL = 'https://customs-backend-java.up.railway.app/user';  

  // 사용자 관리 (프로필 조회/수정)
  private userURL = '/api/user';
  
  // 관리자 기능
  private adminURL = '/api/user/admin';  // 관리자 전용 기능

  /**
   * 사용자 로그인
   */
  async loginUser(username: string, password: string): Promise<string> {
    const response = await fetch(`${this.authURL}/login/user`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error('사용자 로그인에 실패했습니다.');
    }

    const token = await response.text();
    this.setToken(token);
    return token;
  }

  /**
   * 관리자 로그인
   */
  async loginAdmin(username: string, password: string): Promise<string> {
    const response = await fetch(`${this.authURL}/login/admin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      throw new Error('관리자 로그인에 실패했습니다.');
    }

    const token = await response.text();
    this.setToken(token);
    return token;
  }

  /**
   * 통합 로그인 메서드 (기존 호환성 유지)
   */
  async login(username: string, password: string, role: string): Promise<string> {
    if (role.toLowerCase() === 'admin') {
      return this.loginAdmin(username, password);
    } else {
      return this.loginUser(username, password);
    }
  }

  /**
   * 관리자 기능 - 사용자 정보 수정
   */
  async updateUserByAdmin(userId: string, userData: UpdateUserRequest): Promise<UserResponse> {
    const token = this.getToken();
    if (!token) throw new Error('로그인이 필요합니다.');

    // 백엔드 경로: PATCH /user/admin/{userId}
    const response = await fetch(`${this.adminURL}/${userId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.logout();
        throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
      }
      throw new Error('사용자 정보 수정에 실패했습니다.');
    }

    return await response.json();
  }

  /**
   * 일반 사용자 정보 수정
   */
  async updateUser(userId: string, userData: UpdateUserRequest): Promise<UserResponse> {
    const token = this.getToken();
    if (!token) throw new Error('로그인이 필요합니다.');

    // 백엔드 경로: PUT /user/{userId}
    const response = await fetch(`${this.userURL}/${userId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.logout();
        throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
      }
      throw new Error('사용자 정보 수정에 실패했습니다.');
    }

    return await response.json();
  }
  /**
   * 회원가입
   */
  async register(userData: RegisterRequest): Promise<void> {
    const response = await fetch(`${this.userURL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(errorData || '회원가입에 실패했습니다.');
    }
  }



  /**
   * 사용자 프로필 조회
   */
  async getUserProfile(username: string): Promise<UserResponse> {
    const token = this.getToken();
    if (!token) throw new Error('로그인이 필요합니다.');

    // 백엔드에 GET /user/{userId} 엔드포인트가 있다고 가정
    const response = await fetch(`${this.userURL}/${username}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.logout();
        throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
      }
      throw new Error('사용자 정보를 가져오는데 실패했습니다.');
    }

    return await response.json();
  }




  /**
   * 토큰 저장
   */
  setToken(token: string): void {
    localStorage.setItem('jwtToken', token);
  }

  /**
   * 토큰 가져오기
   */
  getToken(): string | null {
    return localStorage.getItem('jwtToken');
  }

  /**
   * 토큰에서 사용자 정보 추출
   */
  getUserFromToken(): { username: string; role: string } | null {
    const token = this.getToken();
    if (!token) return null;

    try {
      const parts = token.split('.');
      if (parts.length !== 3 || !parts[1]) {  // parts[1] 존재 여부 확인
        throw new Error('유효하지 않은 JWT 토큰 형식');
      }
      const payloadBase64Url = parts[1];
      const base64 = payloadBase64Url.replace(/-/g, '+').replace(/_/g, '/');
      const decodedPayload = atob(base64 + '=='.slice(0, (4 - (base64.length % 4)) % 4));
      
      const payload = JSON.parse(decodedPayload);
      return {
        username: payload.sub,
        role: payload.role,
      };
    } catch (error) {
      console.error('토큰 디코딩 실패:', error);
      this.logout();
      return null;
    }
  }

  /**
   * 로그인 상태 확인
   */
  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;

    try {
      const parts = token.split('.');
      if (parts.length !== 3 || !parts[1]) {
        throw new Error('유효하지 않은 JWT 토큰 형식');
      }
      const payloadBase64Url = parts[1];
      const base64 = payloadBase64Url.replace(/-/g, '+').replace(/_/g, '/');
      const decodedPayload = atob(base64 + '=='.slice(0, (4 - (base64.length % 4)) % 4));

      const payload = JSON.parse(decodedPayload);
      const currentTime = Date.now() / 1000;

      if (payload.exp < currentTime) {
        this.logout();
        return false;
      }

      return true;
    } catch (error) {
      console.error('토큰 검증 실패:', error);
      this.logout();
      return false;
    }
  }

  /**
   * 현재 로그인한 사용자 정보 가져오기
   */
  async getCurrentUser(): Promise<AuthUser | null> {
    const userInfo = this.getUserFromToken();
    if (!userInfo) return null;

    try {
      const profile = await this.getUserProfile(userInfo.username);
      return {
        username: profile.username,
        name: profile.name,
        email: profile.email,
        role: profile.role,
        token: this.getToken()!,
        company: profile.company,
        lastLogin: profile.lastLogin,
      };
    } catch (error) {
      console.error('사용자 정보 조회 실패:', error);
      return null;
    }
  }

  /**
   * 현재 로그인한 사용자의 ID를 가져오기
   * JWT 토큰에서 username을 추출한 후, 백엔드 API를 통해 사용자 ID를 조회합니다.
   * 
   * @returns {Promise<number | null>} 사용자 ID 또는 null (인증되지 않은 경우)
   * 
   * @example
   * ```typescript
   * const userId = await authService.getCurrentUserId();
   * if (userId) {
   *   // 챗봇 API 호출 시 사용
   *   const response = await chatbotApiClient.sendMessage({
   *     message: '안녕하세요',
   *     user_id: userId
   *   });
   * }
   * ```
   */
  async getCurrentUserId(): Promise<number | null> {
    const userInfo = this.getUserFromToken();
    if (!userInfo) {
      console.debug('[AuthService] JWT 토큰에서 사용자 정보를 가져올 수 없습니다');
      return null;
    }

    try {
      // username으로 사용자 프로필 조회해서 ID 가져오기
      const profile = await this.getUserProfile(userInfo.username);
      console.debug('[AuthService] 사용자 ID 조회 성공:', {
        username: userInfo.username,
        userId: profile.id
      });
      return profile.id;
    } catch (error) {
      console.error('[AuthService] 사용자 ID 조회 실패:', error);
      return null;
    }
  }

  /**
   * 로그아웃
   */
  logout(): void {
    localStorage.removeItem('jwtToken');
    localStorage.removeItem('user_type');
    localStorage.removeItem('user_email');
  }

  /**
   * 권한 확인
   */
  hasRole(requiredRole: string): boolean {
    const userInfo = this.getUserFromToken();
    if (!userInfo) return false;

    // ADMIN은 모든 권한 보유
    if (userInfo.role === 'ADMIN') return true;

    return userInfo.role === requiredRole;
  }

  /**
   * API 요청에 자동으로 인증 헤더 추가하는 fetch wrapper
   */
  async authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const token = this.getToken();
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // 401 에러 시 자동 로그아웃
    if (response.status === 401) {
      this.logout();
      window.location.href = '/login';
    }

    return response;
  }
}

export const authService = new AuthService();