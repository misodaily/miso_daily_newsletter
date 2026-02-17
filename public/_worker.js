
export default {
    async fetch(request, env, ctx) {
        const url = new URL(request.url);

        // API Handling: /api/subscribe
        if (url.pathname === "/api/subscribe" && request.method === "POST") {
            try {
                const formData = await request.formData();
                const email = formData.get("email");
                const channel = formData.get("channel");
                const marketingConsent = formData.get("marketing_consent") === "on";

                if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                    return new Response("Valid email is required", { status: 400 });
                }

                const supabaseUrl = env.SUPABASE_URL;
                const supabaseKey = env.SUPABASE_KEY;

                if (!supabaseUrl || !supabaseKey) {
                    return new Response("Supabase configuration missing", { status: 500 });
                }

                // Insert into Supabase 'subscribers' table via REST API
                const response = await fetch(`${supabaseUrl}/rest/v1/subscribers`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "apikey": supabaseKey,
                        "Authorization": `Bearer ${supabaseKey}`,
                        "Prefer": "return=minimal",
                    },
                    body: JSON.stringify({
                        email: email,
                        channel: channel,
                        marketing_consent: marketingConsent,
                    }),
                });

                // Helper to generate HTML response
                const createHtmlResponse = (message) => {
                    return `
                    <!DOCTYPE html>
                    <html lang="ko">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Miso Daily Subscription</title>
                        <style>
                            body { font-family: 'Apple SD Gothic Neo', sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background-color: #f2f2f2; }
                            .container { background: white; padding: 40px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 400px; width: 90%; }
                            h1 { color: #FF6600; margin-bottom: 20px; font-size: 24px; }
                            p { color: #444; margin-bottom: 30px; font-size: 16px; }
                            .btn { display: inline-block; padding: 12px 24px; background-color: #333; color: white; text-decoration: none; border-radius: 8px; font-weight: 700; font-size: 16px; transition: background 0.3s; }
                            .btn:hover { background-color: #555; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>${message}</h1>
                            <p>포트폴리오를 점검하고 더 안정적인 투자를 시작해보세요.</p>
                            <a href="https://misodaily-portfolio.vercel.app/" class="btn" target="_blank">내 포트폴리오 점검하러가기</a>
                        </div>
                    </body>
                    </html>
                    `;
                };

                if (response.ok) {
                    return new Response(createHtmlResponse("구독이 완료되었습니다! 🍊"), {
                        headers: { "Content-Type": "text/html; charset=utf-8" },
                    });
                } else {
                    const errorText = await response.text();
                    // Handle Duplicate Email Error (Postgres Code 23505)
                    if (errorText.includes("23505") || errorText.includes("subscribers_email_key")) {
                        return new Response(createHtmlResponse("이미 구독 중인 이메일입니다! 🍊"), {
                            headers: { "Content-Type": "text/html; charset=utf-8" },
                        });
                    }
                    return new Response("구독 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", { status: 500 });
                }
            } catch (e) {
                return new Response("서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", { status: 500 });
            }
        }

        // Default: Serve Static Assets
        // 'ASSETS' binding is automatically provided when 'assets' is configured in wrangler.jsonc
        return env.ASSETS.fetch(request);
    },
};
