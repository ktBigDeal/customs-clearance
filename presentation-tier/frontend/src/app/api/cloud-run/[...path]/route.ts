import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleRequest(request, params, 'GET');
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleRequest(request, params, 'POST');
}

export async function PUT(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleRequest(request, params, 'PUT');
}

export async function DELETE(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleRequest(request, params, 'DELETE');
}

export async function PATCH(request: NextRequest, { params }: { params: { path: string[] } }) {
  return handleRequest(request, params, 'PATCH');
}

async function handleRequest(
  request: NextRequest,
  params: { path: string[] },
  method: string
) {
  const { searchParams } = new URL(request.url);
  let path = params.path?.join('/') || '';
  
  // 요청한 서비스에 따라 적절한 Cloud Run URL 선택
  let cloudRunUrl = '';
  
  // 경로에 따라 서비스 라우팅
  console.log(`🔍 요청 경로: ${path}`);
  console.log(`🔍 환경변수 CLOUD_RUN_HSCODE_URL: ${process.env.CLOUD_RUN_HSCODE_URL}`);
  
  if (path.startsWith('chatbot') || path.startsWith('chat')) {
    cloudRunUrl = process.env.CLOUD_RUN_CHATBOT_URL || '';
  } else if (path.startsWith('ocr')) {
    cloudRunUrl = process.env.CLOUD_RUN_OCR_URL || '';
  } else if (path.startsWith('report')) {
    cloudRunUrl = process.env.CLOUD_RUN_REPORT_URL || '';
  } else if (path.startsWith('hscode')) {
    cloudRunUrl = process.env.CLOUD_RUN_HSCODE_URL || '';
    console.log(`✅ hscode 경로 매치! URL: ${cloudRunUrl}`);
    // hscode 접두사 제거하여 올바른 API 경로로 전달
    path = path.replace('hscode/', '');
    console.log(`🔄 변경된 경로: ${path}`);
  } else if (path.startsWith('us-convert')) {
    cloudRunUrl = process.env.CLOUD_RUN_US_CONVERT_URL || '';
    // us-convert 접두사 제거하여 올바른 API 경로로 전달
    path = path.replace('us-convert/', '');
  } else if (path.startsWith('gateway') || path.startsWith('ai')) {
    cloudRunUrl = process.env.CLOUD_RUN_GATEWAY_URL || '';
  } else {
    // 기본값으로 게이트웨이 사용
    console.log(`⚠️ 기본 라우팅 사용: ${path}`);
    cloudRunUrl = process.env.CLOUD_RUN_GATEWAY_URL || '';
  }

  if (!cloudRunUrl) {
    return NextResponse.json(
      { error: '서비스 URL이 설정되지 않았습니다.', path, service: path.split('/')[0] },
      { status: 500 }
    );
  }

  try {
    const queryString = searchParams.toString();
    const fullUrl = `${cloudRunUrl}/${path}${queryString ? `?${queryString}` : ''}`;

    const requestInit: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        // 원본 요청의 필요한 헤더들 전달
        ...(request.headers.get('authorization') && {
          authorization: request.headers.get('authorization')!,
        }),
        ...(request.headers.get('user-agent') && {
          'user-agent': request.headers.get('user-agent')!,
        }),
      },
    };

    // GET 요청이 아닌 경우에만 body 추가
    if (method !== 'GET' && method !== 'HEAD') {
      try {
        const body = await request.text();
        if (body) {
          requestInit.body = body;
        }
      } catch (error) {
        console.log('요청 body 파싱 중 오류 (무시):', error);
      }
    }

    console.log(`Proxying ${method} request to:`, fullUrl);
    
    // Cloud Run API는 마지막 슬래시가 필요할 수 있음
    const finalUrl = fullUrl.endsWith('/') ? fullUrl : fullUrl + '/';
    console.log(`Final URL with slash:`, finalUrl);
    
    const response = await fetch(finalUrl, requestInit);
    
    const responseHeaders = new Headers();
    // CORS 헤더 설정
    responseHeaders.set('Access-Control-Allow-Origin', '*');
    responseHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS');
    responseHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    
    // 원본 응답의 Content-Type 보존
    const contentType = response.headers.get('content-type');
    if (contentType) {
      responseHeaders.set('Content-Type', contentType);
    }

    // JSON 응답인 경우
    if (contentType?.includes('application/json')) {
      const data = await response.json();
      return NextResponse.json(data, {
        status: response.status,
        headers: responseHeaders,
      });
    }
    
    // 텍스트 응답인 경우
    if (contentType?.includes('text/')) {
      const text = await response.text();
      return new NextResponse(text, {
        status: response.status,
        headers: responseHeaders,
      });
    }
    
    // 바이너리 응답인 경우
    const buffer = await response.arrayBuffer();
    return new NextResponse(buffer, {
      status: response.status,
      headers: responseHeaders,
    });
    
  } catch (error) {
    console.error('Proxy request failed:', error);
    return NextResponse.json(
      { 
        error: 'Cloud Run 서비스 요청 중 오류가 발생했습니다.',
        details: error instanceof Error ? error.message : 'Unknown error',
        requestedUrl: `${cloudRunUrl}/${path}`,
        service: path.split('/')[0]
      },
      { status: 500 }
    );
  }
}
