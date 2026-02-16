
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

                if (!email) {
                    return new Response("Email is required", { status: 400 });
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

                if (response.ok) {
                    return new Response("구독이 완료되었습니다! 감사합니다. 🍊", {
                        headers: { "Content-Type": "text/html; charset=utf-8" },
                    });
                } else {
                    const errorText = await response.text();
                    // Handle Duplicate Email Error (Postgres Code 23505)
                    if (errorText.includes("23505") || errorText.includes("subscribers_email_key")) {
                        return new Response("이미 구독 중인 이메일입니다! 🍊", {
                            headers: { "Content-Type": "text/html; charset=utf-8" },
                        });
                    }
                    return new Response(`Database Error: ${errorText}`, { status: 500 });
                }
            } catch (e) {
                return new Response(`Error: ${e.message}`, { status: 500 });
            }
        }

        // Default: Serve Static Assets
        // 'ASSETS' binding is automatically provided when 'assets' is configured in wrangler.jsonc
        return env.ASSETS.fetch(request);
    },
};
