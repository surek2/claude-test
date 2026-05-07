/**
 * Cloudflare Pages Functions - 구독 API
 * POST /api/subscribe
 */

// CORS 헤더 설정
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// 이메일 유효성 검사
function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

export async function onRequestOptions() {
  return new Response(null, {
    status: 204,
    headers: corsHeaders,
  });
}

export async function onRequestPost({ request, env }) {
  try {
    // 요청 본문 파싱
    const { email } = await request.json();

    // 이메일 유효성 검사
    if (!email || !isValidEmail(email)) {
      return new Response(
        JSON.stringify({ 
          success: false, 
          error: '올바른 이메일 주소를 입력해주세요.' 
        }),
        {
          status: 400,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        }
      );
    }

    // D1 데이터베이스에 구독자 추가
    const db = env.DB;
    
    try {
      // 중복 확인
      const existing = await db
        .prepare('SELECT * FROM subscribers WHERE email = ?')
        .bind(email)
        .first();

      if (existing) {
        return new Response(
          JSON.stringify({ 
            success: false, 
            error: '이미 구독 중인 이메일입니다.' 
          }),
          {
            status: 409,
            headers: {
              'Content-Type': 'application/json',
              ...corsHeaders,
            },
          }
        );
      }

      // 새 구독자 추가
      await db
        .prepare('INSERT INTO subscribers (email, subscribed_at, status) VALUES (?, datetime("now"), ?)')
        .bind(email, 'active')
        .run();

      return new Response(
        JSON.stringify({ 
          success: true, 
          message: '구독이 완료되었습니다!' 
        }),
        {
          status: 201,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        }
      );

    } catch (dbError) {
      console.error('Database error:', dbError);
      return new Response(
        JSON.stringify({ 
          success: false, 
          error: '데이터베이스 오류가 발생했습니다.' 
        }),
        {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        }
      );
    }

  } catch (error) {
    console.error('Error:', error);
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: '구독 처리 중 오류가 발생했습니다.' 
      }),
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders,
        },
      }
    );
  }
}

