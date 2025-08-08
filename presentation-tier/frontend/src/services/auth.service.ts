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
  private baseURL = 'http://localhost:8080/api/v1/user';

  /**
   * 회원가입
   */
  async register(userData: RegisterRequest): Promise<void> {
    const response = await fetch(`${this.baseURL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(errorData || '회원가입에 실패했습니다.');
    }
  }

  /**
   * 로그인
   */
  async login(username: string, password: string, role: string): Promise<string> {
    const response = await fetch(
      `${this.baseURL}/login/${role.toLowerCase()}?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
      {
        method: 'POST',
      }
    );

    if (!response.ok) {
      throw new Error('로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.');
    }

    const token = await response.text();
    return token;
  }

  /**
   * 사용자 프로필 조회
   */
  async getUserProfile(username: string): Promise<UserResponse> {
    const token = this.getToken();
    if (!token) {
      throw new Error('로그인이 필요합니다.');
    }

    const response = await fetch(`${this.baseURL}/${username}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
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
   * 사용자 정보 수정
   */
  async updateUser(username: string, userData: UpdateUserRequest): Promise<UserResponse> {
    const token = this.getToken();
    if (!token) {
      throw new Error('로그인이 필요합니다.');
    }

    const response = await fetch(`${this.baseURL}/${username}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
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
      // JWT 토큰 디코딩 (페이로드 부분)
      const payload = JSON.parse(atob(token.split('.')[1]));
      return {
        username: payload.sub,
        role: payload.role
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
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      
      // 토큰 만료 확인
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
        lastLogin: profile.lastLogin
      };
    } catch (error) {
      console.error('사용자 정보 조회 실패:', error);
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
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
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