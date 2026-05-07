// GET /api/records - 모든 기록 조회
export async function onRequestGet({ env }) {
    try {
        const DB = env.DB;

        if (!DB) {
            return new Response(JSON.stringify({
                error: 'D1 database not configured'
            }), {
                status: 500,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        // D1에서 모든 기록 조회 (최신순)
        const result = await DB.prepare(
            'SELECT id, content, created_at as createdAt FROM records ORDER BY created_at DESC'
        ).all();

        return new Response(JSON.stringify({ records: result.results || [] }), {
            status: 200,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        });

    } catch (error) {
        console.error('Error fetching records:', error);
        return new Response(JSON.stringify({
            error: 'Failed to fetch records',
            message: error.message
        }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// POST /api/records - 새 기록 생성
export async function onRequestPost({ request, env }) {
    try {
        const DB = env.DB;

        if (!DB) {
            return new Response(JSON.stringify({
                error: 'D1 database not configured'
            }), {
                status: 500,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        // 요청 본문 파싱
        const body = await request.json();
        const { content } = body;

        // 유효성 검사
        if (!content || typeof content !== 'string' || content.trim().length === 0) {
            return new Response(JSON.stringify({
                error: 'Content is required'
            }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        // 너무 긴 내용 제한 (10KB)
        if (content.length > 10000) {
            return new Response(JSON.stringify({
                error: 'Content too long (max 10KB)'
            }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        // 새 기록 생성
        const record = {
            id: crypto.randomUUID(),
            content: content.trim(),
            createdAt: new Date().toISOString()
        };

        // D1에 저장
        await DB.prepare(
            'INSERT INTO records (id, content, created_at) VALUES (?, ?, ?)'
        ).bind(record.id, record.content, record.createdAt).run();

        return new Response(JSON.stringify({ record }), {
            status: 201,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        });

    } catch (error) {
        console.error('Error creating record:', error);
        return new Response(JSON.stringify({
            error: 'Failed to create record',
            message: error.message
        }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// OPTIONS - CORS preflight
export async function onRequestOptions() {
    return new Response(null, {
        status: 204,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    });
}
