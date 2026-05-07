// DELETE /api/records/:id - 기록 삭제
export async function onRequestDelete({ params, env }) {
    try {
        const DB = env.DB;
        const { id } = params;

        if (!DB) {
            return new Response(JSON.stringify({
                error: 'D1 database not configured'
            }), {
                status: 500,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        if (!id) {
            return new Response(JSON.stringify({
                error: 'Record ID is required'
            }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        // 기록이 존재하는지 확인
        const existing = await DB.prepare(
            'SELECT id FROM records WHERE id = ?'
        ).bind(id).first();

        if (!existing) {
            return new Response(JSON.stringify({
                error: 'Record not found'
            }), {
                status: 404,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        // D1에서 삭제
        await DB.prepare(
            'DELETE FROM records WHERE id = ?'
        ).bind(id).run();

        return new Response(JSON.stringify({
            success: true,
            message: 'Record deleted'
        }), {
            status: 200,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        });

    } catch (error) {
        console.error('Error deleting record:', error);
        return new Response(JSON.stringify({
            error: 'Failed to delete record',
            message: error.message
        }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// PUT /api/records/:id - 기록 수정
export async function onRequestPut({ params, request, env }) {
    try {
        const DB = env.DB;
        const { id } = params;

        if (!DB) {
            return new Response(JSON.stringify({
                error: 'D1 database not configured'
            }), {
                status: 500,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        if (!id) {
            return new Response(JSON.stringify({
                error: 'Record ID is required'
            }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        const body = await request.json();
        const { content } = body;

        if (!content || typeof content !== 'string' || content.trim().length === 0) {
            return new Response(JSON.stringify({
                error: 'Content is required'
            }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        if (content.length > 10000) {
            return new Response(JSON.stringify({
                error: 'Content too long (max 10KB)'
            }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        const existing = await DB.prepare(
            'SELECT id FROM records WHERE id = ?'
        ).bind(id).first();

        if (!existing) {
            return new Response(JSON.stringify({
                error: 'Record not found'
            }), {
                status: 404,
                headers: { 'Content-Type': 'application/json' }
            });
        }

        await DB.prepare(
            'UPDATE records SET content = ? WHERE id = ?'
        ).bind(content.trim(), id).run();

        const updated = await DB.prepare(
            'SELECT id, content, created_at as createdAt FROM records WHERE id = ?'
        ).bind(id).first();

        return new Response(JSON.stringify({
            record: updated
        }), {
            status: 200,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        });

    } catch (error) {
        console.error('Error updating record:', error);
        return new Response(JSON.stringify({
            error: 'Failed to update record',
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
            'Access-Control-Allow-Methods': 'PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    });
}
